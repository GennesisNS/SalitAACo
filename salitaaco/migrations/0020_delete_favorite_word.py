from django.db import migrations


class Migration(migrations.Migration):
    """The guardian's "Mga Paborito" page was removed, and with it the words it put on a child's Paborito screen."""

    dependencies = [
        ('salitaaco', '0019_separate_admin_accounts'),
    ]

    operations = [
        migrations.DeleteModel(
            name='FavoriteWord',
        ),
    ]
