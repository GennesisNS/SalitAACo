from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('salitaaco', '0029_remove_customization_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='guardianaccount',
            name='age',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='guardianaccount',
            name='privacy_consent_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='guardianaccount',
            name='privacy_consent_version',
            field=models.CharField(blank=True, max_length=20),
        ),
    ]
