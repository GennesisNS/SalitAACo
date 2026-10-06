from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand, CommandError

from salitaaco.defaults.administrator_roles import ADMINISTRATOR


class Command(BaseCommand):
    help = (
        "Give an account access to the admin dashboard, and with --staff to Django's "
        "admin site as well (or take both away with --remove)."
    )

    def add_arguments(self, parser):
        parser.add_argument("username")
        parser.add_argument(
            "--staff", action="store_true",
            help="Also let the account log in to Django's admin site (/admin/ when SHOW_ADMIN_ROUTES is on).",
        )
        parser.add_argument("--remove", action="store_true", help="Remove admin access instead of granting it.")

    def handle(self, *args, **options):
        user = User.objects.filter(username__iexact=options["username"]).first()
        if user is None:
            raise CommandError(f"No account with the username '{options['username']}'.")

        group, _ = Group.objects.get_or_create(name=ADMINISTRATOR)

        if options["remove"]:
            user.groups.remove(group)
            user.is_staff = False
            user.is_superuser = False
            user.save()
            self.stdout.write(self.style.SUCCESS(f"{user.username} is no longer an admin."))
            return

        user.groups.add(group)
        if options["staff"]:
            # Staff status opens Django's admin site; superuser status lets the account edit everything in it.
            user.is_staff = True
            user.is_superuser = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f"{user.username} is now an admin and can log in to Django's admin site."))
        else:
            self.stdout.write(self.style.SUCCESS(f"{user.username} is now an admin."))
