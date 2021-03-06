# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-06-28 16:40
from __future__ import unicode_literals

from decimal import Decimal
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0016_auto_20170627_1125'),
    ]

    operations = [
        migrations.CreateModel(
            name='CGPAMarksheet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cgpa', models.DecimalField(decimal_places=1, default=Decimal('0'), max_digits=3, validators=[django.core.validators.MinValueValidator(Decimal('0')), django.core.validators.MaxValueValidator(Decimal('10'))], verbose_name='CGPA')),
                ('conversion_factor', models.DecimalField(decimal_places=1, default=Decimal('0'), help_text='CGPA to Percentage conversion factor. Most likely it will be mentioned in your marksheet. Eg. 9.5 for CBSE (10th standard)', max_digits=3, validators=[django.core.validators.MinValueValidator(Decimal('0')), django.core.validators.MaxValueValidator(Decimal('10'))], verbose_name='Conversion Factor')),
            ],
        ),
        migrations.CreateModel(
            name='ExaminationBoard',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, unique=True)),
                ('abbreviation', models.CharField(blank=True, max_length=16, verbose_name='Abbreviation')),
            ],
        ),
        migrations.CreateModel(
            name='SchoolMarksheet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cgpa_marksheet', models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='student.CGPAMarksheet')),
            ],
        ),
        migrations.CreateModel(
            name='Score',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject_name', models.CharField(help_text='You are mandated to enter the subject name exactly the same as is in marksheet.', max_length=128)),
                ('subject_code', models.CharField(blank=True, help_text='Fill correct subject code, if provided in marksheet.', max_length=10)),
                ('marks', models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)], verbose_name='Marks out of 100')),
            ],
        ),
        migrations.CreateModel(
            name='ScoreMarksheet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('klass', models.CharField(choices=[('10', 'Tenth'), ('12', 'Twelfth')], default='Tenth', max_length=2, verbose_name='For Which Class')),
                ('board', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='marksheets', to='student.ExaminationBoard', verbose_name='Examination Board')),
                ('score1', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='marksheets_1', to='student.Score', verbose_name='Subject 1')),
                ('score2', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='marksheets_2', to='student.Score', verbose_name='Subject 2')),
                ('score3', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='marksheets_3', to='student.Score', verbose_name='Subject 3')),
                ('score4', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='marksheets_4', to='student.Score', verbose_name='Subject 4')),
                ('score5', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='marksheets_5', to='student.Score', verbose_name='Subject 5')),
                ('score6', models.ForeignKey(blank=True, help_text='Optional', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='marksheets_6', to='student.Score', verbose_name='Subject 6')),
            ],
        ),
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, unique=True)),
                ('code', models.CharField(blank=True, max_length=10)),
            ],
        ),
        migrations.RemoveField(
            model_name='qualification',
            name='tenth_cgpa',
        ),
        migrations.AddField(
            model_name='score',
            name='subject',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='scores', to='student.Subject'),
        ),
        migrations.AddField(
            model_name='schoolmarksheet',
            name='marksheet_10',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='school_marksheet_10', to='student.ScoreMarksheet'),
        ),
        migrations.AddField(
            model_name='schoolmarksheet',
            name='marksheet_12',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='school_marksheet_12', to='student.ScoreMarksheet'),
        ),
        migrations.AddField(
            model_name='cgpamarksheet',
            name='board',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cgpas', to='student.ExaminationBoard'),
        ),
        migrations.AddField(
            model_name='student',
            name='marksheet',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='student.SchoolMarksheet'),
        ),
    ]
