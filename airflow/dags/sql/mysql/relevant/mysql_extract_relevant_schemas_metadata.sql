SELECT JSON_ARRAYAGG(SCHEMA_NAME)                               as entity_name_short,
       CONCAT('mysql.', REPLACE((SELECT @@hostname), '.', '-')) as parent_urn
FROM information_schema.SCHEMATA
WHERE SCHEMA_NAME NOT IN ('mysql', 'information_schema', 'performance_schema', 'sys')
GROUP BY parent_urn;