# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-08-31 00:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0008_auto_20160830_2103'),
    ]

    operations = [
        migrations.AlterField(
            model_name='student',
            name='is_intern',
            field=models.BooleanField(default=False, verbose_name='Currently Intern'),
        ),
        migrations.AlterField(
            model_name='student',
            name='is_placed',
            field=models.BooleanField(default=False, verbose_name='Currently Placed'),
        ),
    ]
