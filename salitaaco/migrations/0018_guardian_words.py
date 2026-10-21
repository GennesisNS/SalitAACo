import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('salitaaco', '0017_plans_and_payments'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesetting',
            name='guardian_word_limit',
            field=models.PositiveSmallIntegerField(default=20),
        ),
        migrations.CreateModel(
            name='GuardianWord',
            fields=[
                ('guardian_word_id', models.AutoField(primary_key=True, serialize=False)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('board', models.CharField(max_length=100)),
                ('word', models.CharField(max_length=40)),
                ('emoji', models.CharField(max_length=16)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('guardian', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='words', to='salitaaco.guardianaccount')),
            ],
            options={
                'ordering': ['created_at', 'guardian_word_id'],
                'constraints': [models.UniqueConstraint(fields=('guardian', 'word'), name='unique_guardian_word')],
            },
        ),
    ]
