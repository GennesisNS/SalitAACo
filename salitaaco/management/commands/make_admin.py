import getpass
import os

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from salitaaco.forms.validators import name_validator, validate_password_strength
from salitaaco.utils.account import create_admin, delete_user_account
from salitaaco.utils.perms_check import is_administrator

# For scripts: the new admin's password, so that it is not asked for (and not typed on the command line).
PASSWORD_VARIABLE = "ADMIN_PASSWORD"


class Command(BaseCommand):
    help = (
        "Make a new admin account, separate from every guardian's and child's account (or delete one "
        "with --remove). The password is asked for, or read from ADMIN_PASSWORD."
    )

    def add_arguments(self, parser):
        parser.add_argument("username", help="The new admin's username. No account may have it yet.")
        parser.add_argument("--name", help="The name shown for the admin. The username when left out.")
        parser.add_argument(
            "--staff", action="store_true",
            help="Also let the account log in to Django's admin site (/admin/ when SHOW_ADMIN_ROUTES is on).",
        )
        parser.add_argument("--remove", action="store_true", help="Delete this admin's account instead.")

    def handle(self, *args, **options):
        username = options["username"]
        existing = User.objects.filter(username__iexact=username).first()

        if options["remove"]:
            if existing is None or not is_administrator(existing):
                raise CommandError(f"No admin account with the username '{username}'.")
            delete_user_account(existing)
            self.stdout.write(self.style.SUCCESS(f"Deleted the admin account {existing.username}."))
            return

        if existing is not None:
            raise CommandError(
                f"The username '{existing.username}' is taken. An admin is a new account of its own, "
                "never a guardian's or a child's: choose another username."
            )

        display_name = options["name"] or username
        password = os.environ.get(PASSWORD_VARIABLE) or self.ask_password()
        try:
            if options["name"]:
                name_validator(display_name)
            validate_password_strength(password)
        except ValidationError as error:
            raise CommandError(" ".join(error.messages))

        create_admin(username, display_name, password, staff=options["staff"])
        also = " It can log in to Django's admin site too." if options["staff"] else ""
        self.stdout.write(self.style.SUCCESS(f"Made the admin account {username}.{also}"))

    def ask_password(self):
        password = getpass.getpass("Password: ")
        if password != getpass.getpass("Password (again): "):
            raise CommandError("The passwords do not match.")
        return password
