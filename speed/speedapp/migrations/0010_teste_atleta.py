# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-06-03 01:56
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('speedapp', '0009_auto_20160603_0100'),
    ]

    operations = [
        migrations.AddField(
            model_name='teste',
            name='atleta',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='speedapp.Atleta'),
            preserve_default=False,
        ),
    ]
