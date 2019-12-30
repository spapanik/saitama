from saitama import punch


class TestParser:
    @property
    def parser(self):
        return punch.get_parser()

    def test_migration_defaults(self):
        parser = self.parser
        args = parser.parse_args(["migrate"])
        assert args.backwards is False
        assert args.command == "migrate"
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

    def test_test_defaults(self):
        parser = self.parser
        args = parser.parse_args(["test"])
        assert args.command == "test"
        assert args.dbname is None
        assert args.host is None
        assert args.password is None
        assert args.port is None
        assert args.settings is None
        assert args.user is None
