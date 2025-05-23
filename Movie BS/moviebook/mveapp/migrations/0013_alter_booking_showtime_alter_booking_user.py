# Generated by Django 5.1.4 on 2025-03-09 17:20

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mveapp', '0012_snack'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booking',
            name='showtime',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bookings', to='mveapp.showtime'),
        ),
        migrations.AlterField(
            model_name='booking',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bookings', to='mveapp.registration'),
        ),
    ]
