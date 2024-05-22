from unittest import mock

from saitama.lib.parser import parse_args


class TestParser:
    @mock.patch("sys.argv", ["punch", "migrate"])
    def test_migration_defaults(self) -> None:
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
    def test_test_defaults(self) -> None:
        args = parse_args()
        assert args.subcommand == "test"
        assert args.dbname is None
        assert args.host is None
        assert args.password is None
        assert args.port is None
        assert args.settings is None
        assert args.user is None
