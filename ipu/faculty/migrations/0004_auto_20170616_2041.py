# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-06-16 15:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('faculty', '0003_auto_20170613_2043'),
    ]

    operations = [
        migrations.AlterField(
            model_name='faculty',
            name='firstname',
            field=models.CharField(default='', max_length=128, verbose_name='First name'),
            preserve_default=False,
        ),
    ]