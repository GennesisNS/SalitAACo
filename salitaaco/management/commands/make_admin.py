from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand, CommandError

from salitaaco.defaults.administrator_roles import ADMINISTRATOR
from salitaaco.models.admin_account import AdminAccount
from salitaaco.utils.account import add_to_group, find_user_account


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

        if options["remove"]:
            user.groups.remove(*Group.objects.filter(name=ADMINISTRATOR))
            user.is_staff = False
            user.is_superuser = False
            user.save()
            # Their admin account goes too. A guardian or child account they
            # also have is left as it is, and is what they are from now on.
            for admin_account in AdminAccount.objects.filter(user=user):
                admin_account.remove_avatar(save=False)
                admin_account.delete()
            self.stdout.write(self.style.SUCCESS(f"{user.username} is no longer an admin."))
            return

        # An admin account is added next to whatever account the user already
        # has, which keeps a guardian's children and a child's guardian in place.
        if not AdminAccount.objects.filter(user=user).exists():
            existing_account = find_user_account(user)
            AdminAccount.objects.create(
                user=user,
                display_name=existing_account.display_name if existing_account else user.username,
            )
        add_to_group(user, ADMINISTRATOR)

        if options["staff"]:
            # Staff status opens Django's admin site; superuser status lets the account edit everything in it.
            user.is_staff = True
            user.is_superuser = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f"{user.username} is now an admin and can log in to Django's admin site."))
        else:
            self.stdout.write(self.style.SUCCESS(f"{user.username} is now an admin."))
