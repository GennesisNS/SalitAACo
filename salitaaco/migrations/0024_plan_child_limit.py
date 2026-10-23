from django.db import migrations, models

# As in defaults/plans.py when this was written; a migration keeps its own copy.
FREE = "free"
FREE_CHILD_LIMIT = 1


def free_plan_child_limit(apps, schema_editor):
    """Every plan starts at the paid number of child accounts; the free plan at its own."""
    Plan = apps.get_model("salitaaco", "Plan")
    Plan.objects.filter(key=FREE).update(child_limit=FREE_CHILD_LIMIT)


class Migration(migrations.Migration):

    dependencies = [
        ('salitaaco', '0023_word_icon_images'),
    ]

    operations = [
        migrations.AddField(
            model_name='plan',
            name='child_limit',
            field=models.PositiveSmallIntegerField(default=3),
        ),
        migrations.RunPython(free_plan_child_limit, migrations.RunPython.noop),
    ]
