import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('salitaaco', '0025_merge_0024_delete_institution_0024_plan_child_limit'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='GeneratedReport',
            fields=[
                ('generated_report_id', models.AutoField(primary_key=True, serialize=False)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('report_type', models.CharField(choices=[('users', 'Mga User'), ('payments', 'Mga Bayad'), ('feedback', 'Feedback')], max_length=20)),
                ('file_type', models.CharField(choices=[('csv', 'CSV (para sa Excel o Google Sheets)'), ('printable', 'Pahinang ipi-print o ise-save bilang PDF')], max_length=20)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('file', models.FileField(upload_to='reports/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('generated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at', '-generated_report_id'],
            },
        ),
    ]
