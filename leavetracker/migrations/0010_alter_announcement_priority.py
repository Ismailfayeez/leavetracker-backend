# Generated by Django 4.0.6 on 2023-03-13 07:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leavetracker', '0009_announcement_priority'),
    ]

    operations = [
        migrations.AlterField(
            model_name='announcement',
            name='priority',
            field=models.CharField(choices=[('H', 'high'), ('M', 'medium'), ('L', 'low')], default='L', max_length=1),
        ),
    ]
