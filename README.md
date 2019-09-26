<p align="center">
    <a href="https://github.com/ambv/black">
        <img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg">
    </a>
</p>

# Saitama: A postgres migrations manager and test runner

Saitama offers an easy way to manage migrations and run postgres unittests.

## Installation

The easiest way is to use pip to install saitama.

```bash
pip install --user saitama
```

## Configuration
To configure saitama for your project, you can use any toml file.

```toml
[tool.saitama]
host = <postgres host>
port = <postgres port>
dbname = <postgres database name>
user = <postgres user>
password = <postgres password>
migrations = <path to migrations dir>
tests = <path to tests dir>
```

All of settings are optional, and the default `host`, `port`, `dbname`, `user` and `password` are the ones specified by `psycopg2`, the default migrations directory is `migrations/`, relative to the parent directory of the toml file, and the default test directory is `tests/`, again relative to the toml file.


## Usage
Saitama, once installed offers a single command, `punch`, that controls the migrations and the testing. `punch` follows the GNU recommendations for command line interfaces, and offers:
* `-h` or `--help` to print help, and
* `-V` or `--version` to print the version

### Migrations
You can use punch to migrate forward or backward to a specific migration. The migrations should be named `\d+_.+\.sql`. Backwards are considered all the migrations that the first underscore after the digits is followed by `backwards_`.

```
usage: punch migrate [-h] [-H HOST] [-P PORT] [-d DBNAME] [-u USER]
                     [-p PASSWORD] [-s SETTINGS] [-D] [-f] [-b] [-y]
                     [migration]

positional arguments:
  migration                        The target migration number. If unspecified,
                                   punch will migrate to latest one

optional arguments:
  -h, --help                       Show this help message and exit
  -H HOST, --host HOST             The postgres host
  -P PORT, --port PORT             The postgres port
  -d DBNAME, --dbname DBNAME       The postgres database
  -u USER, --user USER             The postgres user
  -p PASSWORD, --password PASSWORD The user's password
  -s SETTINGS, --settings SETTINGS The path to the settings file
  -D, --drop                       Drop the existing db and create a new one
  -f, --fake                       Fake the migrations up to the specified one
  -b, --backwards                  Backwards migration
  -y, --yes                        Run in non-interactive mode
```

### Test
Testing will create a database named `test_<dbname>`, run all the migrations to this database, run the tests in the test directory, and produce a report. An exit code 1 is returned if any assertion fails.

```
usage: punch test [-h] [-H HOST] [-P PORT] [-d DBNAME] [-u USER] [-p PASSWORD]
                  [-s SETTINGS]

optional arguments:
  -h, --help                       Show this help message and exit
  -H HOST, --host HOST             The postgres host
  -P PORT, --port PORT             The postgres port
  -d DBNAME, --dbname DBNAME       The postgres database
  -u USER, --user USER             The postgres user
  -p PASSWORD, --password PASSWORD The user's password
  -s SETTINGS, --settings SETTINGS The path to the settings file
```

### Writing a migration
In order to write a migration you just have to write an sql file:

```sql
-- /path/to/0001_initial_migration.sql
CREATE TABLE users(
    user_id  INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username TEXT,
    password TEXT
);
```
You can also specify a backwards migration

```sql
-- /path/to/0001_backwards_initial_migration.sql
DROP TABLE users;
```

### Writing a test
In order to write a migration you just have to write an PL/pgSQL function in an sql file which returns the result of `unittest.result();`. You can make assertions by calling `unittest.assert`. The function should be in the `unittest` schema.

```sql
-- /path/to/test_name.sql
CREATE FUNCTION unittest.bar()
     RETURNS unittest.test_result
    LANGUAGE plpgsql
AS
$$
DECLARE
   _cnt INT;
BEGIN
    INSERT
      INTO users (username, password)
    VALUES ('user', 'hashed_and_salted_password');

    SELECT count(*)
      FROM users
      INTO _cnt;

    PERFORM unittest.assert(_cnt <> 0, 'No user was created!');

    RETURN unittest.result();
END
$$;
```
