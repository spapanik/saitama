from unittest import mock

import pytest

from saitama.lib.cli import parse_args


@mock.patch("sys.argv", ["punch", "migrate"])
def test_migration_defaults() -> None:
    args = parse_args()
    assert args.migrate_subcommand is not None
    assert args.migrate_subcommand.backwards is False
    assert args.migrate_subcommand.drop is False
    assert args.migrate_subcommand.fake is False
    assert args.migrate_subcommand.migration is None
    assert args.migrate_subcommand.yes is False
    assert args.common.dbname is None
    assert args.common.host is None
    assert args.common.password is None
    assert args.common.port is None
    assert args.common.settings is None
    assert args.common.user is None
    assert args.test_subcommand is None


@mock.patch("sys.argv", ["punch", "test"])
def test_test_defaults() -> None:
    args = parse_args()
    assert args.test_subcommand is not None
    assert args.common.dbname is None
    assert args.common.host is None
    assert args.common.password is None
    assert args.common.port is None
    assert args.common.settings is None
    assert args.common.user is None
    assert args.migrate_subcommand is None


@pytest.mark.parametrize("subcommand", ["migrate", "test"])
def test_verbosity(subcommand: str) -> None:
    with mock.patch("sys.argv", ["punch", subcommand]):
        args = parse_args()
        assert args.common.verbosity == 0

    with mock.patch("sys.argv", ["punch", subcommand, "-v"]):
        args = parse_args()
        assert args.common.verbosity == 1

    with mock.patch("sys.argv", ["punch", subcommand, "-vvv"]):
        args = parse_args()
        assert args.common.verbosity == 3
