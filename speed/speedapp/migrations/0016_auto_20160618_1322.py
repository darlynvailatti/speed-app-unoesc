# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-06-18 13:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('speedapp', '0015_teste_tempototalmax'),
    ]

    operations = [
        migrations.AlterField(
            model_name='teste',
            name='qtdVoltas',
            field=models.IntegerField(null=True),
        ),
    ]
