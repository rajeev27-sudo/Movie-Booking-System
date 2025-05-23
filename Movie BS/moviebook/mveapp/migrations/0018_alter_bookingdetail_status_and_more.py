# Generated by Django 5.1.4 on 2025-04-01 08:39

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mveapp', '0017_bookingdetail_transfer_time_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bookingdetail',
            name='status',
            field=models.CharField(choices=[('Booked', 'Booked'), ('Cancelled', 'Cancelled'), ('Transferred', 'Transferred')], default='Booked', max_length=20),
        ),
        migrations.AlterField(
            model_name='bookingdetail',
            name='transferred_to',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='transferred_bookings', to='mveapp.registration'),
        ),
    ]
