from django.urls import path
from . import views

urlpatterns = [
    path('create/<slug:property_slug>/', views.create_booking, name='create_booking'),
    path('my-bookings/', views.CustomerBookingsListView.as_view(), name='customer_bookings'),
    path('landlord-bookings/', views.LandlordBookingsListView.as_view(), name='landlord_bookings'),
    path('approve/<int:booking_id>/', views.approve_booking, name='approve_booking'),
    path('reject/<int:booking_id>/', views.reject_booking, name='reject_booking'),
    path('cancel/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    path('end-rental/<int:booking_id>/', views.end_rental, name='end_rental'),
    path('detail/<int:booking_id>/', views.booking_detail, name='booking_detail'),
    path('download-pdf/<int:booking_id>/', views.download_booking_pdf, name='download_booking_pdf'),
]