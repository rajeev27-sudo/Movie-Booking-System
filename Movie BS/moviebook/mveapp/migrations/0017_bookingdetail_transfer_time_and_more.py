# Generated by Django 5.1.4 on 2025-03-29 08:16

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mveapp', '0016_remove_bookingdetail_snacks'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='bookingdetail',
            name='transfer_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='bookingdetail',
            name='transferred_to',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='transferred_bookings', to=settings.AUTH_USER_MODEL),
        ),
    ]
