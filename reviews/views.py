from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
from .models import Review
from bookings.models import Booking
from .forms import ReviewForm
from utils.notifications import create_notification

@login_required
def create_review(request, booking_id):
    booking = get_object_or_404(
        Booking, 
        id=booking_id, 
        customer=request.user, 
        status='COMPLETED'
    )
    
    # Check if review already exists
    if hasattr(booking, 'review'):
        messages.info(request, 'You have already reviewed this property.')
        return redirect('property_detail', slug=booking.property.slug)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.property = booking.property
            review.reviewer = request.user
            review.booking = booking
            review.save()
            
            # Create notification for the customer
            create_notification(
                user=request.user,
                notification_type='REVIEW_SUBMITTED',
                title='Review Submitted',
                message=f'Your review for {booking.property.title} has been submitted successfully.'
            )
            
            # Create notification for the landlord
            create_notification(
                user=booking.property.landlord,
                notification_type='REVIEW_RECEIVED',
                title='New Review Received',
                message=f'A new review has been submitted for your property {booking.property.title}.'
            )
            
            messages.success(request, 'Your review has been submitted successfully.')
            return redirect('property_detail', slug=booking.property.slug)
    else:
        form = ReviewForm()
    
    return render(request, 'reviews/create_review.html', {
        'form': form,
        'booking': booking,
        'property': booking.property
    })