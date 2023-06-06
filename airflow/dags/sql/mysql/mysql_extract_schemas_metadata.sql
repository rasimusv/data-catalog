SELECT CONCAT(REPLACE((SELECT @@hostname), '.', '-'), '.', SCHEMA_NAME)           as entity_name,
       SCHEMA_NAME                                                                as entity_name_short,
       CONCAT('mysql.', REPLACE((SELECT @@hostname), '.', '-'), '.', SCHEMA_NAME) as urn,
       CONCAT('mysql.', REPLACE((SELECT @@hostname), '.', '-'))                   as parent_urn,
       (SELECT @@hostname)                                                        as hostname,
       JSON_OBJECT('core_system', 'MySQL')                                        as json_data,
       JSON_OBJECT('CORE_SYSTEM', 'MySQL')                                        as json_data_ui,
       JSON_OBJECT('tables',
                   JSON_ARRAY(JSON_OBJECT('table_name', 'Tables',
                                          'columns', JSON_ARRAY('Table name'),
                                          'rows', (SELECT JSON_ARRAYAGG(JSON_ARRAY(TABLE_NAME))
                                                   FROM information_schema.TABLES
                                                   WHERE TABLE_TYPE = 'BASE TABLE'
                                                     AND TABLE_SCHEMA = SCHEMA_NAME),
                                          'generate_links', TRUE),
                              JSON_OBJECT('table_name', 'Procedures',
                                          'columns', JSON_ARRAY('Procedure name'),
                                          'rows', (SELECT JSON_ARRAYAGG(JSON_ARRAY(ROUTINE_NAME))
                                                   FROM information_schema.ROUTINES
                                                   WHERE ROUTINE_TYPE = 'PROCEDURE'
                                                     AND ROUTINE_SCHEMA = SCHEMA_NAME),
                                          'generate_links', TRUE),
                              JSON_OBJECT('table_name', 'Functions',
                                          'columns', JSON_ARRAY('Function name'),
                                          'rows', (SELECT JSON_ARRAYAGG(JSON_ARRAY(ROUTINE_NAME))
                                                   FROM information_schema.ROUTINES
                                                   WHERE ROUTINE_TYPE = 'FUNCTION'
                                                     AND ROUTINE_SCHEMA = SCHEMA_NAME),
                                          'generate_links', TRUE),
                              JSON_OBJECT('table_name', 'Views',
                                          'columns', JSON_ARRAY('View name'),
                                          'rows', (SELECT JSON_ARRAYAGG(JSON_ARRAY(TABLE_NAME))
                                                   FROM information_schema.VIEWS
                                                   WHERE TABLE_SCHEMA = SCHEMA_NAME),
                                          'generate_links',
                                          TRUE)))                                 as tables
FROM information_schema.SCHEMATA
WHERE SCHEMA_NAME NOT IN ('mysql', 'information_schema', 'performance_schema', 'sys');