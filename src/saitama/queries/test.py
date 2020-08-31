create_test_schema = "CREATE SCHEMA unittest;"
create_test_types = """
CREATE TYPE unittest.test_result
    AS ENUM ('pass', 'fail');"""
create_assertion_table = """
CREATE TABLE IF NOT EXISTS unittest.assertion (
    id     INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    result unittest.test_result
);"""
create_result_table = """
CREATE TABLE IF NOT EXISTS unittest.result (
    id     INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name   TEXT,
    result unittest.test_result
);"""
reset_assertions = "TRUNCATE TABLE unittest.assertion;"
create_assert_function = """
CREATE OR REPLACE FUNCTION unittest.assert(
        expression BOOL,
           message TEXT DEFAULT 'Assertion failed')
    RETURNS VOID
    LANGUAGE plpgsql
AS
$$
BEGIN
    IF expression THEN
        INSERT
          INTO unittest.assertion (result)
        VALUES ('pass'::unittest.test_result);
    ELSE
        RAISE NOTICE '%', message;
        INSERT
          INTO unittest.assertion (result)
        VALUES ('fail'::unittest.test_result);
    END IF;
END
$$;"""
create_result_function = """
CREATE OR REPLACE FUNCTION unittest.result()
    RETURNS unittest.test_result
    LANGUAGE plpgsql
AS
$$
DECLARE
    _success BOOL;
BEGIN
    SELECT NOT EXISTS (
            SELECT 1
              FROM unittest.assertion
             WHERE result='fail')
      INTO _success;

    IF _success THEN
        RETURN ('pass'::unittest.test_result);
    END IF;
    RETURN ('fail'::unittest.test_result);
END
$$;
"""
collect_tests = """
SELECT routine_name
  FROM information_schema.routines
 WHERE routine_type = 'FUNCTION'
   AND routine_schema = 'unittest'
   AND type_udt_name = 'test_result'
   AND routine_name <> 'result';"""
test_result = """
SELECT name
  FROM unittest.result
 WHERE result = 'fail';"""
write_test_result = """
INSERT
  INTO unittest.result (name, result)
VALUES (%(name)s, %(result)s);
"""
run_single_test = "SELECT unittest.{test_name}();"
