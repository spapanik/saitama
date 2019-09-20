db_exists = """
SELECT EXISTS(SELECT 1
                FROM pg_database
               WHERE datname = %(dbname)s);"""
create_db = "CREATE DATABASE {dbname};"
drop_db = "DROP DATABASE {dbname}"
terminate_db = """
SELECT pg_terminate_backend(pg_stat_activity.pid)
  FROM pg_stat_activity
 WHERE pg_stat_activity.datname = %(dbname)s
   AND pid <> pg_backend_pid();"""
create_schema = "CREATE SCHEMA IF NOT EXISTS migration;"
create_table = """
CREATE TABLE IF NOT EXISTS migration.execution (
    id           INT GENERATED ALWAYS AS IDENTITY,
    namespace    TEXT        DEFAULT 'default',
    migration_id INT,
    name         TEXT,
    applied      TIMESTAMPTZ DEFAULT current_timestamp,
    backwards    BOOL        DEFAULT FALSE
);"""
last_migration = """
SELECT migration_id, backwards
  FROM migration.execution
 ORDER BY id DESC;"""
write_migration = """
INSERT
  INTO migration.execution(
       migration_id,
       name,
       backwards)
VALUES (%(migration_id)s,
        %(name)s,
        %(backwards)s)
"""
