# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-06-03 01:00
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('speedapp', '0008_teste_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='Atleta',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=120)),
                ('sobreNome', models.CharField(max_length=50, null=True)),
                ('dataNascimento', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='AtletaAtributos',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dataHora', models.DateTimeField()),
                ('pesoEmKg', models.FloatField()),
                ('atleta', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='speedapp.Atleta')),
            ],
        ),
        migrations.CreateModel(
            name='Desporto',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descricao', models.CharField(max_length=100)),
            ],
        ),
        migrations.AddField(
            model_name='atleta',
            name='desporto',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='speedapp.Desporto'),
        ),
    ]
