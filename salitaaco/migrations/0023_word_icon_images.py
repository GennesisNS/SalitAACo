from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('salitaaco', '0022_guardian_board_icon_image'),
    ]

    operations = [
        # A word's picture, an admin's or a guardian's, is now an emoji or an uploaded picture, so the emoji may be empty.
        migrations.AlterField(
            model_name='addedword',
            name='emoji',
            field=models.CharField(blank=True, max_length=16),
        ),
        migrations.AddField(
            model_name='addedword',
            name='icon_image',
            field=models.ImageField(blank=True, upload_to='word-images/'),
        ),
        migrations.AddField(
            model_name='addedword',
            name='icon_mime',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AlterField(
            model_name='guardianword',
            name='emoji',
            field=models.CharField(blank=True, max_length=16),
        ),
        migrations.AddField(
            model_name='guardianword',
            name='icon_image',
            field=models.ImageField(blank=True, upload_to='guardian-word-images/'),
        ),
        migrations.AddField(
            model_name='guardianword',
            name='icon_mime',
            field=models.CharField(blank=True, max_length=50),
        ),
    ]
