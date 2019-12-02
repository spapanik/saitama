import os

import psycopg2

from saitama.conf import Settings


class Connection:
    __slots__ = ["_settings", "_cli_args", "_prepend", "cursor", "db_options"]

    def __init__(self, cli_args, prepend=None, **kwargs):
        self._cli_args = cli_args
        self._settings = Settings(cli_args.settings)
        self._prepend = prepend
        self.db_options = self._get_db_options()
        self.cursor = None

    def execute_script(self, path):
        with open(path) as file:
            self.cursor.execute(file.read())

    def _run_commands(self, *commands, get_output=False, dbname=None, autocommit=False):
        if dbname is not None:
            db_options = self.db_options.copy()
            db_options["dbname"] = dbname
        else:
            db_options = self.db_options

        with psycopg2.connect(**db_options) as connection:
            if autocommit:
                connection.autocommit = True
            with connection.cursor() as cursor:
                self.cursor = cursor
                for command in commands:
                    command()
                if get_output:
                    return self.cursor.fetchall()
                return None

    def _get_db_options(self):
        cli_args = self._cli_args
        db_options = {}

        host = cli_args.host or os.environ.get("PGHOST") or self._settings.host
        if host is not None:
            db_options["host"] = host

        port = cli_args.port or os.environ.get("PGPORT") or self._settings.port
        if port is not None:
            db_options["port"] = port

        user = (
            cli_args.user
            or os.environ.get("PGUSER")
            or os.environ.get("USER")
            or self._settings.user
        )
        if user is not None:
            db_options["user"] = user

        password = (
            cli_args.password or os.environ.get("PGPASSWORD") or self._settings.password
        )
        if password is not None:
            db_options["password"] = password

        dbname = (
            cli_args.dbname
            or os.environ.get("PGDATABASE")
            or self._settings.dbname
            or user
        )
        if dbname is None:
            raise ConnectionError("No database specified")
        if self._prepend:
            dbname = f"{self._prepend}_{dbname}"
        db_options["dbname"] = dbname

        return db_options
