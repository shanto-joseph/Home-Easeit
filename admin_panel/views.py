from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, UpdateView, TemplateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q, Exists, OuterRef, Count, Sum, Avg
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from accounts.models import User, Role
from properties.models import Property, PropertyType
from bookings.models import Booking
from visits.models import Visit
from payments.models import Payment
from reviews.models import Review
from django.utils import timezone   
from datetime import timedelta
import json
from notifications.models import Notification
import time
from django.conf import settings


def is_admin(user):
    return user.is_admin()

class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_admin()

class AdminHomeView(AdminRequiredMixin, TemplateView):
    template_name = 'admin_panel/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_bookings'] = Booking.objects.all().order_by('-created_at')[:5]
        context['now'] = timezone.now()
        return context

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    # Get counts and stats for dashboard
    total_users = User.objects.count()
    customers = User.objects.filter(role__name='CUSTOMER').count()
    landlords = User.objects.filter(role__name='LANDLORD').count()
    properties = Property.objects.count()
    available_properties = Property.objects.filter(is_available=True).count()
    bookings = Booking.objects.count()
    pending_bookings = Booking.objects.filter(status='PENDING').count()
    completed_bookings = Booking.objects.filter(status='COMPLETED').count()
    total_payments = Payment.objects.filter(payment_status='COMPLETED').aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Get recent activities
    recent_properties = Property.objects.order_by('-created_at')[:5]
    recent_bookings = Booking.objects.order_by('-created_at')[:5]
    recent_users = User.objects.order_by('-date_joined')[:5]
    
    context = {
        'total_users': total_users,
        'customers': customers,
        'landlords': landlords,
        'properties': properties,
        'available_properties': available_properties,
        'bookings': bookings,
        'pending_bookings': pending_bookings,
        'completed_bookings': completed_bookings,
        'total_payments': total_payments,
        'recent_properties': recent_properties,
        'recent_bookings': recent_bookings,
        'recent_users': recent_users,
    }
    
    return render(request, 'admin_panel/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def manage_dashboard(request):
    context = {
        'active_tab': 'dashboard',
        'total_users': User.objects.count(),
        'total_properties': Property.objects.count(),
        'total_bookings': Booking.objects.count(),
        'total_revenue': Payment.objects.filter(payment_status='COMPLETED').aggregate(Sum('amount'))['amount__sum'] or 0,
        'recent_bookings': Booking.objects.all().order_by('-created_at')[:5],
        'recent_users': User.objects.all().order_by('-date_joined')[:5],
    }
    return render(request, 'admin_panel/manage_dashboard.html', context)

class UserManagementView(AdminRequiredMixin, ListView):
    model = User
    template_name = 'admin_panel/user_management.html'
    context_object_name = 'users'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = User.objects.all().order_by('-date_joined')
        
        # Filter by user type if provided
        user_type = self.request.GET.get('user_type')
        if user_type and user_type in ['ADMIN', 'CUSTOMER', 'LANDLORD']:
            queryset = queryset.filter(role__name=user_type)
            
        # Search by username or email
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(username__icontains=search_query) | 
                Q(email__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_type'] = self.request.GET.get('user_type', '')
        context['search_query'] = self.request.GET.get('search', '')
        return context

@login_required
@user_passes_test(is_admin)
def manage_users(request):
    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')

    users = User.objects.all()

    # Apply search filter
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )

    # Apply role filter
    if role_filter:
        users = users.filter(role__name=role_filter)

    # Apply status filter
    if status_filter:
        is_active = status_filter == 'active'
        users = users.filter(is_active=is_active)

    # Get user statistics
    total_users = users.count()
    active_users = users.filter(is_active=True).count()
    inactive_users = total_users - active_users
    roles_count = {
        role.name: users.filter(role=role).count()
        for role in Role.objects.all()
    }

    context = {
        'active_tab': 'users',
        'users': users.order_by('-date_joined'),
        'total_users': total_users,
        'active_users': active_users,
        'inactive_users': inactive_users,
        'roles_count': roles_count,
        'search_query': search_query,
        'role_filter': role_filter,
        'status_filter': status_filter,
    }
    return render(request, 'admin_panel/manage_users.html', context)

class PropertyManagementView(AdminRequiredMixin, ListView):
    model = Property
    template_name = 'admin_panel/property_management.html'
    context_object_name = 'properties'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Property.objects.all().order_by('-created_at')
        
        # Filter by availability if provided
        availability = self.request.GET.get('availability')
        if availability == 'available':
            queryset = queryset.filter(is_available=True)
        elif availability == 'unavailable':
            queryset = queryset.filter(is_available=False)
            
        # Search by title, address, or city
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) | 
                Q(address__icontains=search_query) |
                Q(city__icontains=search_query)
            )
            
        return queryset

@login_required
@user_passes_test(is_admin)
def manage_properties(request):
    search_query = request.GET.get('search', '')
    type_filter = request.GET.get('type', '')
    availability_filter = request.GET.get('availability', '')
    
    properties = Property.objects.all().select_related('property_type', 'landlord').prefetch_related('images')
    
    # Apply search filter
    if search_query:
        properties = properties.filter(
            Q(title__icontains=search_query) | 
            Q(address__icontains=search_query) |
            Q(city__icontains=search_query)
        )
    
    # Apply type filter
    if type_filter:
        properties = properties.filter(property_type_id=type_filter)
    
    # Apply availability filter
    if availability_filter:
        is_available = availability_filter == 'available'
        properties = properties.filter(is_available=is_available)
    
    # Get property statistics
    total_properties = properties.count()
    available_properties = properties.filter(is_available=True).count()
    
    # Count active bookings
    active_bookings = Booking.objects.filter(
        property__in=properties,
        status='APPROVED'
    ).count()
    
    # Get all property types for filter dropdown
    property_types = PropertyType.objects.all()
    
    context = {
        'active_tab': 'properties',
        'properties': properties.order_by('-created_at'),
        'total_properties': total_properties,
        'available_properties': available_properties,
        'active_bookings': active_bookings,
        'property_types': property_types,
        'search_query': search_query,
        'type_filter': type_filter,
        'availability_filter': availability_filter,
    }
    return render(request, 'admin_panel/manage_properties.html', context)

@login_required
@user_passes_test(is_admin)
def manage_bookings(request):
    bookings = Booking.objects.all().order_by('-created_at')
    
    # Calculate booking counts by status
    pending_bookings = bookings.filter(status='PENDING').count()
    approved_bookings = bookings.filter(status='APPROVED').count()
    completed_bookings = bookings.filter(status='COMPLETED').count()
    cancelled_rejected_bookings = bookings.filter(status__in=['CANCELLED', 'REJECTED']).count()
    
    context = {
        'active_tab': 'bookings',
        'bookings': bookings,
        'pending_bookings': pending_bookings,
        'approved_bookings': approved_bookings,
        'completed_bookings': completed_bookings,
        'cancelled_rejected_bookings': cancelled_rejected_bookings,
    }
    return render(request, 'admin_panel/manage_bookings.html', context)

@login_required
@user_passes_test(is_admin)
def manage_visits(request):
    visits = Visit.objects.all().order_by('-created_at')
    
    context = {
        'active_tab': 'visits',
        'visits': visits,
        'pending_visits': visits.filter(status='REQUESTED').count(),
        'approved_visits': visits.filter(status='APPROVED').count(),
        'completed_visits': visits.filter(status='COMPLETED').count(),
        'cancelled_visits': visits.filter(status='CANCELLED').count(),
    }
    return render(request, 'admin_panel/manage_visits.html', context)

@login_required
@user_passes_test(is_admin)
@require_POST
def update_visit_status(request, visit_id):
    visit = get_object_or_404(Visit, id=visit_id)
    status = request.POST.get('status')
    
    if status in dict(Visit.STATUS_CHOICES):
        visit.status = status
        visit.save()
        
        # Create notification for customer
        Notification.objects.create(
            user=visit.customer,
            notification_type=f'VISIT_{status}',
            title=f'Visit {status.capitalize()}',
            message=f'Your visit to {visit.property.title} has been marked as {status.lower()}.'
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Visit status updated to {visit.get_status_display()}'
        })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid status'
    }, status=400)

@login_required
@user_passes_test(is_admin)
@require_POST
def reject_visit(request, visit_id):
    visit = get_object_or_404(Visit, id=visit_id)
    reason = request.POST.get('reason')
    
    if not reason:
        return JsonResponse({
            'success': False,
            'message': 'Please provide a reason for rejection'
        }, status=400)
    
    visit.status = 'REJECTED'
    visit.reason = reason
    visit.save()
    
    # Process refund if fee was paid
    if visit.fee_paid and not visit.fee_refunded:
        Payment.objects.create(
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
    
    Notification.objects.create(
        user=visit.customer,
        notification_type='VISIT_REJECTED',
        title='Visit Rejected',
        message=f'Your visit to {visit.property.title} has been rejected. Reason: {reason}'
    )
    
    return JsonResponse({
        'success': True,
        'message': 'Visit rejected successfully'
    })

@login_required
@user_passes_test(is_admin)
@require_POST
def reschedule_visit(request, visit_id):
    visit = get_object_or_404(Visit, id=visit_id)
    reason = request.POST.get('reason')
    
    if not reason:
        return JsonResponse({
            'success': False,
            'message': 'Please provide a reason for rescheduling'
        }, status=400)
    
    visit.status = 'RESCHEDULED'
    visit.reason = reason
    visit.save()
    
    Notification.objects.create(
        user=visit.customer,
        notification_type='VISIT_RESCHEDULED',
        title='Visit Needs Rescheduling',
        message=f'Your visit to {visit.property.title} needs to be rescheduled. Reason: {reason}'
    )
    
    return JsonResponse({
        'success': True,
        'message': 'Visit rescheduling requested successfully'
    })

@login_required
@user_passes_test(is_admin)
def manage_payments(request):
    # Get all payments
    payments = Payment.objects.all().order_by('-payment_date')
    
    # Calculate payment statistics
    pending_payments = payments.filter(payment_status='PENDING').count()
    completed_payments = payments.filter(payment_status='COMPLETED').count()
    refunds = payments.filter(payment_type='REFUND', payment_status='COMPLETED').count()
    
    context = {
        'active_tab': 'payments',
        'payments': payments,
        'pending_payments': pending_payments,
        'completed_payments': completed_payments,
        'refunds': refunds
    }
    return render(request, 'admin_panel/manage_payments.html', context)

@login_required
@user_passes_test(is_admin)
def manage_reviews(request):
    context = {
        'active_tab': 'reviews',
        'reviews': Review.objects.all().order_by('-created_at'),
    }
    return render(request, 'admin_panel/manage_reviews.html', context)

@login_required
@user_passes_test(is_admin)
def toggle_user_status(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        if user.is_admin():
            return JsonResponse({
                'success': False,
                'message': 'Cannot deactivate admin users'
            }, status=400)

        user.is_active = not user.is_active
        user.save()
        
        return JsonResponse({
            'success': True,
            'is_active': user.is_active,
            'message': f'User {"activated" if user.is_active else "deactivated"} successfully'
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

@login_required
@user_passes_test(is_admin)
def get_user_details(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        
        # Get properties count for landlords
        properties_count = Property.objects.filter(landlord=user).count() if user.is_landlord() else 0
        
        # Get bookings count
        if user.is_customer():
            bookings_count = Booking.objects.filter(customer=user).count()
        elif user.is_landlord():
            bookings_count = Booking.objects.filter(property__landlord=user).count()
        else:
            bookings_count = 0
        
        # Get visits count
        if user.is_customer():
            visits_count = Visit.objects.filter(customer=user).count()
        elif user.is_landlord():
            visits_count = Visit.objects.filter(property__landlord=user).count()
        else:
            visits_count = 0
        
        # Get reviews count
        if user.is_customer():
            reviews_count = Review.objects.filter(reviewer=user).count()
        elif user.is_landlord():
            reviews_count = Review.objects.filter(property__landlord=user).count()
        else:
            reviews_count = 0
        
        data = {
            'id': user.id,
            'username': user.username,
            'full_name': user.get_full_name(),
            'email': user.email,
            'phone_number': user.phone_number,
            'date_joined': user.date_joined.strftime('%B %d, %Y'),
            'profile_picture': user.profile_picture.url if user.profile_picture else None,
            'role': user.role.name,
            'is_active': user.is_active,
            'properties_count': properties_count,
            'bookings_count': bookings_count,
            'visits_count': visits_count,
            'reviews_count': reviews_count,
        }
        return JsonResponse(data)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
@require_POST
def update_user_role(request, user_id):
    try:
        user = get_object_or_404(User, id=user_id)
        new_role_name = request.POST.get('role')
        
        if user.is_admin():
            return JsonResponse({
                'success': False,
                'message': 'Cannot change admin user roles'
            }, status=400)
        
        try:
            new_role = Role.objects.get(name=new_role_name)
            user.role = new_role
            user.save()
            
            return JsonResponse({
                'success': True,
                'message': f'User role updated to {new_role_name}'
            })
        except Role.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Invalid role specified'
            }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error updating user role: {str(e)}'
        }, status=500)

@login_required
@user_passes_test(is_admin)
def delete_user(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        if user.is_admin():
            return JsonResponse({
                'success': False,
                'message': 'Cannot delete admin users'
            }, status=400)

        user.delete()
        messages.success(request, 'User deleted successfully')
        return redirect('manage_users')
    
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

@login_required
@user_passes_test(is_admin)
def get_property_details(request, property_id):
    try:
        property = Property.objects.get(id=property_id)
        
        # Get property statistics
        visits_count = Visit.objects.filter(property=property).count()
        bookings_count = Booking.objects.filter(property=property).count()
        reviews_count = Review.objects.filter(property=property).count()
        average_rating = Review.objects.filter(property=property).aggregate(Avg('rating'))['rating__avg'] or 0
        
        data = {
            'id': property.id,
            'title': property.title,
            'property_type': property.property_type.name,
            'address': property.address,
            'city': property.city,
            'monthly_rent': property.monthly_rent,
            'security_deposit': property.security_deposit,
            'is_available': property.is_available,
            'landlord_name': property.landlord.get_full_name(),
            'landlord_email': property.landlord.email,
            'visits_count': visits_count,
            'bookings_count': bookings_count,
            'reviews_count': reviews_count,
            'average_rating': round(average_rating, 1),
        }
        return JsonResponse(data)
    except Property.DoesNotExist:
        return JsonResponse({'error': 'Property not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
@require_POST
def toggle_property_availability(request, property_id):
    try:
        property = get_object_or_404(Property, id=property_id)
        if request.user == property.landlord or request.user.is_admin():
            data = json.loads(request.body)
            property.is_available = data['is_available']
            property.save()
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
@user_passes_test(is_admin)
@require_POST
def delete_property(request, property_id):
    try:
        property = get_object_or_404(Property, id=property_id)
        
        # Check if property has active bookings
        has_active_bookings = Booking.objects.filter(
            property=property,
            status='APPROVED'
        ).exists()
        
        if has_active_bookings:
            messages.error(request, 'Cannot delete property with active bookings')
            return redirect('manage_properties')
        
        property.delete()
        messages.success(request, 'Property deleted successfully')
        return redirect('manage_properties')
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)
    
@login_required
def get_visit_details(request, visit_id):
    try:
        visit = Visit.objects.get(id=visit_id)
        
        data = {
            'property_title': visit.property.title,
            'property_address': visit.property.address,
            'visit_date': visit.visit_date.strftime('%B %d, %Y'),
            'visit_time': visit.visit_time.strftime('%I:%M %p'),
            'status': visit.get_status_display(),
            'fee_status': 'Paid' if visit.fee_paid else 'Pending',
            'customer_name': visit.customer.get_full_name(),
            'customer_email': visit.customer.email,
            'customer_phone': visit.customer.phone_number,
            'reason': visit.reason if visit.reason else None
        }
        return JsonResponse(data)
    except Visit.DoesNotExist:
        return JsonResponse({'error': 'Visit not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_payment_details(request, payment_id):
    try:
        payment = Payment.objects.get(id=payment_id)
        
        property_title = None
        if payment.booking and payment.booking.property:
            property_title = payment.booking.property.title
        elif payment.visit and payment.visit.property:
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
    except Payment.DoesNotExist:
        return JsonResponse({'error': 'Payment not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_review_details(request, review_id):
    try:
        review = Review.objects.get(id=review_id)
        
        data = {
            'property_title': review.property.title,
            'property_address': review.property.address,
            'rating': review.rating,
            'comment': review.comment,
            'created_at': review.created_at.strftime('%B %d, %Y'),
            'reviewer_name': review.reviewer.get_full_name(),
            'reviewer_email': review.reviewer.email,
            'booking_date': review.booking.created_at.strftime('%B %d, %Y') if review.booking else None,
            'is_hidden': review.is_hidden
        }
        return JsonResponse(data)
    except Review.DoesNotExist:
        return JsonResponse({'error': 'Review not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
@require_POST
def toggle_review_visibility(request, review_id):
    try:
        review = get_object_or_404(Review, id=review_id)
        review.is_hidden = not review.is_hidden
        review.save()
        
        return JsonResponse({
            'success': True,
            'is_hidden': review.is_hidden,
            'message': f'Review is now {"hidden" if review.is_hidden else "visible"}'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)
    

    # Add this function to admin_panel/views.py

@login_required
def get_booking_details(request, booking_id):
    try:
        booking = Booking.objects.get(id=booking_id)
        
        data = {
            'property_title': booking.property.title,
            'property_address': booking.property.address,
            'start_date': booking.start_date.strftime('%B %d, %Y'),
            'end_date': booking.end_date.strftime('%B %d, %Y') if booking.end_date else None,
            'status': booking.get_status_display(),
            'monthly_rent': str(booking.monthly_rent),
            'security_deposit': str(booking.security_deposit),
            'customer_name': booking.customer.get_full_name(),
            'customer_email': booking.customer.email,
            'customer_phone': booking.customer.phone_number,
            'created_at': booking.created_at.strftime('%B %d, %Y'),
            'reject_reason': booking.reject_reason if booking.reject_reason else None
        }
        return JsonResponse(data)
    except Booking.DoesNotExist:
        return JsonResponse({'error': 'Booking not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
