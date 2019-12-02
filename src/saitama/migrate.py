import re
import sys

from psycopg2 import sql

from saitama.common import Connection
from saitama.queries import migration as migration_queries


class Migrations(Connection):
    __slots__ = [
        "_settings",
        "_cli_args",
        "_prepend",
        "cursor",
        "db_options",
        "migration_options",
    ]

    migration_name = re.compile(
        r"(?P<migration_id>\d+)_(?P<backwards>backwards_)?(?P<name>.+).sql"
    )

    def __init__(self, cli_args, prepend=None, **kwargs):
        super().__init__(cli_args, prepend, **kwargs)
        self.migration_options = self._migration_args(
            cli_args, testing=kwargs.get("testing")
        )

    def run(self):
        self._run_commands(self._prepare_db, dbname="template1", autocommit=True)
        self._run_commands(self._create_migration_schema, self._migrate)

    def _migration_args(self, args, *, testing=False):
        migrations_dir = self._settings.migrations
        if testing:
            return {
                "drop": True,
                "interactive": False,
                "fake": False,
                "backwards": False,
                "migration": None,
                "migration_dir": migrations_dir,
                "quiet": True,
            }

        return {
            "drop": args.drop,
            "interactive": not args.yes,
            "fake": args.fake,
            "backwards": args.backwards,
            "migration": args.migration,
            "migration_dir": migrations_dir,
            "quiet": False,
        }

    def _create_migration_schema(self):
        self.cursor.execute(migration_queries.create_schema)
        self.cursor.execute(migration_queries.create_table)

    @staticmethod
    def _confirm_drop():
        print("WARNING: All data in the existing database will be lost!")
        while True:
            confirmation = input("Are you sure you want to continue? [y/N] ")
            if confirmation.lower() in ["y", "yes"]:
                confirmation = True
                break
            if confirmation.lower() in ["n", "no", ""]:
                confirmation = False
                break
        if not confirmation:
            raise RuntimeError("Migrations cancelled by the user")

    def _prepare_db(self):
        dbname = self.db_options["dbname"]
        drop = self.migration_options["drop"]
        quiet = self.migration_options["quiet"]

        self.cursor.execute(migration_queries.db_exists, {"dbname": dbname})
        exists = self.cursor.fetchone()[0]
        if exists and drop:
            if self.migration_options["interactive"]:
                self._confirm_drop()
            else:
                if not quiet:
                    print("WARNING: All data in the existing database will be lost!")
            self.cursor.execute(migration_queries.terminate_db, {"dbname": dbname})
            self.cursor.execute(migration_queries.drop_db.format(dbname=dbname))
        if not exists or drop:
            if not exists and not quiet:
                print(f"Database {dbname} does not exist, creating...")
            self.cursor.execute(
                sql.SQL(migration_queries.create_db.format(dbname=dbname))
            )

    @staticmethod
    def _check_migrations(state, target, collected_migrations):
        if state > target:
            state, target = target, state
        keys = sorted(collected_migrations.keys())
        start = keys[0]
        end = keys[-1]
        if start != state + 1 or end != target or end - start + 1 != target - state:
            raise LookupError("Missing migrations")

    def _valid_migrations(self, last_migration):
        backwards = self.migration_options["backwards"]
        target_migration = self.migration_options["migration"]
        if last_migration is None:
            state = 0
        elif last_migration[1]:
            state = last_migration[0] - 1
        else:
            state = last_migration[0]
        if target_migration is not None:
            target = target_migration
        elif backwards:
            target = 0
        else:
            target = float("inf")
        collected_migrations = {}
        for file in self.migration_options["migration_dir"].iterdir():
            match = re.match(self.migration_name, file.name)
            if match is None:
                raise ValueError("Migration violates naming scheme")
            backward_migration = match["backwards"] is not None
            if backward_migration ^ backwards:
                continue
            migration_id = int(match["migration_id"])
            if (not backwards and state < migration_id <= target) or (
                backwards and target < migration_id <= state
            ):
                collected_migrations[migration_id] = (file, match["name"], backwards)
        if not backwards and target_migration is None:
            target = max(collected_migrations, default=state)
        if state == target:
            print("Database is in the desired state, leaving...")
            sys.exit(0)
        self._check_migrations(state, target, collected_migrations)
        return collected_migrations

    def _migrate(self):
        fake = self.migration_options["fake"]
        self.cursor.execute(migration_queries.last_migration)
        last_migration = self.cursor.fetchone()
        valid_migrations = self._valid_migrations(last_migration)
        for migration_id, file_path, name, backwards in sorted(
            (key, *value) for key, value in valid_migrations.items()
        ):
            if not self.migration_options["quiet"]:
                if fake and backwards:
                    verb = "Faking removal of"
                elif backwards:
                    verb = "Un-applying"
                elif fake:
                    verb = "Faking"
                else:
                    verb = "Applying"
                print(f"{verb} migration {migration_id}: {name}")
            if not fake:
                self.execute_script(file_path)
            self.cursor.execute(
                migration_queries.write_migration,
                {"migration_id": migration_id, "name": name, "backwards": backwards},
            )
