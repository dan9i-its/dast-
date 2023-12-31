# Generated by Django 5.0 on 2023-12-08 10:32

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0008_har_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='ZapScan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(default='Новый', max_length=50, verbose_name='Статус')),
                ('full_scan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.fullscan')),
                ('har_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.har')),
            ],
        ),
        migrations.CreateModel(
            name='ZapTrigger',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rule', models.TextField(default=' ', verbose_name='Правило')),
                ('status', models.CharField(default='Новый', max_length=50, verbose_name='Статус')),
                ('description', models.TextField(default=' ', verbose_name='Описание')),
                ('Zap_scan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.zapscan')),
                ('har_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.har')),
            ],
        ),
    ]
