from __future__ import annotations

import os
import pathlib
from typing import TYPE_CHECKING

from dj_settings import ConfigParser

if TYPE_CHECKING:
    from argparse import Namespace


class Settings:
    def __init__(self, args: Namespace) -> None:
        pathname = (
            args.settings or os.environ.get("SAITAMA_SETTINGS") or "./saitama.toml"
        )
        self.path = pathlib.Path(pathname)
        settings = {}
        if self.path.exists():
            data = ConfigParser([self.path]).data
            settings = data.get("tool", {}).get("saitama", {})
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

    def __repr__(self) -> str:
        return f"settings@{self.path}" if self.path.exists() else "default settings"
