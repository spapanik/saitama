import os

from .conf import Settings


def execute_script(cursor, path):
    with open(path) as file:
        cursor.execute(file.read())


def get_db_options(args):
    db_options = {}
    settings = Settings()

    host = args.host or os.environ.get("PGHOST") or settings.host
    if host is not None:
        db_options["host"] = host

    port = args.port or os.environ.get("PGPORT") or settings.port
    if port is not None:
        db_options["port"] = port

    user = (
        args.user
        or os.environ.get("PGUSER")
        or os.environ.get("USER")
        or settings.user
    )
    if user is not None:
        db_options["user"] = user

    password = (
        args.password or os.environ.get("PGPASSWORD") or settings.password
    )
    if password is not None:
        db_options["password"] = password

    dbname = (
        args.dbname or os.environ.get("PGDATABASE") or settings.dbname or user
    )
    if dbname is None:
        raise ConnectionError("No database specified")
    db_options["dbname"] = dbname
    return db_options
