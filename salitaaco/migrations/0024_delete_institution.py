from django.db import migrations


class Migration(migrations.Migration):
    """The admin's "Mga Paaralan at Institusyon" page was removed, and with it its records of schools and centres."""

    dependencies = [
        ('salitaaco', '0023_word_icon_images'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Institution',
        ),
    ]
