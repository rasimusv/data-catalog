SELECT CONCAT(ROUTINE_SCHEMA, '.', ROUTINE_NAME)                                                        as entity_name,
       ROUTINE_NAME                                                                                     as entity_name_short,
       CONCAT('mysql.', REPLACE((SELECT @@hostname), '.', '-'), '.', ROUTINE_SCHEMA, '.', ROUTINE_NAME) as urn,
       CONCAT('mysql.', REPLACE((SELECT @@hostname), '.', '-'), '.', ROUTINE_SCHEMA)                    as parent_urn,
       (SELECT @@hostname)                                                                              as hostname,
       JSON_OBJECT('core_system', 'MySQL',
                   'function_schema', ROUTINE_SCHEMA,
                   'function_name', ROUTINE_NAME,
                   'function_type', ROUTINE_TYPE,
                   'returns', DTD_IDENTIFIER,
                   'function_language', ROUTINE_BODY,
                   'function_code', ROUTINE_DEFINITION,
                   'create_time', CREATED,
                   'update_time', LAST_ALTERED,
                   'function_comment', IF(ROUTINE_COMMENT = '', NULL, ROUTINE_COMMENT))                 as json_data,
       JSON_OBJECT('CORE_SYSTEM', 'MySQL',
                   'RETURNS', DTD_IDENTIFIER,
                   'FUNCTION_LANGUAGE', ROUTINE_BODY,
                   'CREATE_TIME', CREATED,
                   'UPDATE_TIME', LAST_ALTERED)                                                         as json_data_ui,
       IF(ROUTINE_COMMENT = '', NULL, JSON_OBJECT('notifications',
                                                  JSON_ARRAY(JSON_OBJECT('title', 'Function comment',
                                                                         'type', 'info',
                                                                         'body',
                                                                         ROUTINE_COMMENT))))            as notifications,
       JSON_OBJECT('codes',
                   JSON_ARRAY(JSON_OBJECT('code_name', 'Function definition',
                                          'code_language', ROUTINE_BODY,
                                          'highlight', TRUE,
                                          'code_block', ROUTINE_DEFINITION)))                           as codes
FROM information_schema.ROUTINES
WHERE ROUTINE_TYPE = 'FUNCTION'
  and ROUTINE_SCHEMA = '{{ params.schema }}';