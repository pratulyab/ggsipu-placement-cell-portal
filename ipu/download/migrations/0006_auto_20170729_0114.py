# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-07-28 19:44
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('download', '0005_auto_20170728_2244'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dlrequest',
            name='requesters',
            field=models.ManyToManyField(blank=True, related_name='download_requests', through='download.Requester', to=settings.AUTH_USER_MODEL),
        ),
    ]
