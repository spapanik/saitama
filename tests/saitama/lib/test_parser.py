from unittest import mock

import pytest

from saitama.lib.parser import parse_args


@mock.patch("sys.argv", ["punch", "migrate"])
def test_migration_defaults() -> None:
    args = parse_args()
    assert args.backwards is False
    assert args.subcommand == "migrate"
    assert args.dbname is None
    assert args.drop is False
    assert args.fake is False
    assert args.host is None
    assert args.migration is None
    assert args.password is None
    assert args.port is None
    assert args.settings is None
    assert args.user is None
    assert args.yes is False


@mock.patch("sys.argv", ["punch", "test"])
def test_test_defaults() -> None:
    args = parse_args()
    assert args.subcommand == "test"
    assert args.dbname is None
    assert args.host is None
    assert args.password is None
    assert args.port is None
    assert args.settings is None
    assert args.user is None


@pytest.mark.parametrize("subcommand", ["migrate", "test"])
def test_verbosity(subcommand: str) -> None:
    with mock.patch("sys.argv", ["punch", subcommand]):
        args = parse_args()
        assert args.verbosity == 0

    with mock.patch("sys.argv", ["punch", subcommand, "-v"]):
        args = parse_args()
        assert args.verbosity == 1

    with mock.patch("sys.argv", ["punch", subcommand, "-vvv"]):
        args = parse_args()
        assert args.verbosity == 3
