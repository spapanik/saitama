import argparse

from . import migrate, test


def add_common_args(parser):
    parser.add_argument("-H", "--host", help="The postgres host")
    parser.add_argument("-P", "--port", help="The postgres port")
    parser.add_argument("-d", "--dbname", help="The postgres database")
    parser.add_argument("-u", "--user", help="The postgres user")
    parser.add_argument("-p", "--password", help="The user's password")


def parse_args():
    parser = argparse.ArgumentParser(
        prog="punch", description="A utility to manage testing and migrating a database"
    )
    subparsers = parser.add_subparsers(dest="command")

    migration_parser = subparsers.add_parser("migrate", help="Migration runner")
    migration_parser.add_argument(
        "migration",
        nargs="?",
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

    test_parser = subparsers.add_parser("test", help="Test runner")
    add_common_args(test_parser)
    return parser.parse_args()


def main():
    args = parse_args()
    if args.command == "migrate":
        migrate.main(args)
    if args.command == "test":
        test.main(args)


if __name__ == "__main__":
    main()
