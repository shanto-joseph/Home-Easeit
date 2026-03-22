from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('bookings', '0002_add_payment_status_reject_reason'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='booking',
            name='payment_status',
        ),
    ]