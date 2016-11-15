# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-06-05 02:09
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('speedapp', '0010_teste_atleta'),
    ]

    operations = [
        migrations.CreateModel(
            name='AtletaTeste',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('atleta', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='speedapp.Atleta')),
            ],
        ),
        migrations.RemoveField(
            model_name='teste',
            name='atleta',
        ),
        migrations.AddField(
            model_name='atletateste',
            name='teste',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='speedapp.Teste'),
        ),
    ]
