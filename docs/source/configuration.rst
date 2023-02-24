=============
Configuration
=============

To configure saitama for your project, you can use any toml file.

.. code:: toml
    [tool.saitama]
    host = "<postgres host>"
    port = "<postgres port>"
    dbname = "<postgres database name>"
    user = "<postgres user>"
    password = "<postgres password>"
    migrations = "<path to migrations dir>"
    tests = "<path to tests dir>"

All of settings are optional, and the default ``host``, ``port``, ``dbname``, ``user`` and ``password``
are the ones specified by ``psycopg``, the default migrations directory is ``migrations/``,
relative to the parent directory of the toml file,
and the default test directory is ``tests/``, again relative to the toml file.
