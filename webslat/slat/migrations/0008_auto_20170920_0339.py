# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-09-20 03:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('slat', '0007_auto_20170911_0214'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='floors',
            field=models.IntegerField(blank=True, default=1),
            preserve_default=False,
        ),
    ]
