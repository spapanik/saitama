from saitama.lib.parser import parse_args
from saitama.subcommands.migrate import Migrations
from saitama.subcommands.test import UnitTest


def main() -> None:
    args = parse_args()
    if args.subcommand == "migrate":
        Migrations(args).run()
    elif args.subcommand == "test":  # pragma: no branch
        UnitTest(args).run()
