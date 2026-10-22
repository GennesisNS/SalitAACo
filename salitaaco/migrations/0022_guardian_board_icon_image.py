from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('salitaaco', '0021_guardian_boards_and_plan_limits'),
    ]

    operations = [
        # A board's picture is now an emoji or an uploaded picture, so the emoji may be empty.
        migrations.AlterField(
            model_name='guardianboard',
            name='emoji',
            field=models.CharField(blank=True, max_length=16),
        ),
        migrations.AddField(
            model_name='guardianboard',
            name='icon_image',
            field=models.ImageField(blank=True, upload_to='guardian-board-icons/'),
        ),
        migrations.AddField(
            model_name='guardianboard',
            name='icon_mime',
            field=models.CharField(blank=True, max_length=50),
        ),
    ]
