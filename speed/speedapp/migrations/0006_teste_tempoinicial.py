# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-05-02 03:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('speedapp', '0005_auto_20160502_0250'),
    ]

    operations = [
        migrations.AddField(
            model_name='teste',
            name='tempoInicial',
            field=models.FloatField(null=True),
        ),
    ]
