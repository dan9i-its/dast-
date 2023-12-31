# Generated by Django 5.0 on 2023-12-07 13:10

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0006_alter_nucleitrigger_description_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='nucleitrigger',
            name='description',
            field=models.TextField(default=' ', verbose_name='Описание'),
        ),
        migrations.CreateModel(
            name='CrawlScan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('domain', models.CharField(max_length=250, verbose_name='Домен')),
                ('status', models.CharField(max_length=150, verbose_name='Статус краулинга')),
                ('full_scan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.fullscan')),
            ],
            options={
                'verbose_name': 'Crawl скан',
                'verbose_name_plural': 'Сканы краулеров',
            },
        ),
        migrations.CreateModel(
            name='Har',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('har', models.TextField(default=' ', verbose_name='Запрос')),
                ('domain', models.CharField(default=' ', max_length=250, verbose_name='Домен')),
                ('CrawlScan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.crawlscan')),
            ],
            options={
                'verbose_name': 'HAR',
                'verbose_name_plural': 'HARs',
            },
        ),
    ]
