# Generated by Django 5.1.6 on 2025-04-07 12:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='crimedata',
            name='offense',
            field=models.CharField(max_length=500),
        ),
    ]
