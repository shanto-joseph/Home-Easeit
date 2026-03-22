from django.urls import path
from . import views

urlpatterns = [
    path('booking/', views.booking_payment, name='booking_payment'),
    path('visit/property/<int:property_id>/', views.visit_payment, name='visit_payment'),
    path('history/', views.PaymentHistoryView.as_view(), name='payment_history'),
    path('transactions/', views.LandlordTransactionView.as_view(), name='landlord_transactions'),
    path('details/<int:payment_id>/', views.payment_details, name='payment_details'),
]