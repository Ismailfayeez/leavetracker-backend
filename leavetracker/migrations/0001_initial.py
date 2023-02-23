# Generated by Django 4.0.6 on 2023-02-20 07:27

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('project', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Access',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('code', models.CharField(max_length=4)),
            ],
            options={
                'unique_together': {('code', 'name')},
            },
        ),
        migrations.CreateModel(
            name='Domain',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('code', models.CharField(max_length=4)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='project.project')),
            ],
            options={
                'unique_together': {('code', 'project')},
            },
        ),
        migrations.CreateModel(
            name='Employee',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('A', 'active'), ('C', 'closed'), ('IN', 'inactive')], default='A', max_length=2)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('domain', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='leavetracker.domain')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='project.project')),
            ],
        ),
        migrations.CreateModel(
            name='EmployeeAccessList',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=5, unique=True)),
                ('name', models.CharField(max_length=255, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='LeaveDuration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=4)),
                ('name', models.CharField(max_length=15)),
                ('hours', models.DecimalField(decimal_places=2, max_digits=4)),
                ('status', models.CharField(choices=[('A', 'active'), ('C', 'closed'), ('IN', 'inactive')], default='A', max_length=2)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='project.project')),
            ],
            options={
                'unique_together': {('code', 'project')},
            },
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('code', models.CharField(max_length=4)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='project.project')),
            ],
            options={
                'unique_together': {('code', 'project')},
            },
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='team_created_by', to='leavetracker.employee')),
                ('modified_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='team_modified_by', to='leavetracker.employee')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='project.project')),
            ],
        ),
        migrations.CreateModel(
            name='Supervisor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('employee', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='supervisor', to='leavetracker.employee')),
                ('supervisor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='supervisor_employees', to='leavetracker.employee')),
            ],
        ),
        migrations.CreateModel(
            name='RoleAccess',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('access', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='leavetracker.access')),
                ('role', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='role_access', to='leavetracker.role')),
            ],
        ),
        migrations.CreateModel(
            name='LeaveType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=4)),
                ('name', models.CharField(max_length=20)),
                ('hours', models.DecimalField(decimal_places=2, max_digits=5)),
                ('days', models.IntegerField()),
                ('status', models.CharField(choices=[('A', 'active'), ('C', 'closed'), ('IN', 'inactive')], default='A', max_length=2)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='project.project')),
            ],
            options={
                'unique_together': {('project', 'code')},
            },
        ),
        migrations.CreateModel(
            name='LeaveRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('request_number', models.IntegerField(unique=True)),
                ('from_date', models.DateField()),
                ('to_date', models.DateField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(null=True)),
                ('status', models.CharField(choices=[('P', 'Pending'), ('A', 'Accepted'), ('D', 'Deleted'), ('R', 'Rejected'), ('C', 'Cancelled')], default='P', max_length=1)),
                ('duration', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='leavetracker.leaveduration')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='leave_request', to='leavetracker.employee')),
                ('modified_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='leave_request_modified_by', to='leavetracker.employee')),
                ('type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='leave_request', to='leavetracker.leavetype')),
            ],
        ),
        migrations.CreateModel(
            name='LeaveApproval',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('approver_status', models.CharField(choices=[('P', 'Pending'), ('A', 'Accepted'), ('D', 'Deleted'), ('R', 'Rejected'), ('C', 'Cancelled')], default='P', max_length=1)),
                ('approver', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='leavetracker.employee')),
                ('request_number', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='leave_approval', to='leavetracker.leaverequest')),
            ],
        ),
        migrations.CreateModel(
            name='EmployeeAccess',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('access_code', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='leavetracker.employeeaccesslist')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='leavetracker.employee')),
            ],
        ),
        migrations.AddField(
            model_name='employee',
            name='role',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='leavetracker.role'),
        ),
        migrations.AddField(
            model_name='employee',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='employee', to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='TeamMember',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('P', 'participant'), ('A', 'admin')], default='P', max_length=1)),
                ('is_contact', models.CharField(choices=[('Y', 'yes'), ('N', 'no')], default='N', max_length=1)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='teams', to='leavetracker.employee')),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='team_members', to='leavetracker.team')),
            ],
            options={
                'unique_together': {('employee', 'team')},
            },
        ),
        migrations.CreateModel(
            name='SubscribeTeam',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscribed_team_employee', to='leavetracker.employee')),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscribed_teams', to='leavetracker.team')),
            ],
            options={
                'unique_together': {('employee', 'team')},
            },
        ),
        migrations.CreateModel(
            name='LTAccountPreference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='project.project')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'project')},
            },
        ),
        migrations.CreateModel(
            name='LeaveDate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('request_number', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='leave_dates', to='leavetracker.leaverequest')),
            ],
            options={
                'unique_together': {('request_number', 'date')},
            },
        ),
        migrations.CreateModel(
            name='FiscalYear',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('month', models.CharField(max_length=3)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fiscal_year', to='project.project')),
            ],
            options={
                'unique_together': {('project', 'month')},
            },
        ),
        migrations.AlterUniqueTogether(
            name='employee',
            unique_together={('user', 'project')},
        ),
        migrations.CreateModel(
            name='Approver',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('approver', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='approver_employees', to='leavetracker.employee')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='approvers', to='leavetracker.employee')),
            ],
            options={
                'unique_together': {('employee', 'approver')},
            },
        ),
    ]
