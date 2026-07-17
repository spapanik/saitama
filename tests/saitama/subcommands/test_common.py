from __future__ import annotations

from argparse import Namespace
from typing import TYPE_CHECKING
from unittest import mock

import pytest

from saitama.subcommands.common import Connection, DBOptions

if TYPE_CHECKING:
    import pathlib

    from tests.helpers.type_defs import StrFactory


def get_args(**kwargs: object) -> Namespace:
    values: dict[str, object] = {
        "host": None,
        "port": None,
        "dbname": None,
        "user": None,
        "password": None,
        "settings": None,
    }
    values.update(kwargs)
    return Namespace(**values)


@mock.patch("saitama.subcommands.common.Settings")
def test_db_options_from_args(
    mock_settings: mock.MagicMock, test_password: StrFactory
) -> None:
    settings_password = test_password()
    args_password = test_password()
    mock_settings.return_value = mock.MagicMock(
        host="settings-host",
        port=1111,
        dbname="settings-db",
        user="settings-user",
        password=settings_password,
    )
    args = get_args(
        host="args-host",
        port="5432",
        dbname="args-db",
        user="args-user",
        password=args_password,
    )
    connection = Connection(args, prepend="test")
    assert connection.db_options == DBOptions(
        host="args-host",
        port=5432,
        dbname="test_args-db",
        user="args-user",
        password=args_password,
    )


@mock.patch("saitama.subcommands.common.Settings")
def test_db_options_from_environment(
    mock_settings: mock.MagicMock,
    monkeypatch: pytest.MonkeyPatch,
    test_password: StrFactory,
) -> None:
    password = test_password()
    mock_settings.return_value = mock.MagicMock(
        host=None, port=None, dbname=None, user=None, password=None
    )
    monkeypatch.setenv("PGHOST", "environment-host")
    monkeypatch.setenv("PGPORT", "5433")
    monkeypatch.setenv("PGDATABASE", "environment-db")
    monkeypatch.setenv("PGUSER", "environment-user")
    monkeypatch.setenv("PGPASSWORD", password)
    connection = Connection(get_args())
    assert connection.db_options == DBOptions(
        host="environment-host",
        port=5433,
        dbname="environment-db",
        user="environment-user",
        password=password,
    )


@mock.patch("saitama.subcommands.common.Settings")
def test_db_options_from_settings(
    mock_settings: mock.MagicMock, test_password: StrFactory
) -> None:
    password = test_password()
    mock_settings.return_value = mock.MagicMock(
        host="settings-host",
        port=None,
        dbname=None,
        user="settings-user",
        password=password,
    )
    with mock.patch.dict("os.environ", {}, clear=True):
        connection = Connection(get_args())
    assert connection.db_options == DBOptions(
        host="settings-host",
        port=None,
        dbname="settings-user",
        user="settings-user",
        password=password,
    )


@mock.patch("saitama.subcommands.common.Settings")
def test_missing_database(mock_settings: mock.MagicMock) -> None:
    mock_settings.return_value = mock.MagicMock(
        host=None, port=None, dbname=None, user=None, password=None
    )
    with (
        mock.patch.dict("os.environ", {}, clear=True),
        pytest.raises(ConnectionError, match="No database specified"),
    ):
        Connection(get_args())


@mock.patch("saitama.subcommands.common.Settings")
def test_execute_script(mock_settings: mock.MagicMock, tmp_path: pathlib.Path) -> None:
    mock_settings.return_value = mock.MagicMock(
        host=None, port=None, dbname="saitama", user=None, password=None
    )
    path = tmp_path.joinpath("script.sql")
    path.write_text("SELECT 1;")
    connection = Connection(get_args())
    connection.cursor = mock.MagicMock()
    connection.execute_script(path)
    calls = [mock.call("SELECT 1;")]
    assert connection.cursor.execute.call_args_list == calls


@mock.patch("saitama.subcommands.common.psycopg.connect")
@mock.patch("saitama.subcommands.common.Settings")
def test_run_commands(
    mock_settings: mock.MagicMock,
    mock_connect: mock.MagicMock,
    test_password: StrFactory,
) -> None:
    password = test_password()
    mock_settings.return_value = mock.MagicMock(
        host="host", port=5432, dbname="saitama", user="user", password=password
    )
    cursor = mock.MagicMock()
    cursor.fetchall.return_value = [("result",)]
    connection_context = mock_connect.return_value.__enter__.return_value
    connection_context.cursor.return_value.__enter__.return_value = cursor
    connection = Connection(get_args(user="user"))
    command = mock.MagicMock()
    result = connection._run_commands(
        command, get_output=True, dbname="template1", autocommit=True
    )
    assert result == [("result",)]
    calls = [
        mock.call(
            host="host",
            port=5432,
            password=password,
            user="user",
            dbname="template1",
        )
    ]
    assert mock_connect.call_args_list == calls
    assert mock_connect.return_value.__enter__.return_value.autocommit is True
    assert command.call_args_list == [mock.call()]
    assert cursor.fetchall.call_args_list == [mock.call()]


@mock.patch("saitama.subcommands.common.psycopg.connect")
@mock.patch("saitama.subcommands.common.Settings")
def test_run_commands_defaults(
    mock_settings: mock.MagicMock, mock_connect: mock.MagicMock
) -> None:
    mock_settings.return_value = mock.MagicMock(
        host=None, port=None, dbname="saitama", user=None, password=None
    )
    connection = Connection(get_args())
    result = connection._run_commands()
    assert result is None
    assert mock_connect.return_value.__enter__.return_value.autocommit is not True
