import sys
from argparse import ArgumentParser, Namespace

from saitama.__version__ import __version__

sys.tracebacklimit = 0


def add_common_args(parser: ArgumentParser) -> None:
    parser.add_argument("-H", "--host", help="The postgres host")
    parser.add_argument("-P", "--port", help="The postgres port")
    parser.add_argument("-d", "--dbname", help="The postgres database")
    parser.add_argument("-u", "--user", help="The postgres user")
    parser.add_argument("-p", "--password", help="The user's password")
    parser.add_argument("-s", "--settings", help="The path to the settings file")


def parse_args() -> Namespace:
    parser = ArgumentParser(
        prog="punch", description="A utility to manage testing and migrating a database"
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="print the version and exit",
    )

    parent_parser = ArgumentParser(add_help=False)
    parent_parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        dest="verbosity",
        help="increase the level of verbosity",
    )

    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    migration_parser = subparsers.add_parser(
        "migrate", parents=[parent_parser], help="Migration runner"
    )
    migration_parser.add_argument(
        "migration",
        nargs="?",
        type=int,
        help="The target migration number. If unspecified, will migrate to latest one",
    )
    add_common_args(migration_parser)
    migration_parser.add_argument(
        "-D",
        "--drop",
        action="store_true",
        help="Drop the existing db and create a new one",
    )
    migration_parser.add_argument(
        "-f",
        "--fake",
        action="store_true",
        help="Fake the migrations up to the specified one",
    )
    migration_parser.add_argument(
        "-b", "--backwards", action="store_true", help="Backwards migration"
    )
    migration_parser.add_argument(
        "-y", "--yes", action="store_true", help="Run in non-interactive mode"
    )

    test_parser = subparsers.add_parser(
        "test", parents=[parent_parser], help="Test runner"
    )
    add_common_args(test_parser)

    args = parser.parse_args()
    if args.verbosity > 0:
        sys.tracebacklimit = 1000

    return args
