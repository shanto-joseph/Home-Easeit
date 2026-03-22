from django.db import models
from django.conf import settings

class NotificationManager(models.Manager):
    def unread(self):
        return self.filter(is_read=False)

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('VISIT_REQUESTED', 'Visit Requested'),
        ('VISIT_APPROVED', 'Visit Approved'),
        ('VISIT_REJECTED', 'Visit Rejected'),
        ('VISIT_RESCHEDULED', 'Visit Rescheduled'),
        ('VISIT_COMPLETED', 'Visit Completed'),
        ('VISIT_CANCELLED', 'Visit Cancelled'),
        ('VISIT_REFUNDED', 'Visit Refunded'),
        ('BOOKING_REQUESTED', 'Booking Requested'),
        ('BOOKING_APPROVED', 'Booking Approved'),
        ('BOOKING_REJECTED', 'Booking Rejected'),
        ('BOOKING_CANCELLED', 'Booking Cancelled'),
        ('BOOKING_COMPLETED', 'Booking Completed'),
        ('BOOKING_REFUNDED', 'Booking Refunded'),
        ('PAYMENT_RECEIVED', 'Payment Received'),
        ('PAYMENT_REFUNDED', 'Payment Refunded'),
        ('REVIEW_SUBMITTED', 'Review Submitted'),
        ('REVIEW_RECEIVED', 'Review Received'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    objects = NotificationManager()
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.notification_type} for {self.user.username}"