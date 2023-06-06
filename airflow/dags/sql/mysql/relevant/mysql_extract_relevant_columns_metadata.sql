SELECT JSON_ARRAYAGG(COLUMN_NAME)                                                                   as entity_name_short,
       CONCAT('mysql.', REPLACE((SELECT @@hostname), '.', '-'), '.', TABLE_SCHEMA, '.', TABLE_NAME) as parent_urn
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA NOT IN ('mysql', 'information_schema', 'performance_schema', 'sys')
GROUP BY parent_urn;