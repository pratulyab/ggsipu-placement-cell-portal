# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-06-24 10:53
from __future__ import unicode_literals

from decimal import Decimal
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='College',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('college_name', models.CharField(max_length=200)),
                ('college_code', models.CharField(max_length=3)),
                ('college_alias', models.CharField(blank=True, max_length=20)),
                ('year', models.CharField(max_length=4)),
                ('jobs_placement_percentage', models.DecimalField(decimal_places=2, default=0, max_digits=5, validators=[django.core.validators.MinValueValidator(Decimal('0')), django.core.validators.MaxValueValidator(Decimal('100'))], verbose_name='Percentage Placed for Jobs')),
                ('internships_placement_percentage', models.DecimalField(decimal_places=2, default=0, max_digits=5, validators=[django.core.validators.MinValueValidator(Decimal('0')), django.core.validators.MaxValueValidator(Decimal('100'))], verbose_name='Percentage of Internships')),
                ('students_participated_jobs', models.PositiveSmallIntegerField(default=0)),
                ('students_selected_jobs', models.PositiveSmallIntegerField(default=0)),
                ('students_participated_internships', models.PositiveSmallIntegerField(default=0)),
                ('students_selected_internships', models.PositiveSmallIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_name', models.CharField(max_length=200)),
                ('website', models.URLField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Placement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('J', 'Job'), ('I', 'Internship')], default='J', max_length=1)),
                ('salary', models.DecimalField(decimal_places=2, default=0, max_digits=4, validators=[django.core.validators.MinValueValidator(Decimal('0'))], verbose_name='Salary (Lakhs P.A.)')),
                ('salary_comment', models.CharField(blank=True, max_length=20)),
                ('total_students_selected', models.PositiveSmallIntegerField(default=0)),
                ('college', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='placements', to='stats.College')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='placements', to='stats.Company')),
            ],
        ),
        migrations.AddField(
            model_name='college',
            name='companies',
            field=models.ManyToManyField(blank=True, related_name='colleges', through='stats.Placement', to='stats.Company'),
        ),
        migrations.AlterUniqueTogether(
            name='college',
            unique_together=set([('college_code', 'year')]),
        ),
    ]
