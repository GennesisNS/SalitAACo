import MySQLdb
import MySQLdb.cursors
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from salitaaco.utils import legacy_import

LEGACY_TABLES = ["users", "customizations", "word_usage", "ratings"]


class Command(BaseCommand):
    help = (
        "Copy accounts, pictures, recordings, usage counts and ratings from the PHP "
        "application's database (the LEGACY_DB_* settings) into this one."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Read the old database and report what would be imported, without writing anything.",
        )

    def connect(self):
        legacy = settings.LEGACY_DATABASE
        if not legacy["NAME"]:
            raise CommandError("Set LEGACY_DB_NAME (and the other LEGACY_DB_* values) in .env first.")
        try:
            return MySQLdb.connect(
                host=legacy["HOST"],
                port=legacy["PORT"],
                user=legacy["USER"],
                passwd=legacy["PASSWORD"],
                db=legacy["NAME"],
                charset="utf8mb4",
                cursorclass=MySQLdb.cursors.DictCursor,
            )
        except MySQLdb.Error as error:
            raise CommandError(
                f"Could not open the old database '{legacy['NAME']}' on {legacy['HOST']}:{legacy['PORT']}: {error.args[-1]}"
            )

    def fetch(self, sql, params=None):
        """Run a query on the old database and return its rows as dicts."""
        with self.legacy.cursor() as cursor:
            cursor.execute(sql, params or [])
            return list(cursor.fetchall())

    def handle(self, *args, **options):
        self.legacy = self.connect()
        try:
            self.run_import(dry_run=options["dry_run"])
        finally:
            self.legacy.close()

    def run_import(self, dry_run):
        found = {row["TABLE_NAME"] for row in self.fetch(
            "SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA = DATABASE()"
        )}
        missing = [table for table in LEGACY_TABLES if table not in found]
        if missing:
            raise CommandError(f"The old database has no table named: {', '.join(missing)}.")

        if dry_run:
            for table in LEGACY_TABLES:
                count = self.fetch(f"SELECT COUNT(*) AS total FROM {table}")[0]["total"]
                self.stdout.write(f"{table}: {count} rows")
            self.stdout.write("Dry run: nothing was imported.")
            return

        user_ids = [row["id"] for row in self.fetch("SELECT id FROM users ORDER BY id")]
        imported = skipped = 0

        # One account at a time, each in its own transaction: the pictures and
        # recordings of one account are the most that is held in memory, and a
        # failure leaves earlier accounts imported and this one untouched.
        for user_id in user_ids:
            row = self.fetch("SELECT * FROM users WHERE id = %s", [user_id])[0]

            with transaction.atomic():
                user = legacy_import.import_user(row)
                if user is None:
                    skipped += 1
                    self.stdout.write(self.style.WARNING(f"Skipped {row['username']}: username already exists."))
                    continue

                for customization in self.fetch("SELECT * FROM customizations WHERE user_id = %s", [user_id]):
                    legacy_import.import_customization(user, customization)
                for usage in self.fetch("SELECT * FROM word_usage WHERE user_id = %s", [user_id]):
                    legacy_import.import_word_usage(user, usage)
                for rating in self.fetch("SELECT * FROM ratings WHERE user_id = %s", [user_id]):
                    legacy_import.import_rating(user, rating)

            imported += 1
            self.stdout.write(f"Imported {row['username']}")

        self.stdout.write(self.style.SUCCESS(f"Done: {imported} accounts imported, {skipped} skipped."))
