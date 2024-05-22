from saitama.lib.parser import parse_args
from saitama.migrate import Migrations
from saitama.test import UnitTest


def main() -> None:
    args = parse_args()
    if args.command == "migrate":
        Migrations(args).run()
    elif args.command == "test":
        UnitTest(args).run()
