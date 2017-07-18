# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-06-29 18:01
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0020_auto_20170629_2108'),
    ]

    operations = [
        migrations.AlterField(
            model_name='schoolmarksheet',
            name='cgpa_marksheet',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='student.CGPAMarksheet'),
        ),
        migrations.AlterField(
            model_name='schoolmarksheet',
            name='marksheet_10',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='school_marksheet_10', to='student.ScoreMarksheet'),
        ),
    ]