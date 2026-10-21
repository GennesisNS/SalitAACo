import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('salitaaco', '0020_delete_favorite_word'),
    ]

    operations = [
        # The one limit there was is the paid plan's tile limit, and keeps its value.
        migrations.RenameField(
            model_name='sitesetting',
            old_name='guardian_word_limit',
            new_name='plus_word_limit',
        ),
        migrations.AddField(
            model_name='sitesetting',
            name='free_word_limit',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='sitesetting',
            name='free_board_limit',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='sitesetting',
            name='plus_board_limit',
            field=models.PositiveSmallIntegerField(default=5),
        ),
        migrations.CreateModel(
            name='GuardianBoard',
            fields=[
                ('guardian_board_id', models.AutoField(primary_key=True, serialize=False)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('name', models.CharField(max_length=40)),
                ('emoji', models.CharField(max_length=16)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('guardian', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='boards', to='salitaaco.guardianaccount')),
            ],
            options={
                'ordering': ['created_at', 'guardian_board_id'],
                'constraints': [models.UniqueConstraint(fields=('guardian', 'name'), name='unique_guardian_board')],
            },
        ),
    ]
