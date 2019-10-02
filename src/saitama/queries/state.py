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
