DELETE FROM dds.entity e
WHERE parent_eid = (SELECT eid FROM dds.entity WHERE e.urn = '{{ params.parent_urn }}' LIMIT 1)
  AND entity_type_etid = (SELECT etid FROM dds.entity_types WHERE entity_type_name = 'database' LIMIT 1)
  AND entity_name_short NOT IN(SELECT * FROM json_array_elements_text('{{ params.array_json }}'));