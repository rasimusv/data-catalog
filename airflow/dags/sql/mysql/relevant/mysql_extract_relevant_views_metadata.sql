SELECT JSON_ARRAYAGG(TABLE_NAME)                                as entity_name_short,
       CONCAT('mysql.', REPLACE((SELECT @@hostname), '.', '-'), '.', TABLE_SCHEMA)                  as parent_urn
FROM information_schema.VIEWS
WHERE TABLE_SCHEMA NOT IN ('mysql', 'information_schema', 'performance_schema', 'sys')
GROUP BY parent_urn;