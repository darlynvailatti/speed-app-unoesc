# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-05-02 03:31
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('speedapp', '0006_teste_tempoinicial'),
    ]

    operations = [
        migrations.AddField(
            model_name='teste',
            name='testeFinalizado',
            field=models.BooleanField(default=False),
            preserve_default=False,
        ),
    ]
