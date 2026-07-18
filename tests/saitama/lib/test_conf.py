from __future__ import annotations

import pathlib
from typing import TYPE_CHECKING

from saitama.lib.conf import Settings

if TYPE_CHECKING:
    import pytest

    from tests.helpers.type_defs import StrFactory


def test_default_settings(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("SAITAMA_SETTINGS", raising=False)
    settings = Settings()
    assert settings.host is None
    assert settings.port is None
    assert settings.dbname is None
    assert settings.user is None
    assert settings.password is None
    assert settings.migrations == pathlib.Path("migrations")
    assert settings.tests == pathlib.Path("tests")
    assert repr(settings) == "default settings"


def test_configured_settings(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    test_password: StrFactory,
) -> None:
    password = test_password()
    settings_path = tmp_path.joinpath("saitama.toml")
    settings_path.write_text(
        f"""
[tool.saitama]
host = "localhost"
port = 5432
dbname = "saitama"
user = "postgres"
password = "{password}"
migrations = "sql/migrations"
tests = "sql/tests"
"""
    )
    monkeypatch.setenv("SAITAMA_SETTINGS", str(settings_path))
    settings = Settings()
    assert settings.host == "localhost"
    assert settings.port == 5432
    assert settings.dbname == "saitama"
    assert settings.user == "postgres"
    assert settings.password == password
    assert settings.migrations == tmp_path.joinpath("sql/migrations")
    assert settings.tests == tmp_path.joinpath("sql/tests")
    assert repr(settings) == f"settings@{settings_path}"


def test_absolute_paths(tmp_path: pathlib.Path) -> None:
    settings_path = tmp_path.joinpath("saitama.toml")
    migrations = tmp_path.joinpath("migrations")
    tests = tmp_path.joinpath("tests")
    settings_path.write_text(
        f"""
[tool.saitama]
migrations = "{migrations.as_posix()}"
tests = "{tests.as_posix()}"
"""
    )
    settings = Settings(str(settings_path))
    assert settings.migrations == migrations
    assert settings.tests == tests
