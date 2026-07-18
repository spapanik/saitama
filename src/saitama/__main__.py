from saitama.lib.cli import parse_args
from saitama.subcommands.migrate import Migrations
from saitama.subcommands.test import UnitTest


def main() -> None:
    args = parse_args()
    match args:
        case _ if args.migrate_subcommand is not None:
            Migrations(args.common, migrate_args=args.migrate_subcommand).run()
        case _:
            UnitTest(args.common).run()
