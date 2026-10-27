from django.db import migrations


def delete_tile_pictures(apps, schema_editor):
    """
    A tile's own picture is no longer made on the board: a tile's picture is
    its emoji, or the one uploaded with it (Sariling Tile, Mga Salita). The
    pictures made before are deleted with their files; a customization that
    has a recording keeps it, and one that had only a picture goes.
    """
    Customization = apps.get_model("salitaaco", "Customization")
    for customization in Customization.objects.exclude(image=""):
        customization.image.storage.delete(customization.image.name)
        if not customization.sound:
            customization.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('salitaaco', '0028_plan_family_voice_limit'),
    ]

    operations = [
        # Going back brings the columns back empty: the pictures are gone.
        migrations.RunPython(delete_tile_pictures, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='customization',
            name='image',
        ),
        migrations.RemoveField(
            model_name='customization',
            name='image_mime',
        ),
    ]
