from django.db import models
from django.conf import settings

class Visit(models.Model):
    STATUS_CHOICES = (
        ('REQUESTED', 'Requested'),
        ('APPROVED', 'Approved'),
        ('RESCHEDULED', 'Rescheduled'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    )
    
    property = models.ForeignKey('properties.Property', on_delete=models.CASCADE, related_name='visits')
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='property_visits')
    visit_date = models.DateField()
    visit_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='REQUESTED')
    visit_fee = models.DecimalField(max_digits=10, decimal_places=2, default=1000.00)
    fee_paid = models.BooleanField(default=False)
    fee_refunded = models.BooleanField(default=False)
    reason = models.TextField(blank=True, null=True, help_text='Reason for cancellation or rejection')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Visit to {self.property.title} by {self.customer.username}"