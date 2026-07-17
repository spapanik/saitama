import pathlib
from argparse import Namespace
from unittest import mock

import pytest

from saitama.queries import migration as migration_queries
from saitama.subcommands.migrate import Migration, MigrationArgs, Migrations


def get_args(tmp_path: pathlib.Path, **kwargs: object) -> Namespace:
    values: dict[str, object] = {
        "host": None,
        "port": None,
        "dbname": "saitama",
        "user": None,
        "password": None,
        "settings": str(tmp_path.joinpath("saitama.toml")),
        "drop": False,
        "yes": False,
        "fake": False,
        "backwards": False,
        "migration": None,
    }
    values.update(kwargs)
    return Namespace(**values)


def get_migrations(tmp_path: pathlib.Path, **kwargs: object) -> Migrations:
    return Migrations(get_args(tmp_path, **kwargs))


def test_migration_args(tmp_path: pathlib.Path) -> None:
    migrations = get_migrations(
        tmp_path, drop=True, yes=True, fake=True, backwards=True, migration=2
    )
    assert migrations.migration_options == MigrationArgs(
        drop=True,
        interactive=False,
        fake=True,
        backwards=True,
        migration=2,
        migration_dir=tmp_path.joinpath("migrations"),
        quiet=False,
    )


def test_testing_migration_args(tmp_path: pathlib.Path) -> None:
    migrations = Migrations(get_args(tmp_path), prepend="test", testing=True)
    assert migrations.db_options.dbname == "test_saitama"
    assert migrations.migration_options == MigrationArgs(
        drop=True,
        interactive=False,
        fake=False,
        backwards=False,
        migration=None,
        migration_dir=tmp_path.joinpath("migrations"),
        quiet=True,
    )


def test_run(tmp_path: pathlib.Path) -> None:
    migrations = get_migrations(tmp_path)
    with mock.patch.object(Migrations, "_run_commands") as mock_run_commands:
        migrations.run()
    calls = [
        mock.call(migrations._prepare_db, dbname="template1", autocommit=True),
        mock.call(migrations._create_migration_schema, migrations._migrate),
    ]
    assert mock_run_commands.call_args_list == calls


def test_create_migration_schema(tmp_path: pathlib.Path) -> None:
    migrations = get_migrations(tmp_path)
    migrations.cursor = mock.MagicMock()
    migrations._create_migration_schema()
    calls = [
        mock.call(migration_queries.create_schema),
        mock.call(migration_queries.create_table),
    ]
    assert migrations.cursor.execute.call_args_list == calls


@mock.patch("saitama.subcommands.migrate.SGROutput")
@mock.patch("builtins.input", side_effect=["maybe", "Y"])
def test_confirm_drop(mock_input: mock.MagicMock, mock_output: mock.MagicMock) -> None:
    Migrations._confirm_drop()
    assert mock_input.call_count == 2
    assert mock_output.return_value.print.call_args_list == [mock.call()]


@mock.patch("saitama.subcommands.migrate.SGROutput")
@mock.patch("builtins.input", return_value="n")
def test_cancel_drop(mock_input: mock.MagicMock, mock_output: mock.MagicMock) -> None:
    with pytest.raises(RuntimeError, match="Migrations cancelled by the user"):
        Migrations._confirm_drop()
    assert mock_input.call_args_list == [
        mock.call("Are you sure you want to continue? [y/N] ")
    ]
    assert mock_output.return_value.print.call_args_list == [mock.call()]


def test_prepare_db_missing_response(tmp_path: pathlib.Path) -> None:
    migrations = get_migrations(tmp_path)
    migrations.cursor = mock.MagicMock()
    migrations.cursor.fetchone.return_value = None
    with pytest.raises(RuntimeError, match="Failed to check if db exists"):
        migrations._prepare_db()


@mock.patch("saitama.subcommands.migrate.Migrations._confirm_drop")
def test_prepare_db_interactive_drop(
    mock_confirm: mock.MagicMock, tmp_path: pathlib.Path
) -> None:
    migrations = get_migrations(tmp_path, drop=True)
    migrations.cursor = mock.MagicMock()
    migrations.cursor.fetchone.return_value = (True,)
    migrations._prepare_db()
    assert mock_confirm.call_args_list == [mock.call()]
    assert migrations.cursor.execute.call_count == 4
    assert migrations.cursor.execute.call_args_list[0] == mock.call(
        migration_queries.db_exists, {"dbname": "saitama"}
    )
    assert migrations.cursor.execute.call_args_list[1] == mock.call(
        migration_queries.terminate_db, {"dbname": "saitama"}
    )


@mock.patch("saitama.subcommands.migrate.SGROutput")
def test_prepare_db_non_interactive_drop(
    mock_output: mock.MagicMock, tmp_path: pathlib.Path
) -> None:
    migrations = get_migrations(tmp_path, drop=True, yes=True)
    migrations.cursor = mock.MagicMock()
    migrations.cursor.fetchone.return_value = (True,)
    migrations._prepare_db()
    assert mock_output.return_value.print.call_args_list == [mock.call()]


@mock.patch("saitama.subcommands.migrate.SGROutput")
def test_prepare_db_quiet_drop(
    mock_output: mock.MagicMock, tmp_path: pathlib.Path
) -> None:
    migrations = Migrations(get_args(tmp_path), testing=True)
    migrations.cursor = mock.MagicMock()
    migrations.cursor.fetchone.return_value = (True,)
    migrations._prepare_db()
    assert mock_output.call_count == 0


@mock.patch("saitama.subcommands.migrate.SGRString")
def test_prepare_missing_db(
    mock_string: mock.MagicMock, tmp_path: pathlib.Path
) -> None:
    migrations = get_migrations(tmp_path)
    migrations.cursor = mock.MagicMock()
    migrations.cursor.fetchone.return_value = (False,)
    migrations._prepare_db()
    assert mock_string.call_args_list == [
        mock.call("Database saitama does not exist, creating...")
    ]
    assert migrations.cursor.execute.call_count == 2


def test_prepare_existing_db(tmp_path: pathlib.Path) -> None:
    migrations = get_migrations(tmp_path)
    migrations.cursor = mock.MagicMock()
    migrations.cursor.fetchone.return_value = (True,)
    migrations._prepare_db()
    assert migrations.cursor.execute.call_args_list == [
        mock.call(migration_queries.db_exists, {"dbname": "saitama"})
    ]


@pytest.mark.parametrize(
    ("state", "target", "keys"),
    [
        (0, 2, [2]),
        (0, 2, [1]),
    ],
)
def test_missing_migrations(state: int, target: int, keys: list[int]) -> None:
    collected = {
        key: Migration(path=pathlib.Path(f"{key}.sql"), name=str(key), backwards=False)
        for key in keys
    }
    with pytest.raises(LookupError, match="Missing migrations"):
        Migrations._check_migrations(state, target, collected)


def test_complete_migrations() -> None:
    collected = {
        key: Migration(path=pathlib.Path(f"{key}.sql"), name=str(key), backwards=True)
        for key in [1, 2]
    }
    Migrations._check_migrations(2, 0, collected)


def write_migrations(tmp_path: pathlib.Path) -> pathlib.Path:
    migration_dir = tmp_path.joinpath("migrations")
    migration_dir.mkdir()
    for filename in [
        "1_first.sql",
        "1_backwards_first.sql",
        "2_second.sql",
        "2_backwards_second.sql",
    ]:
        migration_dir.joinpath(filename).touch()
    return migration_dir


def test_valid_forward_migrations(tmp_path: pathlib.Path) -> None:
    migration_dir = write_migrations(tmp_path)
    migrations = get_migrations(tmp_path)
    result = migrations._valid_migrations(None)
    assert result == {
        1: Migration(
            path=migration_dir.joinpath("1_first.sql"),
            name="first",
            backwards=False,
        ),
        2: Migration(
            path=migration_dir.joinpath("2_second.sql"),
            name="second",
            backwards=False,
        ),
    }


def test_valid_backward_migrations(tmp_path: pathlib.Path) -> None:
    migration_dir = write_migrations(tmp_path)
    migrations = get_migrations(tmp_path, backwards=True)
    result = migrations._valid_migrations((2, False))
    assert result == {
        1: Migration(
            path=migration_dir.joinpath("1_backwards_first.sql"),
            name="first",
            backwards=True,
        ),
        2: Migration(
            path=migration_dir.joinpath("2_backwards_second.sql"),
            name="second",
            backwards=True,
        ),
    }


def test_valid_target_migration(tmp_path: pathlib.Path) -> None:
    migration_dir = write_migrations(tmp_path)
    migrations = get_migrations(tmp_path, migration=2)
    result = migrations._valid_migrations((1, False))
    assert result == {
        2: Migration(
            path=migration_dir.joinpath("2_second.sql"),
            name="second",
            backwards=False,
        )
    }


@mock.patch("saitama.subcommands.migrate.SGRString")
def test_database_in_desired_state(
    mock_string: mock.MagicMock, tmp_path: pathlib.Path
) -> None:
    write_migrations(tmp_path)
    migrations = get_migrations(tmp_path, migration=1)
    with pytest.raises(SystemExit) as error:
        migrations._valid_migrations((2, True))
    assert error.value.code == 0
    assert mock_string.return_value.print.call_args_list == [mock.call()]


def test_invalid_migration_name(tmp_path: pathlib.Path) -> None:
    migration_dir = tmp_path.joinpath("migrations")
    migration_dir.mkdir()
    migration_dir.joinpath("invalid.sql").touch()
    migrations = get_migrations(tmp_path)
    with pytest.raises(ValueError, match="Migration violates naming scheme"):
        migrations._valid_migrations(None)


@mock.patch("saitama.subcommands.migrate.SGRString")
def test_migrate(mock_string: mock.MagicMock, tmp_path: pathlib.Path) -> None:
    migrations = get_migrations(tmp_path)
    migrations.cursor = mock.MagicMock()
    migrations.cursor.fetchone.return_value = None
    valid_migrations = {
        2: Migration(path=tmp_path.joinpath("2.sql"), name="second", backwards=True),
        1: Migration(path=tmp_path.joinpath("1.sql"), name="first", backwards=False),
    }
    with (
        mock.patch.object(
            Migrations, "_valid_migrations", return_value=valid_migrations
        ),
        mock.patch.object(Migrations, "execute_script") as mock_execute,
    ):
        migrations._migrate()
    assert mock_string.call_args_list == [
        mock.call("Applying migration 1: first"),
        mock.call("Un-applying migration 2: second"),
    ]
    assert mock_execute.call_args_list == [
        mock.call(tmp_path.joinpath("1.sql")),
        mock.call(tmp_path.joinpath("2.sql")),
    ]
    assert migrations.cursor.execute.call_count == 3


@mock.patch("saitama.subcommands.migrate.SGRString")
def test_fake_migrate(mock_string: mock.MagicMock, tmp_path: pathlib.Path) -> None:
    migrations = get_migrations(tmp_path, fake=True)
    migrations.cursor = mock.MagicMock()
    migrations.cursor.fetchone.return_value = (2, False)
    valid_migrations = {
        1: Migration(path=tmp_path.joinpath("1.sql"), name="first", backwards=True),
        2: Migration(path=tmp_path.joinpath("2.sql"), name="second", backwards=False),
    }
    with (
        mock.patch.object(
            Migrations, "_valid_migrations", return_value=valid_migrations
        ),
        mock.patch.object(Migrations, "execute_script") as mock_execute,
    ):
        migrations._migrate()
    assert mock_string.call_args_list == [
        mock.call("Faking removal of migration 1: first"),
        mock.call("Faking migration 2: second"),
    ]
    assert mock_execute.call_count == 0


@mock.patch("saitama.subcommands.migrate.SGRString")
def test_quiet_migrate(mock_string: mock.MagicMock, tmp_path: pathlib.Path) -> None:
    migrations = Migrations(get_args(tmp_path), testing=True)
    migrations.cursor = mock.MagicMock()
    migrations.cursor.fetchone.return_value = None
    valid_migrations = {
        1: Migration(path=tmp_path.joinpath("1.sql"), name="first", backwards=False),
    }
    with (
        mock.patch.object(
            Migrations, "_valid_migrations", return_value=valid_migrations
        ),
        mock.patch.object(Migrations, "execute_script"),
    ):
        migrations._migrate()
    assert mock_string.call_count == 0
