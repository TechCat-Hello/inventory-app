# Generated by Django 5.1.4 on 2025-06-11 05:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0011_returnlog'),
    ]

    operations = [
        migrations.AddField(
            model_name='rental',
            name='expected_return_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
