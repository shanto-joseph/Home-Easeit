from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from datetime import datetime, timedelta
from .models import Visit
from properties.models import Property
from .forms import VisitForm
from notifications.models import Notification
from payments.models import Payment
import time

def get_available_slots():
    """Generate available time slots between 9 AM and 6 PM"""
    slots = []
    start_time = datetime.strptime('09:00', '%H:%M')
    end_time = datetime.strptime('18:00', '%H:%M')
    slot_duration = timedelta(hours=1)
    
    current_slot = start_time
    while current_slot < end_time:
        slots.append(current_slot.strftime('%H:%M'))
        current_slot += slot_duration
    
    return slots

@login_required
def get_available_slots_view(request):
    date = request.GET.get('date')
    property_id = request.GET.get('property_id')
    
    if not date or not property_id:
        return JsonResponse({'error': 'Missing parameters'}, status=400)
    
    try:
        visit_date = datetime.strptime(date, '%Y-%m-%d').date()
        property = Property.objects.get(id=property_id)
        
        # Get all slots
        available_slots = get_available_slots()
        
        # Get booked slots
        booked_visits = Visit.objects.filter(
            property=property,
            visit_date=visit_date,
            status__in=['REQUESTED', 'APPROVED', 'RESCHEDULED']
        )
        booked_slots = [visit.visit_time.strftime('%H:%M') for visit in booked_visits]
        
        return JsonResponse({
            'available_slots': available_slots,
            'booked_slots': booked_slots
        })
    except (ValueError, Property.DoesNotExist):
        return JsonResponse({'error': 'Invalid parameters'}, status=400)

@login_required
def schedule_visit(request, property_slug):
    property = get_object_or_404(Property, slug=property_slug, is_available=True)
    
    # Check if user already has a pending or approved visit
    existing_visit = Visit.objects.filter(
        customer=request.user,
        property=property,
        status__in=['REQUESTED', 'APPROVED']
    ).exists()
    
    if existing_visit:
        messages.error(request, 'You already have a pending or approved visit for this property.')
        return redirect('property_detail', slug=property_slug)
    
    if request.method == 'POST':
        form = VisitForm(request.POST)
        form.property_instance = property  # Set property for validation
        if form.is_valid():
            # Store form data in session instead of saving to database
            visit_date = form.cleaned_data['visit_date']
            visit_time = form.cleaned_data['visit_time']
            
            request.session['visit_data'] = {
                'visit_date': visit_date.strftime('%Y-%m-%d'),
                'visit_time': visit_time.strftime('%H:%M')
            }
            
            # Redirect to payment page with property_id
            return redirect('visit_payment', property_id=property.id)
    else:
        form = VisitForm()
    
    context = {
        'form': form,
        'property': property,
        'available_slots': get_available_slots(),
        'today': timezone.now().date(),
        'max_date': timezone.now().date() + timedelta(days=30),
    }
    
    return render(request, 'visits/schedule_visit.html', context)

class CustomerVisitsListView(LoginRequiredMixin, ListView):
    model = Visit
    template_name = 'visits/customer_visits.html'
    context_object_name = 'visits'
    
    def get_queryset(self):
        return Visit.objects.filter(customer=self.request.user).order_by('-created_at')

class LandlordVisitsListView(LoginRequiredMixin, ListView):
    model = Visit
    template_name = 'visits/landlord_visits.html'
    context_object_name = 'visits'
    
    def get_queryset(self):
        return Visit.objects.filter(property__landlord=self.request.user).order_by('-created_at')

@login_required
def approve_visit(request, visit_id):
    visit = get_object_or_404(Visit, id=visit_id, property__landlord=request.user)
    
    if request.method == 'POST' and visit.status == 'REQUESTED':
        # Check for conflicting visits
        conflicting_visits = Visit.objects.filter(
            property=visit.property,
            visit_date=visit.visit_date,
            visit_time=visit.visit_time,
            status='APPROVED'
        ).exists()
        
        if conflicting_visits:
            messages.error(request, 'There is already an approved visit at this time.')
            return redirect('landlord_visits')
        
        visit.status = 'APPROVED'
        visit.save()
        
        # Create notification for customer
        Notification.objects.create(
            user=visit.customer,
            notification_type='VISIT_APPROVED',
            title='Visit Request Approved',
            message=f'Your visit request for {visit.property.title} on {visit.visit_date} at {visit.visit_time} has been approved.'
        )
        
        messages.success(request, 'Visit request approved successfully.')
    else:
        messages.error(request, 'This visit request cannot be approved.')
    
    return redirect('landlord_visits')

@login_required
def reject_visit(request, visit_id):
    visit = get_object_or_404(Visit, id=visit_id, property__landlord=request.user)
    
    if request.method == 'POST' and visit.status == 'REQUESTED':
        reason = request.POST.get('reason')
        if not reason:
            messages.error(request, 'Please provide a reason for rejection.')
            return redirect('landlord_visits')
        
        visit.status = 'REJECTED'
        visit.reason = reason
        visit.save()
        
        # Create notification for customer
        Notification.objects.create(
            user=visit.customer,
            notification_type='VISIT_REJECTED',
            title='Visit Request Rejected',
            message=f'Your visit request for {visit.property.title} has been rejected. Reason: {reason}'
        )
        
        # Process refund if fee was paid
        if visit.fee_paid and not visit.fee_refunded:
            # Create refund payment record
            refund_payment = Payment.objects.create(
                user=visit.customer,
                visit=visit,
                amount=visit.visit_fee,
                payment_type='REFUND',
                payment_method='SYSTEM',
                payment_status='COMPLETED',
                transaction_id=f"REFUND-VISIT-REJECT-{visit.id}-{int(time.time())}"
            )
            
            visit.fee_refunded = True
            visit.save()
            
            Notification.objects.create(
                user=visit.customer,
                notification_type='VISIT_REFUNDED',
                title='Visit Fee Refunded',
                message=f'Your visit fee for {visit.property.title} has been refunded due to rejection.'
            )
        
        messages.success(request, 'Visit request rejected and refund processed successfully.')
    else:
        messages.error(request, 'This visit request cannot be rejected.')
    
    return redirect('landlord_visits')

@login_required
def reschedule_visit(request, visit_id):
    visit = get_object_or_404(Visit, id=visit_id, property__landlord=request.user)
    
    if request.method == 'POST' and visit.status == 'REQUESTED':
        reason = request.POST.get('reason')
        if not reason:
            messages.error(request, 'Please provide a reason for rescheduling.')
            return redirect('landlord_visits')
        
        visit.status = 'RESCHEDULED'
        visit.reason = reason
        visit.save()
        
        # Create notification for customer
        Notification.objects.create(
            user=visit.customer,
            notification_type='VISIT_RESCHEDULED',
            title='Visit Needs Rescheduling',
            message=f'Your visit to {visit.property.title} needs to be rescheduled. Reason: {reason}'
        )
        
        messages.success(request, 'Visit rescheduling requested successfully.')
    else:
        messages.error(request, 'This visit cannot be rescheduled.')
    
    return redirect('landlord_visits')

@login_required
def confirm_reschedule(request, visit_id):
    visit = get_object_or_404(Visit, id=visit_id, customer=request.user, status='RESCHEDULED')
    
    if request.method == 'POST':
        new_date = request.POST.get('visit_date')
        new_time = request.POST.get('visit_time')
        
        if not new_date or not new_time:
            messages.error(request, 'Please provide both date and time for rescheduling.')
            return redirect('customer_visits')
        
        try:
            # Check for conflicting visits
            new_date_obj = datetime.strptime(new_date, '%Y-%m-%d').date()
            new_time_obj = datetime.strptime(new_time, '%H:%M').time()
            
            conflicting_visits = Visit.objects.filter(
                property=visit.property,
                visit_date=new_date_obj,
                visit_time=new_time_obj,
                status__in=['REQUESTED', 'APPROVED']
            ).exists()
            
            if conflicting_visits:
                messages.error(request, 'This time slot is already booked. Please select a different date or time.')
                return redirect('customer_visits')
            
            visit.visit_date = new_date_obj
            visit.visit_time = new_time_obj
            visit.status = 'REQUESTED'
            visit.save()
            
            # Create notification for landlord
            Notification.objects.create(
                user=visit.property.landlord,
                notification_type='VISIT_REQUESTED',
                title='Visit Rescheduled',
                message=f'{visit.customer.get_full_name()} has rescheduled their visit to {visit.property.title} for {new_date} at {new_time}.'
            )
            
            messages.success(request, 'Visit rescheduled successfully.')
        except ValueError:
            messages.error(request, 'Invalid date or time format.')
    
    return redirect('customer_visits')

@login_required
def update_visit_status(request, visit_id):
    visit = get_object_or_404(Visit, id=visit_id, property__landlord=request.user)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['APPROVED', 'COMPLETED', 'CANCELLED']:
            visit.status = new_status
            visit.save()
            
            # Create notification for customer
            notification_type = f'VISIT_{new_status}'
            title = f'Visit {new_status.capitalize()}'
            message = f'Your visit to {visit.property.title} has been marked as {new_status.lower()}.'
            
            Notification.objects.create(
                user=visit.customer,
                notification_type=notification_type,
                title=title,
                message=message
            )
            
            messages.success(request, f'Visit status updated to {visit.get_status_display()}.')
        else:
            messages.error(request, 'Invalid status update requested.')
    
    return redirect('landlord_visits')

@login_required
def visit_refund(request, visit_id):
    visit = get_object_or_404(Visit, id=visit_id, customer=request.user, status='COMPLETED')
    
    if request.method == 'POST':
        if visit.fee_paid and not visit.fee_refunded:
            # Create refund payment record
            refund_payment = Payment.objects.create(
                user=visit.customer,
                visit=visit,
                amount=visit.visit_fee,
                payment_type='REFUND',
                payment_method='SYSTEM',
                payment_status='COMPLETED',
                transaction_id=f"REFUND-VISIT-NOTINTERESTED-{visit.id}-{int(time.time())}"
            )
            
            visit.fee_refunded = True
            visit.save()
            
            # Create notification for customer
            Notification.objects.create(
                user=visit.customer,
                notification_type='VISIT_REFUNDED',
                title='Visit Fee Refunded',
                message=f'Your visit fee for {visit.property.title} has been refunded as you were not interested in the property.'
            )
            
            messages.success(request, 'Visit fee refund has been processed.')
        else:
            messages.error(request, 'Visit fee cannot be refunded.')
    
    return redirect('customer_visits')