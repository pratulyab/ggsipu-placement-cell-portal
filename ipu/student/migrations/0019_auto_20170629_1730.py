# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-06-29 12:00
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0018_auto_20170629_0220'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='examinationboard',
            options={'ordering': ['name']},
        ),
        migrations.AlterModelOptions(
            name='subject',
            options={'ordering': ['name']},
        ),
    ]