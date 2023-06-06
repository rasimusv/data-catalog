SELECT JSON_ARRAYAGG(ROUTINE_NAME)                                as entity_name_short,
       CONCAT('mysql.', REPLACE((SELECT @@hostname), '.', '-'), '.', ROUTINE_SCHEMA)                    as parent_urn
FROM information_schema.ROUTINES
WHERE ROUTINE_TYPE = 'FUNCTION'
  AND ROUTINE_SCHEMA NOT IN ('mysql', 'information_schema', 'performance_schema', 'sys')
GROUP BY parent_urn;