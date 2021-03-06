# -*- coding: utf-8 -*-
# Generated by Django 1.11.26 on 2019-12-28 03:55
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PollResult',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('metric_name', models.TextField()),
                ('success', models.BooleanField()),
                ('result', models.TextField()),
                ('seconds_to_poll', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='Tick',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('machine', models.TextField()),
                ('date', models.DateTimeField()),
            ],
        ),
        migrations.AddField(
            model_name='pollresult',
            name='tick',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tutu.Tick'),
        ),
    ]
