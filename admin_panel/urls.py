from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('users/', views.UserManagementView.as_view(), name='user_management'),
    path('properties/', views.PropertyManagementView.as_view(), name='property_management'),
    path('manage/', views.manage_dashboard, name='manage_dashboard'),
    path('manage/users/', views.manage_users, name='manage_users'),
    path('manage/properties/', views.manage_properties, name='manage_properties'),
    path('manage/bookings/', views.manage_bookings, name='manage_bookings'),
    path('manage/visits/', views.manage_visits, name='manage_visits'),
    path('manage/payments/', views.manage_payments, name='manage_payments'),
    path('manage/reviews/', views.manage_reviews, name='manage_reviews'),
    path('users/toggle-status/<int:user_id>/', views.toggle_user_status, name='toggle_user_status'),
    path('users/update-role/<int:user_id>/', views.update_user_role, name='update_user_role'),
    path('users/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('users/details/<int:user_id>/', views.get_user_details, name='get_user_details'),
    
    # Fixed Property Management URLs
    path('manage/properties/details/<int:property_id>/', views.get_property_details, name='get_property_details'),
    path('manage/properties/toggle-availability/<int:property_id>/', views.toggle_property_availability, name='toggle_property_availability'),
    path('manage/properties/delete/<int:property_id>/', views.delete_property, name='delete_property'),

    path('manage/visits/update-status/<int:visit_id>/', views.update_visit_status, name='admin_update_visit_status'),
    path('manage/visits/reject/<int:visit_id>/', views.reject_visit, name='admin_reject_visit'),
    path('manage/visits/reschedule/<int:visit_id>/', views.reschedule_visit, name='admin_reschedule_visit'),
    path('detail/<int:visit_id>/', views.get_visit_details, name='get_visit_details'),
    
    # Add the booking details URL
    path('manage/bookings/details/<int:booking_id>/', views.get_booking_details, name='get_booking_details'),
    
    # Add the payment details URL
    path('manage/payments/details/<int:payment_id>/', views.get_payment_details, name='get_payment_details'),
    path('reviews/details/<int:review_id>/', views.get_review_details, name='get_review_details'),
    path('reviews/toggle-visibility/<int:review_id>/', views.toggle_review_visibility, name='toggle_review_visibility'),
]