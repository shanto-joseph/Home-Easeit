from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='payment_status',
            field=models.CharField(
                choices=[
                    ('PENDING', 'Pending'),
                    ('COMPLETED', 'Completed'),
                    ('FAILED', 'Failed'),
                    ('REFUNDED', 'Refunded')
                ],
                default='PENDING',
                max_length=20
            ),
        ),
        migrations.AddField(
            model_name='booking',
            name='reject_reason',
            field=models.TextField(blank=True, null=True),
        ),
    ]