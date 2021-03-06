# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-09-09 14:10
from __future__ import unicode_literals

from decimal import Decimal
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('student', '0010_auto_20160831_0903'),
        ('college', '0001_initial'),
        ('company', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Association',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('I', 'Internship'), ('J', 'Job')], default='J', max_length=1, verbose_name='Type')),
                ('salary', models.DecimalField(decimal_places=2, default=0, help_text='Salary to be offered in LPA.', max_digits=4, validators=[django.core.validators.MinValueValidator(Decimal('0'))], verbose_name='Salary (Lakhs P.A.)')),
                ('desc', models.TextField(blank=True, verbose_name="Placement details you'd want to mention")),
                ('initiator', models.CharField(choices=[('C', 'College'), ('CO', 'Company')], default='C', max_length=2, verbose_name='Who initiated it')),
                ('approved', models.NullBooleanField(default=None)),
                ('college', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='associations', to='college.College')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='associations', to='company.Company')),
                ('programme', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='associations', to='college.Programme')),
                ('streams', models.ManyToManyField(help_text='Choose particular stream(s).', related_name='associations', to='college.Stream')),
            ],
        ),
        migrations.CreateModel(
            name='Dissociation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('duration', models.DateField(blank=True, help_text='Choose the date till when you want to block this user from contacting you.', null=True)),
                ('initiator', models.CharField(choices=[('C', 'College'), ('CO', 'Company')], default='C', max_length=2, verbose_name='Who caused it')),
                ('college', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dissociations', to='college.College')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dissociations', to='company.Company')),
            ],
        ),
        migrations.CreateModel(
            name='PlacementSession',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(blank=True, help_text="Mention this placement session's current status for shortlisted students' knowledge. Eg. Resume Submission, Final Round, HR Round, Personal Interview Round", max_length=256, verbose_name='Current status')),
                ('application_deadline', models.DateField(help_text='Choose last date for students to apply. If no event is scheduled for now, choose an arbitrary future date.', null=True, verbose_name='Application Deadline')),
                ('ended', models.BooleanField(default=False, help_text='Setting it to true would mean that the students currently in the session are selected.', verbose_name='Has the placement session ended')),
                ('last_modified_by', models.CharField(choices=[('C', 'College'), ('CO', 'Company')], default='C', max_length=2)),
                ('association', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='session', to='recruitment.Association')),
            ],
        ),
        migrations.CreateModel(
            name='SelectionCriteria',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('current_year', models.CharField(blank=True, choices=[('1', '1 and above'), ('2', '2 and above'), ('3', '3 and above'), ('4', '4 and above')], max_length=1, verbose_name='Which year students may apply')),
                ('is_sub_back', models.BooleanField(default=False, verbose_name='Are student with any subject back(s) allowed')),
                ('tenth', models.CharField(blank=True, choices=[('50', '50 and above'), ('60', '60 and above'), ('70', '70 and above'), ('80', '80 and above'), ('90', '90 and above')], max_length=2, verbose_name='Xth Percentage')),
                ('twelfth', models.CharField(blank=True, choices=[('50', '50 and above'), ('60', '60 and above'), ('70', '70 and above'), ('80', '80 and above'), ('90', '90 and above')], max_length=2, verbose_name='XIIth Percentage')),
                ('graduation', models.CharField(blank=True, choices=[('50', '50 and above'), ('60', '60 and above'), ('70', '70 and above'), ('80', '80 and above'), ('90', '90 and above')], max_length=2, verbose_name='Graduation Percentage')),
                ('post_graduation', models.CharField(blank=True, choices=[('50', '50 and above'), ('60', '60 and above'), ('70', '70 and above'), ('80', '80 and above'), ('90', '90 and above')], max_length=2, verbose_name='Post Graduation Percentage')),
                ('doctorate', models.CharField(blank=True, choices=[('50', '50 and above'), ('60', '60 and above'), ('70', '70 and above'), ('80', '80 and above'), ('90', '90 and above')], max_length=2, verbose_name='Doctorate Percentage')),
            ],
        ),
        migrations.AddField(
            model_name='placementsession',
            name='selection_criteria',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sessions', to='recruitment.SelectionCriteria'),
        ),
        migrations.AddField(
            model_name='placementsession',
            name='students',
            field=models.ManyToManyField(blank=True, related_name='sessions', to='student.Student'),
        ),
        migrations.AlterUniqueTogether(
            name='dissociation',
            unique_together=set([('company', 'college')]),
        ),
    ]
