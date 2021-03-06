# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-07-31 18:53
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models
import utils


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0025_auto_20170709_1500'),
    ]

    operations = [
        migrations.AlterField(
            model_name='student',
            name='photo',
            field=models.ImageField(blank=True, upload_to=utils.get_hashed_photo_name, verbose_name='Photo'),
        ),
        migrations.AlterField(
            model_name='student',
            name='resume',
            field=models.FileField(blank=True, upload_to=utils.get_hashed_resume_name, verbose_name='Resume'),
        ),
        migrations.AlterField(
            model_name='techprofile',
            name='codechef',
            field=models.CharField(blank=True, help_text='Please provide your Codechef username, if applicable.', max_length=14, validators=[django.core.validators.RegexValidator('^[a-z]{1}[a-z0-9_]{3,13}$')]),
        ),
        migrations.AlterField(
            model_name='techprofile',
            name='codeforces',
            field=models.CharField(blank=True, help_text='Please provide your Codeforces username, if applicable.', max_length=24),
        ),
        migrations.AlterField(
            model_name='techprofile',
            name='spoj',
            field=models.CharField(blank=True, help_text='Please provide your SPOJ username, if applicable.', max_length=14),
        ),
    ]
