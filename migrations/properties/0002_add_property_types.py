from django.db import migrations

def add_property_types(apps, schema_editor):
    PropertyType = apps.get_model('properties', 'PropertyType')
    types = [
        '1BHK',
        '2BHK',
        '3BHK',
        '4BHK',
        'Studio Apartment',
        'Villa',
        'Independent House',
        'Penthouse',
        'Duplex',
    ]
    for type_name in types:
        PropertyType.objects.create(name=type_name)

def remove_property_types(apps, schema_editor):
    PropertyType = apps.get_model('properties', 'PropertyType')
    PropertyType.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('properties', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_property_types, remove_property_types),
    ]