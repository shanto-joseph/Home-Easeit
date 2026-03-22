from django.db import migrations

def add_amenities(apps, schema_editor):
    Amenity = apps.get_model('properties', 'Amenity')
    amenities = [
        ('Parking', 'fa-car'),
        ('Air Conditioning', 'fa-snowflake'),
        ('Gym', 'fa-dumbbell'),
        ('Swimming Pool', 'fa-swimming-pool'),
        ('Security', 'fa-shield-alt'),
        ('Power Backup', 'fa-bolt'),
        ('Lift', 'fa-elevator'),
        ('CCTV', 'fa-video'),
        ('WiFi', 'fa-wifi'),
        ('Furnished', 'fa-couch'),
        ('Gas Pipeline', 'fa-fire'),
        ('Water Supply 24/7', 'fa-faucet'),
        ('Garden', 'fa-tree'),
        ('Playground', 'fa-futbol'),
        ('Visitor Parking', 'fa-parking'),
    ]
    
    for name, icon in amenities:
        Amenity.objects.create(name=name, icon=icon)

def remove_amenities(apps, schema_editor):
    Amenity = apps.get_model('properties', 'Amenity')
    Amenity.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('properties', '0002_add_property_types'),
    ]

    operations = [
        migrations.RunPython(add_amenities, remove_amenities),
    ]