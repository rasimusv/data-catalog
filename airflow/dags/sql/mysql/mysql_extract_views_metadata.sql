SELECT CONCAT(TABLE_SCHEMA, '.', TABLE_NAME)                                                        as entity_name,
       TABLE_NAME                                                                                   as entity_name_short,
       CONCAT('mysql.', REPLACE((SELECT @@hostname), '.', '-'), '.', TABLE_SCHEMA, '.', TABLE_NAME) as urn,
       CONCAT('mysql.', REPLACE((SELECT @@hostname), '.', '-'), '.', TABLE_SCHEMA)                  as parent_urn,
       (SELECT @@hostname)                                                                          as hostname,
       JSON_OBJECT('core_system', 'MySQL',
                   'view_schema', TABLE_SCHEMA,
                   'view_name', TABLE_NAME,
                   'view_definition', VIEW_DEFINITION,
                   'is_updatable', IS_UPDATABLE)                                                    as json_data,
       JSON_OBJECT('CORE_SYSTEM', 'MySQL',
                   'IS_UPDATABLE', IS_UPDATABLE)                                                    as json_data_ui,
       JSON_OBJECT('codes',
                   JSON_ARRAY(JSON_OBJECT('code_name', 'View definition',
                                          'code_language', 'SQL',
                                          'highlight', TRUE,
                                          'code_block', VIEW_DEFINITION)))                          as codes,
       JSON_OBJECT('tables',
                   JSON_ARRAY(JSON_OBJECT('table_name', 'Columns',
                                          'columns', JSON_ARRAY('Ordinal position', 'Column name', 'Column type',
                                                                'NOT NULL', 'Column default value'),
                                          'rows', (SELECT JSON_ARRAYAGG(JSON_ARRAY(ORDINAL_POSITION,
                                                                                   COLUMN_NAME,
                                                                                   COLUMN_TYPE,
                                                                                   IF(IS_NULLABLE = 'YES', FALSE, TRUE),
                                                                                   COLUMN_DEFAULT))
                                                   FROM information_schema.COLUMNS
                                                   WHERE TABLE_NAME = VIEWS.TABLE_NAME
                                                     AND TABLE_SCHEMA = VIEWS.TABLE_SCHEMA),
                                          'generate_links', TRUE)))                                 as tables
FROM information_schema.VIEWS
WHERE TABLE_SCHEMA = '{{ params.schema }}';