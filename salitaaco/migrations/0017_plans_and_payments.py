import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

# The two plans the site started with. They are written out here, not imported,
# so that this migration makes the same rows whatever the code says later.
FIRST_PLANS = [
    {
        "key": "free",
        "name": "Free",
        "price": 0,
        "position": 1,
        "features": "\n".join([
            "Mga pangunahing board ng simbolo",
            "Mga karaniwang sitwasyong Pilipino",
            "Boses na text-to-speech",
            "Pag-set up ng profile ng tagapag-alaga",
        ]),
    },
    {
        "key": "plus",
        "name": "SalitAACo Plus",
        "price": 149,
        "position": 2,
        "features": "\n".join([
            "Lahat ng nasa Free",
            "Boses ng pamilya (family voice banking)",
            "Mada-download na ulat ng paggamit",
            "Karagdagang mga scenario pack",
        ]),
    },
]


def create_plans(apps, schema_editor):
    Plan = apps.get_model("salitaaco", "Plan")
    for plan in FIRST_PLANS:
        Plan.objects.get_or_create(key=plan["key"], defaults=plan)


def delete_plans(apps, schema_editor):
    Plan = apps.get_model("salitaaco", "Plan")
    Plan.objects.filter(key__in=[plan["key"] for plan in FIRST_PLANS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('salitaaco', '0016_institutions'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesetting',
            name='gcash_qr',
            field=models.ImageField(blank=True, upload_to='payment-qr/'),
        ),
        migrations.AddField(
            model_name='sitesetting',
            name='gcash_qr_mime',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='sitesetting',
            name='gcash_name',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='sitesetting',
            name='gcash_number',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.CreateModel(
            name='Plan',
            fields=[
                ('plan_id', models.AutoField(primary_key=True, serialize=False)),
                ('key', models.SlugField(max_length=20, unique=True)),
                ('name', models.CharField(max_length=60)),
                ('price', models.PositiveIntegerField(default=0)),
                ('features', models.TextField(blank=True)),
                ('offered', models.BooleanField(default=True)),
                ('position', models.PositiveSmallIntegerField(default=0)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['position', 'plan_id'],
            },
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('payment_id', models.AutoField(primary_key=True, serialize=False)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('amount', models.PositiveIntegerField()),
                ('proof', models.ImageField(upload_to='payment-proofs/')),
                ('proof_mime', models.CharField(max_length=50)),
                ('status', models.CharField(choices=[('pending', 'Naghihintay'), ('approved', 'Aprubado'), ('rejected', 'Tinanggihan')], default='pending', max_length=10)),
                ('note', models.CharField(blank=True, max_length=300)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('starts_at', models.DateTimeField(blank=True, null=True)),
                ('ends_at', models.DateTimeField(blank=True, null=True)),
                ('guardian', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='salitaaco.guardianaccount')),
                ('plan', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='payments', to='salitaaco.plan')),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at', '-payment_id'],
            },
        ),
        migrations.RunPython(create_plans, delete_plans),
    ]
