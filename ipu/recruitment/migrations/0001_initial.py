# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-08-09 10:21
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('college', '0001_initial'),
        ('company', '0001_initial'),
        ('student', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Association',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('desc', models.TextField(blank=True, help_text='You can add job details, some specific skills you are looking for. Eg. iOS Developer', verbose_name='Placement details')),
                ('initiator', models.CharField(choices=[('C', 'College'), ('CO', 'Company')], default='C', max_length=2, verbose_name='Who initiated it')),
                ('college', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='associations', to='college.College')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='associations', to='company.Company')),
                ('programme', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='associations', to='college.Programme')),
                ('streams', models.ManyToManyField(help_text='Choose particular subject(s).', related_name='associations', to='college.Stream')),
            ],
        ),
        migrations.CreateModel(
            name='Dissociation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('duration', models.DateField(blank=True, help_text='Choose the date till when you want to block the associations with this user.', null=True)),
                ('initiator', models.CharField(choices=[('C', 'College'), ('CO', 'Company')], default='C', max_length=2, verbose_name='Who caused it')),
                ('college', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='disassociations', to='college.College')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='disassociations', to='company.Company')),
            ],
        ),
        migrations.CreateModel(
            name='PlacementSession',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(blank=True, help_text="Mention this placement session's current status for shortlisted students' knowledge. Eg. Resume Submission, Final Round, HR Round, Personal Interview Round", max_length=256, verbose_name='Current status')),
                ('recent_deadline', models.DateField(help_text='Choose the deadline date for an event. Eg. Last date for applying', null=True, verbose_name='Deadline')),
                ('ended', models.BooleanField(default=False, help_text='This would mean that the student currently in the session are selected.', verbose_name='Has the placement session has ended')),
                ('association', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='session', to='recruitment.Association')),
                ('students', models.ManyToManyField(blank=True, related_name='sessions', to='student.Student')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='dissociation',
            unique_together=set([('company', 'college')]),
        ),
    ]