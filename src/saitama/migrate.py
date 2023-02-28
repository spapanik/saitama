from __future__ import annotations

import pathlib
import re
import sys
from argparse import Namespace
from dataclasses import dataclass

from psycopg import sql

from saitama.common import Connection
from saitama.queries import migration as migration_queries


@dataclass
class MigrationArgs:
    drop: bool
    interactive: bool
    fake: bool
    backwards: bool
    migration: int | None
    migration_dir: pathlib.Path
    quiet: bool


@dataclass
class Migration:
    path: pathlib.Path
    name: str
    backwards: bool


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

    def __init__(
        self, cli_args: Namespace, prepend: str | None = None, *, testing: bool = False
    ):
        super().__init__(cli_args, prepend, testing=testing)
        self.migration_options = self._migration_args(cli_args, testing=testing)

    def run(self) -> None:
        self._run_commands(self._prepare_db, dbname="template1", autocommit=True)
        self._run_commands(self._create_migration_schema, self._migrate)

    def _migration_args(
        self, args: Namespace, *, testing: bool = False
    ) -> MigrationArgs:
        migrations_dir = self._settings.migrations
        if testing:
            return MigrationArgs(
                drop=True,
                interactive=False,
                fake=False,
                backwards=False,
                migration=None,
                migration_dir=migrations_dir,
                quiet=True,
            )

        return MigrationArgs(
            drop=args.drop,
            interactive=not args.yes,
            fake=args.fake,
            backwards=args.backwards,
            migration=args.migration,
            migration_dir=migrations_dir,
            quiet=False,
        )

    def _create_migration_schema(self) -> None:
        self.cursor.execute(migration_queries.create_schema)
        self.cursor.execute(migration_queries.create_table)

    @staticmethod
    def _confirm_drop() -> None:
        print("WARNING: All data in the existing database will be lost!")
        while True:
            raw_confirmation = input("Are you sure you want to continue? [y/N] ")
            if raw_confirmation.lower() in ["y", "yes"]:
                confirmation = True
                break
            if raw_confirmation.lower() in ["n", "no", ""]:
                confirmation = False
                break
        if not confirmation:
            raise RuntimeError("Migrations cancelled by the user")

    def _prepare_db(self) -> None:
        dbname = self.db_options.dbname
        drop = self.migration_options.drop
        quiet = self.migration_options.quiet

        self.cursor.execute(migration_queries.db_exists, {"dbname": dbname})
        response = self.cursor.fetchone()
        if response is None:
            raise RuntimeError("Failed to check if db exists.")
        exists = response[0]
        if exists and drop:
            if self.migration_options.interactive:
                self._confirm_drop()
            elif not quiet:
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
    def _check_migrations(
        state: float, target: float, collected_migrations: dict[int, Migration]
    ) -> None:
        if state > target:
            state, target = target, state
        keys = sorted(collected_migrations.keys())
        start = keys[0]
        end = keys[-1]
        if start != state + 1 or end != target or end - start + 1 != target - state:
            raise LookupError("Missing migrations")

    def _valid_migrations(
        self, last_migration: tuple[int, bool] | None
    ) -> dict[int, Migration]:
        backwards = self.migration_options.backwards
        target_migration = self.migration_options.migration
        if last_migration is None:
            state = 0
        elif last_migration[1]:
            state = last_migration[0] - 1
        else:
            state = last_migration[0]
        if target_migration is not None:
            target: float = target_migration
        elif backwards:
            target = 0
        else:
            target = float("inf")
        collected_migrations = {}
        for file in self.migration_options.migration_dir.iterdir():
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
                collected_migrations[migration_id] = Migration(
                    path=file, name=match["name"], backwards=backwards
                )
        if not backwards and target_migration is None:
            target = max(collected_migrations, default=state)
        if state == target:
            print("Database is in the desired state, leaving...")
            sys.exit(0)
        self._check_migrations(state, target, collected_migrations)
        return collected_migrations

    def _migrate(self) -> None:
        fake = self.migration_options.fake
        self.cursor.execute(migration_queries.last_migration)
        last_migration = self.cursor.fetchone()
        valid_migrations = self._valid_migrations(last_migration)
        for migration_id, migration in sorted(
            (key, value) for key, value in valid_migrations.items()
        ):
            if not self.migration_options.quiet:
                if fake and migration.backwards:
                    verb = "Faking removal of"
                elif migration.backwards:
                    verb = "Un-applying"
                elif fake:
                    verb = "Faking"
                else:
                    verb = "Applying"
                print(f"{verb} migration {migration_id}: {migration.name}")
            if not fake:
                self.execute_script(migration.path)
            self.cursor.execute(
                migration_queries.write_migration,
                {
                    "migration_id": migration_id,
                    "name": migration.name,
                    "backwards": migration.backwards,
                },
            )
