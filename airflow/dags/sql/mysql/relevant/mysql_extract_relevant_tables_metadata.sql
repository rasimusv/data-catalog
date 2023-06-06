SELECT JSON_ARRAYAGG(TABLE_NAME)                                                   as entity_name_short,
       CONCAT('mysql.', REPLACE((SELECT @@hostname), '.', '-'), '.', TABLE_SCHEMA) as parent_urn
FROM information_schema.TABLES
WHERE TABLE_TYPE = 'BASE TABLE'
  AND TABLE_SCHEMA NOT IN ('mysql', 'information_schema', 'performance_schema', 'sys')
GROUP BY parent_urn;