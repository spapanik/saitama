import pathlib
from argparse import Namespace
from unittest import mock

import pytest

from saitama.queries import test as test_queries
from saitama.subcommands.test import TestArgs as UnitTestArgs, UnitTest


def get_args(tmp_path: pathlib.Path) -> Namespace:
    return Namespace(
        host=None,
        port=None,
        dbname="saitama",
        user=None,
        password=None,
        settings=str(tmp_path.joinpath("saitama.toml")),
    )


def test_test_args(tmp_path: pathlib.Path) -> None:
    unit_test = UnitTest(get_args(tmp_path))
    assert unit_test.db_options.dbname == "test_saitama"
    assert unit_test.test_options == UnitTestArgs(test_dir=tmp_path.joinpath("tests"))


@mock.patch("saitama.subcommands.test.SGRString")
@mock.patch("saitama.subcommands.test.Migrations")
def test_run_passes(
    mock_migrations: mock.MagicMock,
    mock_string: mock.MagicMock,
    tmp_path: pathlib.Path,
) -> None:
    unit_test = UnitTest(get_args(tmp_path))
    with mock.patch.object(UnitTest, "_run_commands", return_value=[]) as mock_run:
        unit_test.run()
    assert mock_migrations.call_args_list == [
        mock.call(unit_test._cli_args, prepend="test", testing=True)
    ]
    assert mock_migrations.return_value.run.call_args_list == [mock.call()]
    assert mock_run.call_args_list == [
        mock.call(unit_test._prepare_db, unit_test._run_tests, get_output=True)
    ]
    assert mock_string.call_args_list == [
        mock.call("Test results:", prefix="\n", is_error=False),
        mock.call("All tests passed!", params=[mock.ANY]),
    ]


@mock.patch("saitama.subcommands.test.SGRString")
@mock.patch("saitama.subcommands.test.Migrations")
def test_run_fails(
    mock_migrations: mock.MagicMock,
    mock_string: mock.MagicMock,
    tmp_path: pathlib.Path,
) -> None:
    unit_test = UnitTest(get_args(tmp_path))
    with (
        mock.patch.object(
            UnitTest,
            "_run_commands",
            return_value=[("test_one",), ("test_two",)],
        ),
        pytest.raises(SystemExit) as error,
    ):
        unit_test.run()
    assert error.value.code == 1
    assert mock_migrations.return_value.run.call_args_list == [mock.call()]
    assert mock_string.call_args_list == [
        mock.call("Test results:", prefix="\n", is_error=True),
        mock.call("The following tests failed:", params=[mock.ANY], is_error=True),
        mock.call(" * test_one"),
        mock.call(" * test_two"),
    ]


def test_prepare_db(tmp_path: pathlib.Path) -> None:
    unit_test = UnitTest(get_args(tmp_path))
    unit_test.cursor = mock.MagicMock()
    unit_test._prepare_db()
    calls = [
        mock.call(test_queries.create_test_schema),
        mock.call(test_queries.create_test_types),
        mock.call(test_queries.create_assertion_table),
        mock.call(test_queries.create_assert_function),
        mock.call(test_queries.create_result_table),
        mock.call(test_queries.create_result_function),
    ]
    assert unit_test.cursor.execute.call_args_list == calls


@mock.patch("saitama.subcommands.test.SGRString")
def test_single_test_passes(
    mock_string: mock.MagicMock, tmp_path: pathlib.Path
) -> None:
    unit_test = UnitTest(get_args(tmp_path))
    unit_test.cursor = mock.MagicMock()
    unit_test.cursor.fetchone.return_value = ("pass",)
    unit_test._run_single_test("test_example")
    assert mock_string.call_args_list == [
        mock.call("Running test_example...", suffix="\t"),
        mock.call("✓", params=[mock.ANY]),
    ]
    assert unit_test.cursor.execute.call_count == 3
    assert unit_test.cursor.execute.call_args_list[-1] == mock.call(
        test_queries.write_test_result,
        {"name": "test_example", "result": "pass"},
    )


@mock.patch("saitama.subcommands.test.SGRString")
def test_single_test_fails(mock_string: mock.MagicMock, tmp_path: pathlib.Path) -> None:
    unit_test = UnitTest(get_args(tmp_path))
    unit_test.cursor = mock.MagicMock()
    unit_test.cursor.fetchone.return_value = ("fail",)
    unit_test._run_single_test("test_example")
    assert mock_string.call_args_list == [
        mock.call("Running test_example...", suffix="\t"),
        mock.call("✗", params=[mock.ANY]),
    ]


def test_single_test_missing_response(tmp_path: pathlib.Path) -> None:
    unit_test = UnitTest(get_args(tmp_path))
    unit_test.cursor = mock.MagicMock()
    unit_test.cursor.fetchone.return_value = None
    with pytest.raises(RuntimeError, match="Test isn't a valid sql file"):
        unit_test._run_single_test("test_example")


def test_run_tests(tmp_path: pathlib.Path) -> None:
    test_dir = tmp_path.joinpath("tests")
    test_dir.mkdir()
    test_file = test_dir.joinpath("test_example.sql")
    test_file.touch()
    unit_test = UnitTest(get_args(tmp_path))
    unit_test.cursor = mock.MagicMock()
    unit_test.cursor.fetchall.return_value = [("test_one",), ("test_two",)]
    with (
        mock.patch.object(UnitTest, "execute_script") as mock_execute,
        mock.patch.object(UnitTest, "_run_single_test") as mock_run_single,
    ):
        unit_test._run_tests()
    assert mock_execute.call_args_list == [mock.call(test_file)]
    assert mock_run_single.call_args_list == [
        mock.call("test_one"),
        mock.call("test_two"),
    ]
    assert unit_test.cursor.execute.call_args_list == [
        mock.call(test_queries.collect_tests),
        mock.call(test_queries.test_result),
    ]


def test_run_no_tests(tmp_path: pathlib.Path) -> None:
    tmp_path.joinpath("tests").mkdir()
    unit_test = UnitTest(get_args(tmp_path))
    unit_test.cursor = mock.MagicMock()
    unit_test.cursor.fetchall.return_value = []
    with (
        mock.patch.object(UnitTest, "execute_script") as mock_execute,
        mock.patch.object(UnitTest, "_run_single_test") as mock_run_single,
    ):
        unit_test._run_tests()
    assert mock_execute.call_count == 0
    assert mock_run_single.call_count == 0
