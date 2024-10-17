# Generated by Django 5.0.6 on 2024-10-17 11:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('API', '0004_sensordata_air_quality_index'),
    ]

    operations = [
        migrations.CreateModel(
            name='HealthTip',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='RiskAlert',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('element', models.CharField(max_length=255)),
                ('threshold_high', models.FloatField()),
                ('threshold_bad', models.FloatField()),
                ('danger_message', models.TextField()),
                ('solution_message', models.TextField()),
            ],
        ),
    ]
