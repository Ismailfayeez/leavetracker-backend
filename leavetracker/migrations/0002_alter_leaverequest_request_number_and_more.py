# Generated by Django 4.0.6 on 2023-02-20 09:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0001_initial'),
        ('leavetracker', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='leaverequest',
            name='request_number',
            field=models.IntegerField(),
        ),
        migrations.AlterUniqueTogether(
            name='leaverequest',
            unique_together={('request_number', 'employee')},
        ),
        migrations.CreateModel(
            name='LatestLeaveRequestNumber',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('request_id', models.IntegerField()),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='project.project')),
            ],
        ),
    ]