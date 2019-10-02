extensions = """
SELECT ext.extname AS name,
       ext.extversion AS version
  FROM pg_catalog.pg_extension ext
       LEFT JOIN pg_catalog.pg_namespace nsp
       ON nsp.oid = ext.extnamespace
 WHERE nsp.nspname = 'public'
 ORDER BY name;"""
