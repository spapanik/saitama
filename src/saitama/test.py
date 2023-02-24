import pathlib
import sys
from argparse import Namespace
from dataclasses import dataclass

from saitama.common import Connection
from saitama.migrate import Migrations
from saitama.queries import test as test_queries


class ANSIEscape:
    __slots__: list[str] = []

    ENDC = "\033[0m"
    FAIL = "\033[31m"
    OKGREEN = "\033[32m"
    OKBLUE = "\033[34m"
    WARNING = "\033[33m"


@dataclass
class TestArgs:
    test_dir: pathlib.Path


class UnitTest(Connection):
    __slots__ = [
        "_settings",
        "_cli_args",
        "_prepend",
        "cursor",
        "db_options",
        "test_options",
    ]

    def __init__(
        self, cli_args: Namespace, prepend: str = "test", *, testing: bool = True
    ):
        super().__init__(cli_args, prepend, testing=testing)
        self.test_options = self._test_args()

    def run(self) -> None:
        Migrations(self._cli_args, prepend=self._prepend, testing=True).run()
        failed_tests = self._run_commands(
            self._prepare_db, self._run_tests, get_output=True
        )
        print("\nTest results:")

        if failed_tests:
            print(
                f"{ANSIEscape.FAIL}The following tests failed:{ANSIEscape.ENDC}",
                end="\n * ",
            )
            print("\n * ".join(test_name for test_name, *_ in failed_tests))
            sys.exit(1)
        print(f"{ANSIEscape.OKGREEN}All tests passed!{ANSIEscape.ENDC}")

    def _test_args(self) -> TestArgs:
        return TestArgs(test_dir=self._settings.tests)

    def _prepare_db(self) -> None:
        self.cursor.execute(test_queries.create_test_schema)
        self.cursor.execute(test_queries.create_test_types)
        self.cursor.execute(test_queries.create_assertion_table)
        self.cursor.execute(test_queries.create_assert_function)
        self.cursor.execute(test_queries.create_result_table)
        self.cursor.execute(test_queries.create_result_function)

    def _run_single_test(self, test_name: str) -> None:
        print(f"Running {test_name}...\t", end="")
        self.cursor.execute(test_queries.reset_assertions)
        self.cursor.execute(test_queries.run_single_test.format(test_name=test_name))
        response = self.cursor.fetchone()
        if response is None:
            raise RuntimeError("Test isn't a valid sql file.")
        result = response[0]
        if result == "pass":
            print(f"{ANSIEscape.OKGREEN}🗸{ANSIEscape.ENDC}")
        else:
            print(f"{ANSIEscape.FAIL}✗{ANSIEscape.ENDC}")
        self.cursor.execute(
            test_queries.write_test_result, {"name": test_name, "result": result}
        )

    def _run_tests(self) -> None:
        for file_path in self.test_options.test_dir.iterdir():
            self.execute_script(file_path)

        self.cursor.execute(test_queries.collect_tests)
        for test_name, *_ in self.cursor.fetchall():
            self._run_single_test(test_name)

        self.cursor.execute(test_queries.test_result)
