# Generated by Django 4.0.6 on 2023-03-23 01:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('leavetracker', '0011_announcementviewedemployee'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='announcementviewedemployee',
            unique_together={('announcement', 'employee')},
        ),
    ]