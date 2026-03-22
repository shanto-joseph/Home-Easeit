from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ('visits', '0001_initial'),
        ('bookings', '0003_remove_payment_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='visit',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='booking', to='visits.visit'),
        ),
    ]