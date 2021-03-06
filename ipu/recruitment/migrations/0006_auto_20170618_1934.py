# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-06-18 14:04
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('recruitment', '0005_auto_20170526_1548'),
    ]

    operations = [
        migrations.AddField(
            model_name='association',
            name='created_on',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2017, 6, 18, 14, 4, 54, 883350, tzinfo=utc)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='association',
            name='decline_message',
            field=models.CharField(blank=True, help_text='Reason(s) for declining', max_length=1024),
        ),
    ]
