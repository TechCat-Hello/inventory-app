# Generated by Django 5.1.4 on 2025-06-10 22:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0008_rental_quantity'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rental',
            name='quantity',
            field=models.PositiveIntegerField(),
        ),
    ]
