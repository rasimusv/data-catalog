CREATE SCHEMA IF NOT EXISTS dds;

SET search_path TO dds;

CREATE EXTENSION IF NOT EXISTS zombodb;

ALTER SYSTEM SET zdb.default_elasticsearch_url = 'http://elasticsearch:9200/';

CREATE TABLE IF NOT EXISTS dds.entity_types
(
    etid                              BIGSERIAL PRIMARY KEY,
    entity_type_name                  VARCHAR UNIQUE,
    entity_type_displayed_name        VARCHAR,
    entity_type_displayed_name_plural VARCHAR
);

CREATE TABLE IF NOT EXISTS dds.entity
(
    eid               BIGSERIAL PRIMARY KEY,
    entity_type_etid  BIGINT REFERENCES dds.entity_types ON DELETE CASCADE ON UPDATE CASCADE NOT NULL,
    parent_eid        BIGINT REFERENCES dds.entity ON DELETE CASCADE ON UPDATE CASCADE,
    loaded_by_eid     BIGINT REFERENCES dds.entity ON DELETE CASCADE ON UPDATE CASCADE,
    processed_ts      TIMESTAMP DEFAULT NOW(),
    urn               VARCHAR UNIQUE                                                         NOT NULL,
    entity_name       VARCHAR                                                                NOT NULL,
    entity_name_short VARCHAR                                                                NOT NULL,
    info              VARCHAR,
    search_data       VARCHAR,
    json_data         jsonb,
    json_data_ui      jsonb,
    codes             jsonb,
    htmls             jsonb,
    links             jsonb,
    notifications     jsonb,
    tables            jsonb,
    tags              varchar[]
);

CREATE TABLE IF NOT EXISTS dds.relation
(
    rid            BIGSERIAL PRIMARY KEY,
    loaded_by_eid  BIGINT REFERENCES dds.entity ON DELETE CASCADE ON UPDATE CASCADE NOT NULL,
    processed_dttm TIMESTAMP DEFAULT NOW(),
    source         BIGINT REFERENCES dds.entity ON DELETE CASCADE ON UPDATE CASCADE,
    destination    BIGINT REFERENCES dds.entity ON DELETE CASCADE ON UPDATE CASCADE,
    attribute      BIGINT REFERENCES dds.entity ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT ur UNIQUE(source, destination, attribute)

);

INSERT INTO dds.entity_types (entity_type_name, entity_type_displayed_name, entity_type_displayed_name_plural)
VALUES ('database', 'База данных', 'Базы данных'),
       ('instance', 'Хост', 'Хосты'),
       ('schema', 'Схема', 'Схемы'),
       ('etl', 'ETL Процесс', 'ETL Процессы'),
       ('table', 'Таблица', 'Таблицы'),
       ('view', 'Представление', 'Представления'),
       ('column', 'Столбец', 'Столбцы'),
       ('procedure', 'Процедура', 'Процедуры'),
       ('function', 'Функция', 'Функции'),
       ('lineage_backend', 'Бэкенд Data Lineage', 'Бэкенды Data Lineage');

INSERT INTO dds.entity (entity_type_etid, parent_eid, loaded_by_eid, urn, entity_name, entity_name_short,
                        info, search_data, json_data, json_data_ui, codes, htmls, links, notifications, tables, tags)
VALUES ((SELECT etid from dds.entity_types WHERE entity_type_name = 'lineage_backend' LIMIT 1),
        NULL,
        NULL,
        'datacatalog.openlineage_backend',
        'datacatalog.openlineage_backend',
        'openlineage_backend',
        'OpenLineage backend for data catalog',
        'data catalog OpenLineage lineage',
        '{"core_system": "OpenLineage"}',
        '{"CORE_SYSTEM": "OpenLineage"}',
        NULL, NULL, NULL, NULL, NULL,
        string_to_array('OpenLineage,Lineage', ',')::varchar[]
        );

CREATE TYPE dds.entity_idx_type AS
(
    eid               BIGINT,
    urn               VARCHAR,
    entity_name       VARCHAR,
    entity_name_short VARCHAR,
    info              VARCHAR,
    search_data       VARCHAR,
    tags              varchar[]
);

CREATE FUNCTION dds.entity_idx_func(dds.entity)
    RETURNS dds.entity_idx_type
    IMMUTABLE STRICT
    LANGUAGE sql AS
$$
SELECT ROW (
           $1.eid::BIGINT,
           $1.urn,
           $1.entity_name,
           $1.entity_name_short,
           $1.info,
           $1.search_data,
           $1.tags
           )::dds.entity_idx_type;
$$;

CREATE INDEX full_text_entity ON dds.entity
    USING zombodb ((dds.entity_idx_func(dds.entity.*)))
    WITH (url='http://elasticsearch:9200/');