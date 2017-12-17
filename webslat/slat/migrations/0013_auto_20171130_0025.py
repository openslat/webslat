# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-11-30 00:25
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('slat', '0012_auto_20170927_2341'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='rarity',
            field=models.FloatField(choices=[(0.05, '20'), (0.04, '25'), (0.02, '50'), (0.01, '100'), (0.004, '250'), (0.002, '500'), (0.001, '1000'), (0.0004, '2000'), (0.0004, '2500')]),
        ),
    ]