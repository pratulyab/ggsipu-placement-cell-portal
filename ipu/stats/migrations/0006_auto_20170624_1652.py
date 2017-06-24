# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-06-24 11:22
from __future__ import unicode_literals

from decimal import Decimal
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stats', '0005_auto_20170624_1644'),
    ]

    operations = [
        migrations.CreateModel(
            name='YearRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.CharField(max_length=4)),
                ('jobs_placement_percentage', models.DecimalField(decimal_places=2, default=0, max_digits=5, validators=[django.core.validators.MinValueValidator(Decimal('0')), django.core.validators.MaxValueValidator(Decimal('100'))], verbose_name='Percentage Placed for Jobs')),
                ('internships_placement_percentage', models.DecimalField(decimal_places=2, default=0, max_digits=5, validators=[django.core.validators.MinValueValidator(Decimal('0')), django.core.validators.MaxValueValidator(Decimal('100'))], verbose_name='Percentage of Internships')),
                ('students_participated_jobs', models.PositiveSmallIntegerField(default=0)),
                ('students_selected_jobs', models.PositiveSmallIntegerField(default=0)),
                ('students_participated_internships', models.PositiveSmallIntegerField(default=0)),
                ('students_selected_internships', models.PositiveSmallIntegerField(default=0)),
            ],
        ),
        migrations.RemoveField(
            model_name='placement',
            name='college',
        ),
        migrations.AlterField(
            model_name='college',
            name='code',
            field=models.CharField(max_length=3, unique=True),
        ),
        migrations.AlterUniqueTogether(
            name='college',
            unique_together=set([]),
        ),
        migrations.AddField(
            model_name='yearrecord',
            name='college',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='records', to='stats.College'),
        ),
        migrations.AddField(
            model_name='yearrecord',
            name='companies',
            field=models.ManyToManyField(blank=True, related_name='records', through='stats.Placement', to='stats.Company'),
        ),
        migrations.RemoveField(
            model_name='college',
            name='companies',
        ),
        migrations.RemoveField(
            model_name='college',
            name='internships_placement_percentage',
        ),
        migrations.RemoveField(
            model_name='college',
            name='jobs_placement_percentage',
        ),
        migrations.RemoveField(
            model_name='college',
            name='students_participated_internships',
        ),
        migrations.RemoveField(
            model_name='college',
            name='students_participated_jobs',
        ),
        migrations.RemoveField(
            model_name='college',
            name='students_selected_internships',
        ),
        migrations.RemoveField(
            model_name='college',
            name='students_selected_jobs',
        ),
        migrations.RemoveField(
            model_name='college',
            name='year',
        ),
        migrations.AddField(
            model_name='placement',
            name='record',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, related_name='placements', to='stats.YearRecord'),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='yearrecord',
            unique_together=set([('college', 'year')]),
        ),
    ]