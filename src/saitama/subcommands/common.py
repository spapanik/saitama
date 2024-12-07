from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any

import psycopg

from saitama.lib.conf import Settings

if TYPE_CHECKING:
    import pathlib
    from argparse import Namespace
    from collections.abc import Callable


@dataclass
class DBOptions:
    host: str | None
    port: int | None
    password: str | None
    user: str | None
    dbname: str


class Connection:
    __slots__ = ["_cli_args", "_prepend", "_settings", "cursor", "db_options"]

    def __init__(
        self,
        cli_args: Namespace,
        prepend: str | None = None,
        *,
        testing: bool = False,  # noqa: ARG002
    ) -> None:
        self._cli_args = cli_args
        self._settings = Settings(cli_args)
        self._prepend = prepend
        self.db_options = self._get_db_options()

    def execute_script(self, path: pathlib.Path) -> None:
        with path.open() as file:
            self.cursor.execute(file.read())

    def _run_commands(  # type: ignore[misc]
        self,
        *commands: Callable[[], None],
        get_output: bool = False,
        dbname: str | None = None,
        autocommit: bool = False,
    ) -> list[tuple[Any, ...]] | None:
        db_options = asdict(self.db_options)
        if dbname is not None:
            db_options["dbname"] = dbname

        with psycopg.connect(**db_options) as connection:
            if autocommit:
                connection.autocommit = True
            with connection.cursor() as cursor:
                self.cursor = cursor
                for command in commands:
                    command()
                return self.cursor.fetchall() if get_output else None

    def _get_db_options(self) -> DBOptions:
        cli_args = self._cli_args
        host = cli_args.host or os.environ.get("PGHOST") or self._settings.host
        port = cli_args.port or os.environ.get("PGPORT") or self._settings.port
        user = (
            cli_args.user
            or os.environ.get("PGUSER")
            or os.environ.get("USER")
            or self._settings.user
        )
        password = (
            cli_args.password or os.environ.get("PGPASSWORD") or self._settings.password
        )
        dbname = (
            cli_args.dbname
            or os.environ.get("PGDATABASE")
            or self._settings.dbname
            or user
        )
        if dbname is None:
            msg = "No database specified"
            raise ConnectionError(msg)
        if self._prepend:
            dbname = f"{self._prepend}_{dbname}"

        return DBOptions(
            host=host,
            port=port if port is None else int(port),
            user=user,
            password=password,
            dbname=dbname,
        )
