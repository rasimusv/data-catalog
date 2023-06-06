INSERT INTO dds.entity (loaded_by_eid, entity_type_etid, entity_name, entity_name_short, urn, parent_eid, info,
                        search_data, json_data, json_data_ui, codes, htmls, links, notifications, tables, tags)
VALUES ((SELECT eid FROM dds.entity WHERE dds.entity.urn = 'datacatalog.airflow.etl.{{ params.exporter_name }}' LIMIT 1),
        (SELECT etid FROM dds.entity_types WHERE entity_type_name = 'instance' LIMIT 1),
        '{{ params.urn }}',
        '{{ params.entity_name }}',
        '{{ params.urn }}',
        NULL,
        'Instance of {{ params.source_name }} {{ params.hostname }}',
        REPLACE('{{ params.urn }}', '.', '   '),
        '{{ params.json_data }}',
        '{{ params.json_data_ui }}',
        NULL, NULL, NULL, NULL,
        '{{ params.tables }}',
        '{"{{ params.source_name }}", "instance", "database"}')
  ON CONFLICT (urn) DO UPDATE SET tables = '{{ params.tables }}' WHERE dds.entity.urn = '{{ params.urn }}';


