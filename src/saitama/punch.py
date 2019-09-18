import argparse


def parse_args():
    parser = argparse.ArgumentParser(
        prog="punch",
        description="A utility to manage testing and migrating a database",
    )
    subparsers = parser.add_subparsers(dest="command")

    migration_parser = subparsers.add_parser(
        "migrate", help="Migration runner"
    )

    test_parser = subparsers.add_parser("test", help="Test runner")
    return parser.parse_args()


def main():
    return parse_args()


if __name__ == "__main__":
    main()
