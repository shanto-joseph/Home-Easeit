from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.urls import reverse
from django.contrib import messages
from django.db.models import Count, Sum, Avg, Q
from django.http import JsonResponse
from .models import Payment
from properties.models import Property
from bookings.models import Booking
from visits.models import Visit
from .forms import PaymentForm
from django.utils import timezone
from datetime import datetime
import time
from notifications.models import Notification
from decimal import Decimal

@login_required
def booking_payment(request):
    # Get booking data from session
    booking_data = request.session.get('booking_data')
    if not booking_data:
        messages.error(request, 'Booking data not found. Please try again.')
        return redirect('property_list')
    
    property = get_object_or_404(Property, id=booking_data['property_id'])
    visit_fee = Decimal(str(booking_data.get('visit_fee', 0)))
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment_method = form.cleaned_data['payment_method']
            
            # Create the booking
            booking = Booking(
                property=property,
                customer=request.user,
                start_date=datetime.fromisoformat(booking_data['start_date']).date(),
                end_date=datetime.fromisoformat(booking_data['end_date']).date() if booking_data['end_date'] else None,
                monthly_rent=Decimal(str(booking_data['monthly_rent'])),
                security_deposit=Decimal(str(booking_data['security_deposit'])),
                status='PENDING'
            )
            
            # If there's a visit, associate it
            if booking_data.get('visit_id'):
                visit = Visit.objects.get(id=booking_data['visit_id'])
                booking.visit = visit
            
            booking.save()
            
            # Create payment for security deposit
            security_deposit_payment = Payment(
                user=request.user,
                booking=booking,
                amount=booking.security_deposit,
                payment_type='SECURITY_DEPOSIT',
                payment_method=payment_method,
                payment_status='COMPLETED',
                transaction_id=f"TXN-{booking.id}-{int(time.time())}"
            )
            security_deposit_payment.save()
            
            # Create payment for first month's rent (adjusted with visit fee if applicable)
            rent_payment = Payment(
                user=request.user,
                booking=booking,
                amount=Decimal(str(booking.monthly_rent)) - visit_fee,
                payment_type='RENT',
                payment_method=payment_method,
                payment_status='COMPLETED',
                transaction_id=f"TXN-{booking.id}-RENT-{int(time.time())}"
            )
            rent_payment.save()
            
            # Clear session data
            if 'booking_data' in request.session:
                del request.session['booking_data']
            
            messages.success(request, 'Payment successful! Your booking is now pending landlord approval.')
            return redirect('customer_bookings')
    else:
        form = PaymentForm()
    
    total_amount = Decimal(str(booking_data['monthly_rent'])) + Decimal(str(booking_data['security_deposit'])) - visit_fee
    
    return render(request, 'payments/booking_payment.html', {
        'form': form,
        'property': property,
        'visit_fee': visit_fee,
        'total_amount': total_amount,
        'booking_data': booking_data
    })

@login_required
def visit_payment(request, property_id):
    property = get_object_or_404(Property, id=property_id)
    visit_data = request.session.get('visit_data')
    
    if not visit_data:
        messages.error(request, 'Visit data not found. Please try scheduling again.')
        return redirect('property_detail', slug=property.slug)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment_method = form.cleaned_data['payment_method']
            
            # Create visit record
            visit = Visit(
                property=property,
                customer=request.user,
                visit_date=datetime.fromisoformat(visit_data['visit_date']).date(),
                visit_time=visit_data['visit_time'],
                status='REQUESTED',
                fee_paid=True
            )
            visit.save()
            
            # Create payment record
            payment = Payment(
                user=request.user,
                visit=visit,
                amount=visit.visit_fee,
                payment_type='VISIT_FEE',
                payment_method=payment_method,
                payment_status='COMPLETED',  # Simplified for demo purposes
                transaction_id=f"TXN-VISIT-{visit.id}-{int(time.time())}"
            )
            payment.save()
            
            # Create notification for landlord
            Notification.objects.create(
                user=property.landlord,
                notification_type='VISIT_REQUESTED',
                title='New Visit Request',
                message=f'{request.user.get_full_name()} has requested to visit {property.title}.'
            )
            
            # Clear session data
            del request.session['visit_data']
            
            messages.success(request, 'Visit fee payment processed successfully! Your visit request is now pending landlord approval.')
            return redirect('customer_visits')
    else:
        form = PaymentForm()
    
    return render(request, 'payments/visit_payment.html', {
        'form': form,
        'visit_fee': 1000,  # Default visit fee
        'property': property
    })

class PaymentHistoryView(LoginRequiredMixin, ListView):
    model = Payment
    template_name = 'payments/payment_history.html'
    context_object_name = 'payments'
    paginate_by = 10
    
    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user).order_by('-payment_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payments = self.get_queryset()
        
        # Calculate payment statistics
        completed_payments = payments.filter(payment_status='COMPLETED')
        refunds = payments.filter(payment_type='REFUND', payment_status='COMPLETED')
        
        context['total_paid'] = completed_payments.exclude(payment_type='REFUND').aggregate(Sum('amount'))['amount__sum'] or 0
        context['total_refunds'] = refunds.aggregate(Sum('amount'))['amount__sum'] or 0
        context['rent_count'] = completed_payments.filter(payment_type='RENT').count()
        context['visit_count'] = completed_payments.filter(payment_type='VISIT_FEE').count()
        context['refund_count'] = refunds.count()
        
        return context

class LandlordTransactionView(LoginRequiredMixin, ListView):
    model = Payment
    template_name = 'payments/landlord_transactions.html'
    context_object_name = 'transactions'
    paginate_by = 10
    
    def get_queryset(self):
        # Get all payments related to landlord's properties
        property_payments = Payment.objects.filter(
            Q(booking__property__landlord=self.request.user) |
            Q(visit__property__landlord=self.request.user)
        ).order_by('-payment_date')
        
        # Annotate each payment with transaction type
        for payment in property_payments:
            payment.type = 'refunded' if payment.payment_type == 'REFUND' else 'received'
        
        return property_payments
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        transactions = self.get_queryset()
        
        # Calculate transaction statistics
        completed_transactions = transactions.filter(payment_status='COMPLETED')
        received = completed_transactions.exclude(payment_type='REFUND')
        refunded = completed_transactions.filter(payment_type='REFUND')
        
        context['total_received'] = received.aggregate(Sum('amount'))['amount__sum'] or 0
        context['total_refunded'] = refunded.aggregate(Sum('amount'))['amount__sum'] or 0
        context['transaction_count'] = transactions.count()
        context['net_balance'] = context['total_received'] - context['total_refunded']
        
        return context

@login_required
def payment_details(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    
    property_title = None
    if payment.booking:
        property_title = payment.booking.property.title
    elif payment.visit:
        property_title = payment.visit.property.title
    
    data = {
        'transaction_id': payment.transaction_id,
        'payment_date': payment.payment_date.strftime('%B %d, %Y %I:%M %p'),
        'payment_method': payment.get_payment_method_display(),
        'status': payment.get_payment_status_display(),
        'payment_type': payment.get_payment_type_display(),
        'property_title': property_title,
        'amount': str(payment.amount),
        'additional_info': 'Payment processed through secure payment gateway.'
    }
    
    return JsonResponse(data)