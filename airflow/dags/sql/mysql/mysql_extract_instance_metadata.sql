SELECT REPLACE((SELECT @@hostname), '.', '-')                       as entity_name,
       CONCAT('mysql.', REPLACE((SELECT @@hostname), '.', '-'))     as urn,
       (SELECT @@hostname)                                          as hostname,
       JSON_OBJECT('core_system', 'MySQL')                          as json_data,
       JSON_OBJECT('CORE_SYSTEM', 'MySQL')                          as json_data_ui,
       JSON_OBJECT('tables',
                   JSON_ARRAY(JSON_OBJECT('table_name', 'Schemas',
                                          'columns', JSON_ARRAY('Schema name'),
                                          'rows', JSON_ARRAYAGG(JSON_ARRAY(SCHEMA_NAME)),
                                          'generate_links', TRUE))) as tables
FROM information_schema.SCHEMATA
WHERE SCHEMA_NAME NOT IN ('mysql', 'information_schema', 'performance_schema', 'sys');