from django.db import migrations, models

# As in defaults/plans.py when this was written; a migration keeps its own copy.
FREE = "free"
FREE_FAMILY_VOICE_LIMIT = 2


def free_plan_family_voice_limit(apps, schema_editor):
    """The free plan keeps the 2 family voices it allowed before; every other plan, no limit, as before."""
    Plan = apps.get_model("salitaaco", "Plan")
    Plan.objects.filter(key=FREE).update(family_voice_limit=FREE_FAMILY_VOICE_LIMIT)


class Migration(migrations.Migration):

    dependencies = [
        ('salitaaco', '0027_add_default_users'),
    ]

    operations = [
        migrations.AddField(
            model_name='plan',
            name='family_voice_limit',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.RunPython(free_plan_family_voice_limit, migrations.RunPython.noop),
    ]
