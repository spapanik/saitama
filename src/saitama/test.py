import sys

import pastel

from .common import Connection
from .migrate import Migrations
from .queries import test as test_queries


class UnitTest(Connection):
    __slots__ = [
        "_settings",
        "_cli_args",
        "_prepend",
        "cursor",
        "db_options",
        "test_options",
    ]

    def __init__(self, cli_args, prepend="test", **kwargs):
        super().__init__(cli_args, prepend, **kwargs)
        self.test_options = self._test_args()

    def run(self):
        Migrations(self._cli_args, prepend=self._prepend, testing=True).run()
        failed_tests = self._run_commands(
            self._prepare_db, self._run_tests, get_output=True
        )
        print("\nTest results:")

        if failed_tests:
            print(
                pastel.colorize("<fg=red>The following tests failed:</>"), end="\n * "
            )
            print("\n * ".join(test_name for test_name, *_ in failed_tests))
            sys.exit(1)
        print(pastel.colorize("<fg=green>All tests passed!</>"))

    def _test_args(self):
        return {"test_dir": self._settings.tests}

    def _prepare_db(self):
        self.cursor.execute(test_queries.create_test_schema)
        self.cursor.execute(test_queries.create_test_types)
        self.cursor.execute(test_queries.create_assertion_table)
        self.cursor.execute(test_queries.create_assert_function)
        self.cursor.execute(test_queries.create_result_table)
        self.cursor.execute(test_queries.create_result_function)

    def _run_single_test(self, test_name):
        print(f"Running {test_name}...\t", end="")
        self.cursor.execute(test_queries.reset_assertions)
        self.cursor.execute(test_queries.run_single_test.format(test_name=test_name))
        result = self.cursor.fetchone()[0]
        if result == "pass":
            print(pastel.colorize("<fg=green>🗸</>"))
        else:
            print(pastel.colorize("<fg=red>✗</>"))
        self.cursor.execute(
            test_queries.write_test_result, {"name": test_name, "result": result}
        )

    def _run_tests(self):
        for file_path in self.test_options["test_dir"].iterdir():
            self.execute_script(file_path)

        self.cursor.execute(test_queries.collect_tests)
        for test_name, *_ in self.cursor.fetchall():
            self._run_single_test(test_name)

        self.cursor.execute(test_queries.test_result)
