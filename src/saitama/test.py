import sys

import psycopg2

from .common import execute_script, get_db_options
from .conf import Settings
from .migrate import main as migrate
from .queries import test as test_queries


def _canonical_args(args):
    settings = Settings()

    db_options = get_db_options(args)
    db_options["dbname"] = f"test_{db_options['dbname']}"
    return {
        "db_options": db_options,
        "migration_args": {
            "drop": True,
            "interactive": False,
            "fake": False,
            "backwards": False,
            "migration": None,
            "migrations": settings.migrations,
            "quiet": True,
        },
        "test_args": {"tests": settings.tests},
    }


def _prepare_db(cursor):
    cursor.execute(test_queries.create_test_schema)
    cursor.execute(test_queries.create_test_types)
    cursor.execute(test_queries.create_assertion_table)
    cursor.execute(test_queries.create_assert_function)
    cursor.execute(test_queries.create_result_table)
    cursor.execute(test_queries.create_result_function)


def _collect_tests(cursor, tests_path):
    for file_path in tests_path.iterdir():
        execute_script(cursor, file_path)
    cursor.execute(test_queries.collect_tests)
    return [row[0] for row in cursor.fetchall()]


def _run_single_test(cursor, test_name):
    cursor.execute(test_queries.reset_assertions)
    cursor.execute(test_queries.run_single_test.format(test_name=test_name))
    result = cursor.fetchone()[0]
    cursor.execute(
        test_queries.write_test_result, {"name": test_name, "result": result}
    )


def _run_tests(cursor, test_functions):
    for test_name in test_functions:
        _run_single_test(cursor, test_name)
    cursor.execute(test_queries.test_result)
    return cursor.fetchone()[0]


def main(args):
    args = _canonical_args(args)
    migrate(
        {"db_options": args["db_options"], **args["migration_args"]},
        testing=True,
    )
    with psycopg2.connect(**args["db_options"]) as connection:
        with connection.cursor() as cursor:
            _prepare_db(cursor)
            test_functions = _collect_tests(cursor, args["test_args"]["tests"])
            success = _run_tests(cursor, test_functions)

    if not success:
        print("Tests failed")
        sys.exit(1)
    print("Tests passed")
