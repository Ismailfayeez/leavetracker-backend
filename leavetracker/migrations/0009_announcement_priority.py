# Generated by Django 4.0.6 on 2023-03-13 06:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leavetracker', '0008_announcement_announcementteam'),
    ]

    operations = [
        migrations.AddField(
            model_name='announcement',
            name='priority',
            field=models.CharField(choices=[('H', 'high'), ('M', 'medium'), ('L', 'low')], default='H', max_length=1),
        ),
    ]
