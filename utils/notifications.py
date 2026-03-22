from notifications.models import Notification

def create_notification(user, notification_type, title, message, related_object=None):
    """
    Create a new notification for a user.
    
    Args:
        user: The user who will receive the notification
        notification_type: Type of notification (e.g., 'BOOKING_APPROVED')
        title: Title of the notification
        message: Detailed message for the notification
        related_object: Optional related object (e.g., booking, review, etc.)
    """
    notification = Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message
    )
    
    return notification