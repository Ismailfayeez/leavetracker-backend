# Generated by Django 4.0.6 on 2023-02-21 07:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='projectadminaccess',
            name='code',
            field=models.CharField(max_length=20, unique=True),
        ),
    ]