extensions = """
SELECT ext.extname AS name,
       ext.extversion AS version
  FROM pg_catalog.pg_extension ext
       LEFT JOIN pg_catalog.pg_namespace nsp
       ON nsp.oid = ext.extnamespace
 WHERE nsp.nspname = 'public'
 ORDER BY name;"""
types = """
SELECT pg_catalog.format_type(type.oid, NULL) AS name,
       type.typname                           AS internal_name,
       CASE
           WHEN type.typrelid != 0
               THEN CAST('tuple' AS pg_catalog.TEXT)
           WHEN type.typlen < 0
               THEN CAST('var' AS pg_catalog.TEXT)
           ELSE CAST(type.typlen AS pg_catalog.TEXT)
       END                                    AS size,
       pg_catalog.array_to_string(
               ARRAY(
                       SELECT enm.enumlabel
                         FROM pg_catalog.pg_enum enm
                        WHERE enm.enumtypid = type.oid
                        ORDER BY enm.enumsortorder
                   ),
               E'\n'
           )                                  AS elements
  FROM pg_catalog.pg_type type
       LEFT JOIN pg_catalog.pg_namespace nsp
       ON nsp.oid = type.typnamespace
 WHERE nsp.nspname = 'public'
   AND pg_catalog.pg_type_is_visible(type.oid)
   AND NOT EXISTS(SELECT 1 FROM pg_catalog.pg_type el WHERE el.oid = type.typelem AND el.typarray = type.oid)
   AND (type.typrelid = 0 OR (SELECT cls.relkind = 'c' FROM pg_catalog.pg_class cls WHERE cls.oid = type.typrelid))
 ORDER BY name;"""
functions = """
SELECT  p.proname as name,
  pg_catalog.pg_get_function_result(p.oid) as result_data_type,
  pg_catalog.pg_get_function_arguments(p.oid) as argument_data_types,
 CASE p.prokind
  WHEN 'a' THEN 'agg'
  WHEN 'w' THEN 'window'
  WHEN 'p' THEN 'proc'
  ELSE 'func'
 END as type,
 CASE
  WHEN p.provolatile = 'i' THEN 'immutable'
  WHEN p.provolatile = 's' THEN 'stable'
  WHEN p.provolatile = 'v' THEN 'volatile'
 END as volatility,
 CASE
  WHEN p.proparallel = 'r' THEN 'restricted'
  WHEN p.proparallel = 's' THEN 'safe'
  WHEN p.proparallel = 'u' THEN 'unsafe'
 END as parallel,
 CASE WHEN prosecdef THEN 'definer' ELSE 'invoker' END AS security,
 l.lanname as language,
 p.prosrc as source_code
FROM pg_catalog.pg_proc p
     LEFT JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
     LEFT JOIN pg_catalog.pg_language l ON l.oid = p.prolang
WHERE pg_catalog.pg_function_is_visible(p.oid)
  AND n.nspname = 'public'
ORDER BY name;
"""
