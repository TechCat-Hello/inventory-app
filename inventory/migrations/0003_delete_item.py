# Generated by Django 5.1.4 on 2025-06-08 23:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0002_inventoryitem'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Item',
        ),
    ]
