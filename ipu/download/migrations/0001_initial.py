# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-07-26 14:51
from __future__ import unicode_literals

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import re


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('college', '0002_auto_20170613_2043'),
    ]

    operations = [
        migrations.CreateModel(
            name='Batch',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.CharField(choices=[('2008', '2008'), ('2009', '2009'), ('2010', '2010'), ('2011', '2011'), ('2012', '2012'), ('2013', '2013'), ('2014', '2014'), ('2015', '2015'), ('2016', '2016'), ('2017', '2017'), ('2018', '2018'), ('2019', '2019')], max_length=4)),
                ('college', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='batches', to='college.College')),
                ('stream', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='batches', to='college.Stream')),
            ],
            options={
                'verbose_name_plural': 'Batches',
            },
        ),
        migrations.CreateModel(
            name='DLRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('students', models.TextField(validators=[django.core.validators.RegexValidator(re.compile('^\\d+(?:\\,\\d+)*\\Z', 32), code='invalid', message='Enter only digits separated by commas.')])),
                ('batch', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='download_requests', to='download.Batch')),
            ],
        ),
        migrations.CreateModel(
            name='Requester',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('requested_on', models.DateTimeField(auto_now_add=True)),
                ('downloaded', models.BooleanField(default=False)),
                ('requested', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='requests', to='download.DLRequest')),
                ('requester', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='requests', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ZippedFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('zipped_file', models.FileField(upload_to='')),
                ('download_request', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='zipped_file', to='download.DLRequest')),
            ],
        ),
        migrations.AddField(
            model_name='dlrequest',
            name='requester',
            field=models.ManyToManyField(related_name='download_requests', through='download.Requester', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='batch',
            unique_together=set([('college', 'stream', 'year')]),
        ),
    ]
