from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.urls import reverse
from django.contrib import messages
from .models import Booking
from properties.models import Property
from visits.models import Visit
from .forms import BookingForm
from django.utils import timezone
from datetime import datetime
from payments.forms import PaymentForm
from notifications.models import Notification
from payments.models import Payment
import time
from decimal import Decimal
#pdf generation
from io import BytesIO
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import mm

@login_required
def create_booking(request, property_slug):
    property = get_object_or_404(Property, slug=property_slug, is_available=True)
    
    # Check if user has a completed visit with paid fee
    visit_fee = 0
    recent_visit = Visit.objects.filter(
        customer=request.user,
        property=property,
        status='COMPLETED',
        fee_paid=True,
        fee_refunded=False,
        booking__isnull=True  # Only get visits that aren't already associated with a booking
    ).first()
    
    if recent_visit:
        visit_fee = recent_visit.visit_fee
    
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            # Store booking data in session instead of creating the booking
            booking_data = {
                'property_id': property.id,
                'start_date': form.cleaned_data['start_date'].isoformat(),
                'end_date': form.cleaned_data['end_date'].isoformat() if form.cleaned_data['end_date'] else None,
                'monthly_rent': float(property.monthly_rent),
                'security_deposit': float(property.security_deposit),
                'visit_id': recent_visit.id if recent_visit else None,
                'visit_fee': float(visit_fee) if visit_fee else 0
            }
            request.session['booking_data'] = booking_data
            
            # Redirect to payment page
            return redirect('booking_payment')
    else:
        form = BookingForm()
    
    total_amount = property.monthly_rent + property.security_deposit - visit_fee
    
    return render(request, 'bookings/create_booking.html', {
        'form': form,
        'property': property,
        'visit_fee': visit_fee,
        'total_amount': total_amount
    })

@login_required
def end_rental(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, customer=request.user, status='APPROVED')
    
    if request.method == 'POST':
        booking.status = 'COMPLETED'
        booking.end_date = timezone.now().date()
        booking.save()
        
        # Make property available again
        property = booking.property
        property.is_available = True
        property.save()
        
        messages.success(request, 'Rental ended successfully.')
    
    return redirect('customer_bookings')

class CustomerBookingsListView(LoginRequiredMixin, ListView):
    model = Booking
    template_name = 'bookings/customer_bookings.html'
    context_object_name = 'bookings'
    
    def get_queryset(self):
        return Booking.objects.filter(customer=self.request.user).order_by('-created_at')

class LandlordBookingsListView(LoginRequiredMixin, ListView):
    model = Booking
    template_name = 'bookings/landlord_bookings.html'
    context_object_name = 'bookings'
    
    def get_queryset(self):
        return Booking.objects.filter(property__landlord=self.request.user).order_by('-created_at')

@login_required
def approve_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, property__landlord=request.user)
    
    if booking.status == 'PENDING':
        booking.status = 'APPROVED'
        booking.save()
        
        # Update property availability
        property = booking.property
        property.is_available = False
        property.save()
        
        # Create notification for customer
        Notification.objects.create(
            user=booking.customer,
            notification_type='BOOKING_APPROVED',
            title='Booking Approved',
            message=f'Your booking for {property.title} has been approved.'
        )
        
        messages.success(request, 'Booking approved successfully.')
    else:
        messages.error(request, 'This booking cannot be approved.')
    
    return redirect('landlord_bookings')

@login_required
def reject_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, property__landlord=request.user)
    
    if request.method == 'POST' and booking.status == 'PENDING':
        reason = request.POST.get('reason')
        if not reason:
            messages.error(request, 'Please provide a reason for rejection.')
            return redirect('landlord_bookings')
        
        booking.status = 'REJECTED'
        booking.reject_reason = reason
        booking.save()
        
        # Get all payments related to this booking
        booking_payments = Payment.objects.filter(
            booking=booking,
            payment_status='COMPLETED',
            payment_type__in=['RENT', 'SECURITY_DEPOSIT']
        )
        
        # Calculate total amount to refund
        total_refund = sum(payment.amount for payment in booking_payments)
        
        # Create refund for booking payments
        if total_refund > 0:
            refund_payment = Payment(
                user=booking.customer,
                booking=booking,
                amount=total_refund,
                payment_type='REFUND',
                payment_method='SYSTEM',
                payment_status='COMPLETED',
                transaction_id=f"TXN-REFUND-BOOKING-REJECT-{booking.id}-{int(time.time())}"
            )
            refund_payment.save()
            
            # Create notification for booking refund
            Notification.objects.create(
                user=booking.customer,
                notification_type='BOOKING_REFUNDED',
                title='Booking Payment Refunded',
                message=f'Your payment of ₹{total_refund} for {booking.property.title} has been refunded due to booking rejection.'
            )
        
        # Handle visit fee refund if applicable
        if booking.visit and booking.visit.fee_paid and not booking.visit.fee_refunded:
            # Create refund payment record for visit fee
            visit_refund = Payment(
                user=booking.customer,
                visit=booking.visit,
                amount=booking.visit.visit_fee,
                payment_type='REFUND',
                payment_method='SYSTEM',
                payment_status='COMPLETED',
                transaction_id=f"TXN-REFUND-VISIT-REJECT-{booking.visit.id}-{int(time.time())}"
            )
            visit_refund.save()
            
            # Mark visit fee as refunded
            booking.visit.fee_refunded = True
            booking.visit.save()
            
            # Create notification for visit fee refund
            Notification.objects.create(
                user=booking.customer,
                notification_type='VISIT_REFUNDED',
                title='Visit Fee Refunded',
                message=f'Your visit fee for {booking.property.title} has been refunded due to booking rejection.'
            )
        
        # Create notification for booking rejection
        Notification.objects.create(
            user=booking.customer,
            notification_type='BOOKING_REJECTED',
            title='Booking Rejected',
            message=f'Your booking for {booking.property.title} has been rejected. Reason: {reason}'
        )
        
        messages.success(request, 'Booking rejected and all payments have been refunded successfully.')
    else:
        messages.error(request, 'This booking cannot be rejected.')

    return redirect('landlord_bookings')

@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, customer=request.user)
    
    if booking.status in ['PENDING', 'APPROVED']:
        booking.status = 'CANCELLED'
        booking.save()
        
        # Get all payments related to this booking
        booking_payments = Payment.objects.filter(
            booking=booking,
            payment_status='COMPLETED',
            payment_type__in=['RENT', 'SECURITY_DEPOSIT']
        )
        
        # Calculate total amount to refund
        total_refund = sum(payment.amount for payment in booking_payments)
        
        # Create refund for booking payments
        if total_refund > 0:
            refund_payment = Payment(
                user=booking.customer,
                booking=booking,
                amount=total_refund,
                payment_type='REFUND',
                payment_method='SYSTEM',
                payment_status='COMPLETED',
                transaction_id=f"TXN-REFUND-BOOKING-{booking.id}-{int(time.time())}"
            )
            refund_payment.save()
            
            # Create notification for booking refund
            Notification.objects.create(
                user=booking.customer,
                notification_type='BOOKING_REFUNDED',
                title='Booking Payment Refunded',
                message=f'Your payment of ₹{total_refund} for {booking.property.title} has been refunded.'
            )
        
        # If the booking was approved, make the property available again
        if booking.status == 'APPROVED':
            property = booking.property
            property.is_available = True
            property.save()
        
        # Handle visit fee refund if applicable
        if booking.visit and booking.visit.fee_paid and not booking.visit.fee_refunded:
            # Create refund payment record for visit fee
            visit_refund = Payment(
                user=booking.customer,
                visit=booking.visit,
                amount=booking.visit.visit_fee,
                payment_type='REFUND',
                payment_method='SYSTEM',
                payment_status='COMPLETED',
                transaction_id=f"TXN-REFUND-VISIT-{booking.visit.id}-{int(time.time())}"
            )
            visit_refund.save()
            
            # Mark visit fee as refunded
            booking.visit.fee_refunded = True
            booking.visit.save()
            
            # Create notification for visit fee refund
            Notification.objects.create(
                user=booking.customer,
                notification_type='VISIT_REFUNDED',
                title='Visit Fee Refunded',
                message=f'Your visit fee for {booking.property.title} has been refunded due to booking cancellation.'
            )
        
        # Create notification for landlord
        Notification.objects.create(
            user=booking.property.landlord,
            notification_type='BOOKING_CANCELLED',
            title='Booking Cancelled',
            message=f'{request.user.get_full_name()} has cancelled their booking for {booking.property.title}.'
        )
        
        messages.success(request, 'Booking cancelled and all payments have been refunded successfully.')
    else:
        messages.error(request, 'This booking cannot be cancelled.')
    
    return redirect('customer_bookings')

@login_required
def booking_detail(request, booking_id):
    # For customer
    if request.user.is_customer():
        booking = get_object_or_404(Booking, id=booking_id, customer=request.user)
    # For landlord
    elif request.user.is_landlord():
        booking = get_object_or_404(Booking, id=booking_id, property__landlord=request.user)
    else:
        messages.error(request, 'You do not have permission to view this booking.')
        return redirect('home')
    
    return render(request, 'bookings/booking_detail.html', {'booking': booking})

@login_required
def download_booking_pdf(request, booking_id):
    # Get booking object
    if request.user.is_customer():
        booking = get_object_or_404(Booking, id=booking_id, customer=request.user)
    else:
        booking = get_object_or_404(Booking, id=booking_id, property__landlord=request.user)
    
    # Create PDF buffer
    buffer = BytesIO()
    
    # Set up the document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=15*mm,
        bottomMargin=15*mm
    )
    
    # Styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#4F46E5'),  # Indigo color
        spaceAfter=20
    ))
    
    styles.add(ParagraphStyle(
        name='SectionTitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1F2937'),  # Gray-800
        spaceBefore=15,
        spaceAfter=10
    ))
    
    # Content elements
    elements = []
    
    # Header with logo and title
    header_data = [
        [Paragraph("Home Easeit", styles['CustomTitle']),
         Paragraph(f"<para align=right><font color='#6B7280'>Booking #{booking.id}</font></para>", styles['Normal'])]
    ]
    header_table = Table(header_data, colWidths=[doc.width/2]*2)
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
    ]))
    elements.append(header_table)
    
    # Status and Date
    status_data = [
        [Paragraph(f"<para align=left><font color='#6B7280'>Status</font></para>", styles['Normal']),
         Paragraph(f"<para align=right><font color='#059669'>{booking.get_status_display()}</font></para>", styles['Normal'])],
        [Paragraph(f"<para align=left><font color='#6B7280'>Created On</font></para>", styles['Normal']),
         Paragraph(f"<para align=right>{booking.created_at.strftime('%B %d, %Y')}</para>", styles['Normal'])]
    ]
    status_table = Table(status_data, colWidths=[doc.width/2]*2)
    status_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(status_table)
    elements.append(Spacer(1, 20))
    
    # Property Details
    elements.append(Paragraph("Property Details", styles['SectionTitle']))
    property_data = [
        [Paragraph(f"<para><b>{booking.property.title}</b></para>", styles['Normal'])],
        [Paragraph(f"<para><font color='#6B7280'>{booking.property.address}</font></para>", styles['Normal'])],
        [Paragraph(f"<para><b>Monthly Rent:</b> ₹{booking.monthly_rent}</para>", styles['Normal'])],
        [Paragraph(f"<para><b>Security Deposit:</b> ₹{booking.security_deposit}</para>", styles['Normal'])],
        [Paragraph(f"<para><b>Start Date:</b> {booking.start_date.strftime('%B %d, %Y')}</para>", styles['Normal'])]
    ]
    if booking.end_date:
        property_data.append([Paragraph(f"<para><b>End Date:</b> {booking.end_date.strftime('%B %d, %Y')}</para>", styles['Normal'])])
    
    property_table = Table(property_data, colWidths=[doc.width])
    property_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(property_table)
    
    # Contact Information
    elements.append(Paragraph("Contact Information", styles['SectionTitle']))
    contact_data = [
        ['Customer', 'Landlord'],
        [booking.customer.get_full_name(), booking.property.landlord.get_full_name()],
        [booking.customer.email, booking.property.landlord.email],
        [booking.customer.phone_number, booking.property.landlord.phone_number]
    ]
    contact_table = Table(contact_data, colWidths=[doc.width/2]*2)
    contact_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F3F4F6')),  # Light gray background
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#4B5563')),  # Gray-600
    ]))
    elements.append(contact_table)
    
    # Build PDF
    doc.build(elements)
    
    # Get PDF value from buffer
    pdf = buffer.getvalue()
    buffer.close()
    
    # Create response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="booking_{booking_id}.pdf"'
    response.write(pdf)
    
    return response