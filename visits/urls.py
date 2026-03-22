from django.urls import path
from . import views

urlpatterns = [
    path('schedule/<slug:property_slug>/', views.schedule_visit, name='schedule_visit'),
    path('my-visits/', views.CustomerVisitsListView.as_view(), name='customer_visits'),
    path('landlord-visits/', views.LandlordVisitsListView.as_view(), name='landlord_visits'),
    path('approve/<int:visit_id>/', views.approve_visit, name='approve_visit'),
    path('reject/<int:visit_id>/', views.reject_visit, name='reject_visit'),
    path('reschedule/<int:visit_id>/', views.reschedule_visit, name='reschedule_visit'),
    path('confirm-reschedule/<int:visit_id>/', views.confirm_reschedule, name='confirm_reschedule'),
    path('update-status/<int:visit_id>/', views.update_visit_status, name='update_visit_status'),
    path('refund/<int:visit_id>/', views.visit_refund, name='visit_refund'),
    path('get-available-slots/', views.get_available_slots_view, name='get_available_slots'),
]