import re
import sys

import psycopg2
from psycopg2 import sql

from .common import execute_script, get_db_options
from .conf import Settings
from .queries import migration as migration_queries

MIGRATION_NAME = re.compile(
    r"(?P<migration_id>\d+)_(?P<backwards>backwards_)?(?P<name>.+).sql"
)


def _canonical_args(args):
    settings = Settings()

    return {
        "db_options": get_db_options(args),
        "drop": args.drop,
        "interactive": not args.yes,
        "fake": args.fake,
        "backwards": args.backwards,
        "migration": args.migration,
        "migrations": settings.migrations,
    }


def _create_migration_schema(cursor):
    cursor.execute(migration_queries.create_schema)
    cursor.execute(migration_queries.create_table)


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


def _check_migrations(state, target, collected_migrations):
    if state > target:
        state, target = target, state
    keys = sorted(collected_migrations.keys())
    start = keys[0]
    end = keys[-1]
    if (
        start != state + 1
        or end != target
        or end - start + 1 != target - state
    ):
        raise LookupError("Missing migrations")


def _valid_migrations(
    last_migration, target_migration, migration_dir, backwards
):
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
    for file in migration_dir.iterdir():
        match = re.match(MIGRATION_NAME, file.name)
        if match is None:
            raise ValueError("Migration violates naming scheme")
        backward_migration = match["backwards"] is not None
        if backward_migration ^ backwards:
            continue
        migration_id = int(match["migration_id"])
        if (not backwards and state < migration_id <= target) or (
            backwards and target < migration_id <= state
        ):
            collected_migrations[migration_id] = (
                file,
                match["name"],
                backwards,
            )
    if not backwards and target_migration is None:
        target = max(collected_migrations, default=state)
    if state == target:
        print("Database is in the desired state, leaving...")
        sys.exit(0)
    _check_migrations(state, target, collected_migrations)
    return collected_migrations


def prepare_db(cursor, dbname, *, drop=False, interactive=True):
    cursor.execute(migration_queries.db_exists, {"dbname": dbname})
    exists = cursor.fetchone()[0]
    if exists and drop:
        if interactive:
            _confirm_drop()
        else:
            print("WARNING: All data in the existing database will be lost!")
        cursor.execute(migration_queries.terminate_db, {"dbname": dbname})
        cursor.execute(migration_queries.drop_db.format(dbname=dbname))
    if not exists or drop:
        if not exists:
            print(f"Database {dbname} does not exist, creating...")
        cursor.execute(
            sql.SQL(migration_queries.create_db.format(dbname=dbname))
        )
        return


def migrate(
    cursor, migrations, target_migration, *, backwards=False, fake=False
):
    cursor.execute(migration_queries.last_migration)
    last_migration = cursor.fetchone()
    valid_migrations = _valid_migrations(
        last_migration, target_migration, migrations, backwards
    )
    for migration_id, file_path, name, backwards in sorted(
        (key, *value) for key, value in valid_migrations.items()
    ):
        if fake:
            print(f"Faking migration {migration_id}: {name}")
        else:
            print(f"Applying migration {migration_id}: {name}")
            execute_script(cursor, file_path)
        cursor.execute(
            migration_queries.write_migration,
            {
                "migration_id": migration_id,
                "name": name,
                "backwards": backwards,
            },
        )


def main(args):
    args = _canonical_args(args)
    db_options = args["db_options"]
    template_db_options = db_options.copy()
    template_db_options["dbname"] = "template1"
    with psycopg2.connect(**template_db_options) as connection:
        connection.autocommit = True
        with connection.cursor() as cursor:
            prepare_db(
                cursor,
                db_options["dbname"],
                drop=args["drop"],
                interactive=args["interactive"],
            )

    with psycopg2.connect(args) as connection:
        with connection.cursor() as cursor:
            _create_migration_schema(cursor)
            migrate(
                cursor,
                args["migrations"],
                args["migration"],
                backwards=args["backwards"],
                fake=args["fake"],
            )
