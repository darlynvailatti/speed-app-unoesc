# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-06-05 16:52
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('speedapp', '0012_teste_origem'),
    ]

    operations = [
        migrations.AddField(
            model_name='teste',
            name='tipo',
            field=models.CharField(choices=[('0', 'Voltas realizadas'), ('1', 'Tempo decorrido')], default=0, max_length=1),
            preserve_default=False,
        ),
    ]
