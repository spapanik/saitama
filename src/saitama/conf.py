import os
import pathlib

import toml


class Settings:
    def __init__(self, path=None):
        if path is None:
            self.path = os.environ.get("SAITAMA_SETTINGS")
        else:
            self.path = path
        if self.path is not None:
            self.path = pathlib.Path(self.path).absolute()
            data = toml.load(self.path)
            settings = data.get("tool", {}).get("saitama", {})
        else:
            self.path = pathlib.Path(".").absolute()
            settings = {}
        self.host = settings.get("host")
        self.port = settings.get("port")
        self.dbname = settings.get("dbname")
        self.user = settings.get("user")
        self.password = settings.get("password")
        self.migrations = pathlib.Path(settings.get("migrations", "migrations"))
        if not self.migrations.is_absolute():
            self.migrations = self.path.parent.joinpath(self.migrations)
        self.tests = pathlib.Path(settings.get("tests", "tests"))
        if not self.tests.is_absolute():
            self.tests = self.path.parent.joinpath(self.tests)

    def __repr__(self):
        if self.path is None:
            return "default settings"

        return f"settings@{self.path}"
