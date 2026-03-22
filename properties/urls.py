from django.urls import path
from . import views

urlpatterns = [
    path('', views.PropertyListView.as_view(), name='property_list'),
    path('create/', views.PropertyCreateView.as_view(), name='property_create'),
    path('my-properties/', views.LandlordPropertiesView.as_view(), name='landlord_properties'),
    path('my-bookings/', views.LandlordBookingsListView.as_view(), name='landlord_bookings'),
    path('edit/<slug:slug>/', views.PropertyUpdateView.as_view(), name='property_edit'),
    path('delete/<slug:slug>/', views.PropertyDeleteView.as_view(), name='property_delete'),
    path('customer/<slug:slug>/', views.CustomerPropertyDetailView.as_view(), name='property_detail'),
    path('landlord/<slug:slug>/', views.LandlordPropertyDetailView.as_view(), name='landlord_property_detail'),
    path('api/property-types/', views.get_property_types, name='api_property_types'),
    path('api/amenities/', views.get_amenities, name='api_amenities'),
    path('toggle-availability/<int:property_id>/', views.toggle_availability, name='toggle_availability'),
    path('delete-image/<int:image_id>/', views.delete_property_image, name='delete_property_image'),
]