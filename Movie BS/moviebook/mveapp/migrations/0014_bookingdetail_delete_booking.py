# Generated by Django 5.1.4 on 2025-03-23 07:10

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mveapp', '0013_alter_booking_showtime_alter_booking_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='BookingDetail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('payment_id', models.CharField(max_length=100)),
                ('booking_time', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('Booked', 'Booked'), ('Cancelled', 'Cancelled')], default='Booked', max_length=20)),
                ('movie', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='mveapp.movie')),
                ('seats', models.ManyToManyField(to='mveapp.seat')),
                ('show_time', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='mveapp.showtime')),
                ('snacks', models.ManyToManyField(blank=True, to='mveapp.snack')),
                ('theater', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='mveapp.theatre')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mveapp.registration')),
            ],
        ),
        migrations.DeleteModel(
            name='Booking',
        ),
    ]
