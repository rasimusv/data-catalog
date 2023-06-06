import json
from time import sleep

from airflow import DAG, XComArg
from airflow.decorators import task
from airflow.hooks.base import BaseHook
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.mysql.operators.mysql import MySqlOperator
from datetime import datetime, timedelta
from airflow.lineage.entities import Table

# TODO refactor all SQL files, make dag independent from SQL query structure, update schema
# Default settings applied to all tasks
default_args = {
    'owner': 'metadata',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1)
}

postgres_conn_id = 'postgres_metadata_registry'
pg_conn_type = BaseHook.get_connection(postgres_conn_id).conn_type
pg_host = BaseHook.get_connection(postgres_conn_id).host
pg_port = str(BaseHook.get_connection(postgres_conn_id).port)
pg_database = BaseHook.get_connection(postgres_conn_id).schema
pg_cluster = pg_conn_type + '://' + pg_host + ':' + pg_port
datacatalog_dds_entity = Table(database=pg_database, cluster=pg_cluster, name='dds.entity', )

# Instantiate DAG
with DAG('mysql-metadata-exporter',
         start_date=datetime(2023, 5, 20),
         max_active_runs=3,
         schedule_interval='0 * * * *',
         default_args=default_args,
         catchup=False,
         template_searchpath='/opt/airflow/cert'  # path to look for external files
         ) as dag:
    @task(trigger_rule="all_done")
    def airflow_bug_workaround_sleep_task():
        """
        Airflow has a bug which is skipping all task after a chain of mapped tasks ('***_task[]')
        This task is usually placed in the middle of chain, to workaround bug
        More about this bug: https://github.com/apache/airflow/issues/25200
        """
        sleep(1)


    @task
    def transform_relevant_entities(relevant_entities):
        """Transform metadata about relevant entities to make it loadable"""
        return {
            'array_json': relevant_entities[0],
            'parent_urn': relevant_entities[1]
        }


    # Load metadata about exporter to metadata registry
    load_mysql_exporter_metadata = PostgresOperator(
        task_id='init_mysql_exporter_metadata',
        postgres_conn_id=postgres_conn_id,
        sql="sql/metadata_registry/load/mr_load_exporter_metadata.sql",
        params={'source_name': 'MySQL', 'exporter_name': dag.dag_id})

    connection_ids = json.loads(open(file='dags/MySQLExporter/mysql_connections.json').read())['Airflow connection ids']

    extract_instance_metadata_tasks = []
    for conn_id in connection_ids:
        mysql_conn_type = BaseHook.get_connection(conn_id).conn_type
        mysql_host = BaseHook.get_connection(conn_id).host
        mysql_port = str(BaseHook.get_connection(conn_id).port)

        mysql_database = 'information_schema'
        mysql_cluster = mysql_conn_type + '://' + mysql_host + ':' + mysql_port

        schemata = Table(database=mysql_database, cluster=mysql_cluster, name='SCHEMATA', )
        columns = Table(database=mysql_database, cluster=mysql_cluster, name='COLUMNS', )
        routines = Table(database=mysql_database, cluster=mysql_cluster, name='ROUTINES', )
        tables = Table(database=mysql_database, cluster=mysql_cluster, name='TABLES', )
        views = Table(database=mysql_database, cluster=mysql_cluster, name='VIEWS', )

        # ------------------------------------INSTANCES-----------------------------------

        # Extract metadata about instance
        extract_instance_metadata_task = MySqlOperator(task_id=f'extract_instance_metadata_task_{conn_id}',
                                                       mysql_conn_id=conn_id,
                                                       sql="sql/mysql/mysql_extract_instance_metadata.sql")

        extract_instance_metadata_tasks.append(extract_instance_metadata_task)


        @task(task_id=f'transform_each_instance_task_{conn_id}', inlets=[schemata], outlets=[datacatalog_dds_entity])
        def transform_each_instance(instance):
            """Transform metadata about instance to make it loadable"""
            return {'urn': instance[1],
                    'entity_name': instance[0],
                    'hostname': instance[2],
                    'json_data': instance[3],
                    'json_data_ui': instance[4],
                    'tables': instance[5],
                    'source_name': 'MySQL',
                    'exporter_name': dag.dag_id
                    }


        # Load metadata about instance to metadata registry
        load_each_instance_task = PostgresOperator.partial(task_id=f'load_each_instance_task_{conn_id}',
                                                           postgres_conn_id=postgres_conn_id,
                                                           sql="sql/metadata_registry/load/mr_load_instance_metadata.sql").expand(
            params=transform_each_instance.expand(instance=XComArg(extract_instance_metadata_task)))

        # ------------------------------------END OF INSTANCES-----------------------------------

        # ------------------------------------SCHEMAS-----------------------------------

        # Extract metadata about schema
        extract_schema_metadata_task = MySqlOperator(task_id=f'extract_schema_metadata_task_{conn_id}',
                                                     mysql_conn_id=conn_id,
                                                     sql="sql/mysql/mysql_extract_schemas_metadata.sql")


        @task(task_id=f'transform_each_schema_task_{conn_id}', inlets=[schemata], outlets=[datacatalog_dds_entity])
        def transform_each_schema(schema):
            """Transform metadata about schema to make it loadable"""
            return {
                'entity_name': schema[0],
                'entity_name_short': schema[1],
                'urn': schema[2],
                'parent_urn': schema[3],
                'hostname': schema[4],
                'json_data': schema[5],
                'json_data_ui': schema[6],
                'tables': schema[7],
                'source_name': 'MySQL',
                'exporter_name': dag.dag_id
            }


        # Load metadata about schema to metadata registry
        load_each_schema_task = PostgresOperator.partial(task_id=f'load_each_schema_task_{conn_id}',
                                                         postgres_conn_id=postgres_conn_id,
                                                         sql="sql/metadata_registry/load/mr_load_database_metadata.sql").expand(
            params=transform_each_schema.expand(schema=XComArg(extract_schema_metadata_task)))

        # Extract metadata about relevant schemas on instance
        extract_relevant_schemas_metadata_task = MySqlOperator(
            task_id=f'extract_relevant_schemas_metadata_task_{conn_id}',
            mysql_conn_id=conn_id,
            sql="sql/mysql/relevant/mysql_extract_relevant_schemas_metadata.sql")

        # Delete irrelevant schemas from metadata registry
        delete_irrelevant_schemas_task = PostgresOperator.partial(task_id=f'delete_irrelevant_schemas_task_{conn_id}',
                                                                  postgres_conn_id=postgres_conn_id,
                                                                  sql="sql/metadata_registry/delete/mr_delete_databases_metadata.sql").expand(
            params=transform_relevant_entities.expand(
                relevant_entities=XComArg(extract_relevant_schemas_metadata_task)))

        # ------------------------------------END OF SCHEMAS-----------------------------------

        # ------------------------------------TABLES-----------------------------------

        # Extract metadata about tables
        extract_tables_metadata_task = MySqlOperator(task_id=f'extract_tables_metadata_task_{conn_id}',
                                                     mysql_conn_id=conn_id,
                                                     sql="sql/mysql/mysql_extract_tables_metadata.sql",
                                                     params={'schema': BaseHook.get_connection(conn_id).schema})


        @task(task_id=f'transform_each_table_task_{conn_id}', inlets=[tables], outlets=[datacatalog_dds_entity])
        def transform_each_table(table):
            """Transform metadata about table to make it loadable"""
            return {'entity_name': table[0],
                    'entity_name_short': table[1],
                    'urn': table[2],
                    'parent_urn': table[3],
                    'hostname': table[4],
                    'json_data': table[5],
                    'json_data_ui': table[6],
                    'notifications': '{"None": "None"}' if table[7] is None else table[7],
                    'tables': table[8],
                    'source_name': 'MySQL',
                    'exporter_name': dag.dag_id
                    }


        # Load metadata about tables to metadata registry
        load_each_table_task = PostgresOperator.partial(task_id=f'load_each_table_task_{conn_id}',
                                                        postgres_conn_id=postgres_conn_id,
                                                        sql="sql/metadata_registry/load/mr_load_table_metadata.sql").expand(
            params=transform_each_table.expand(table=XComArg(extract_tables_metadata_task)))

        # Extract metadata about relevant tables on instance
        extract_relevant_tables_metadata_task = MySqlOperator(
            task_id=f'extract_relevant_tables_metadata_task_{conn_id}',
            mysql_conn_id=conn_id,
            sql="sql/mysql/relevant/mysql_extract_relevant_tables_metadata.sql")

        # Delete irrelevant tables from metadata registry
        delete_irrelevant_tables_task = PostgresOperator.partial(task_id=f'delete_irrelevant_tables_task_{conn_id}',
                                                                 postgres_conn_id=postgres_conn_id,
                                                                 sql="sql/metadata_registry/delete/mr_delete_tables_metadata.sql").expand(
            params=transform_relevant_entities.expand(
                relevant_entities=XComArg(extract_relevant_tables_metadata_task)))

        # ------------------------------------END OF TABLES-----------------------------------

        # ------------------------------------VIEWS-----------------------------------

        # Extract metadata about views
        extract_views_metadata_task = MySqlOperator(task_id=f'extract_views_metadata_task_{conn_id}',
                                                    mysql_conn_id=conn_id,
                                                    sql="sql/mysql/mysql_extract_views_metadata.sql",
                                                    params={'schema': BaseHook.get_connection(conn_id).schema})


        @task(task_id=f'transform_each_view_task_{conn_id}', inlets=[views], outlets=[datacatalog_dds_entity])
        def transform_each_view(view):
            """Transform metadata about view to make it loadable"""
            return {'entity_name': view[0],
                    'entity_name_short': view[1],
                    'urn': view[2],
                    'parent_urn': view[3],
                    'hostname': view[4],
                    'json_data': view[5],
                    'json_data_ui': view[6],
                    'codes': view[7],
                    'tables': view[8],
                    'source_name': 'MySQL',
                    'exporter_name': dag.dag_id
                    }


        # Load metadata about views to metadata registry
        load_each_view_task = PostgresOperator.partial(task_id=f'load_each_view_task_{conn_id}',
                                                       postgres_conn_id=postgres_conn_id,
                                                       sql="sql/metadata_registry/load/mr_load_view_metadata.sql").expand(
            params=transform_each_view.expand(view=XComArg(extract_views_metadata_task)))

        # Extract metadata about relevant views on instance
        extract_relevant_views_metadata_task = MySqlOperator(
            task_id=f'extract_relevant_views_metadata_task_{conn_id}',
            mysql_conn_id=conn_id,
            sql="sql/mysql/relevant/mysql_extract_relevant_views_metadata.sql")

        # Delete irrelevant views from metadata registry
        delete_irrelevant_views_task = PostgresOperator.partial(task_id=f'delete_irrelevant_views_task_{conn_id}',
                                                                postgres_conn_id=postgres_conn_id,
                                                                sql="sql/metadata_registry/delete/mr_delete_views_metadata.sql").expand(
            params=transform_relevant_entities.expand(
                relevant_entities=XComArg(extract_relevant_views_metadata_task)))

        # ------------------------------------END OF VIEWS-----------------------------------

        # ------------------------------------COLUMNS-----------------------------------

        # Extract metadata about columns
        extract_columns_metadata_task = MySqlOperator(task_id=f'extract_columns_metadata_task_{conn_id}',
                                                      mysql_conn_id=conn_id,
                                                      sql="sql/mysql/mysql_extract_columns_metadata.sql",
                                                      params={'schema': BaseHook.get_connection(conn_id).schema})


        @task(task_id=f'transform_each_column_task_{conn_id}', inlets=[columns], outlets=[datacatalog_dds_entity])
        def transform_each_column(column):
            """Transform metadata about column to make it loadable"""
            return {'entity_name': column[0],
                    'entity_name_short': column[1],
                    'urn': column[2],
                    'parent_urn': column[3],
                    'parent_table_full_name': column[4],
                    'json_data': column[5],
                    'json_data_ui': column[6],
                    'notifications': '{"None": "None"}' if column[7] is None else column[7],
                    'source_name': 'MySQL',
                    'exporter_name': dag.dag_id
                    }


        # Load metadata about columns to metadata registry
        load_each_column_task = PostgresOperator.partial(task_id=f'load_each_column_task_{conn_id}',
                                                         postgres_conn_id=postgres_conn_id,
                                                         sql="sql/metadata_registry/load/mr_load_column_metadata.sql").expand(
            params=transform_each_column.expand(column=XComArg(extract_columns_metadata_task)))

        # Extract metadata about relevant columns on instance
        extract_relevant_columns_metadata_task = MySqlOperator(
            task_id=f'extract_relevant_columns_metadata_task_{conn_id}',
            mysql_conn_id=conn_id,
            sql="sql/mysql/relevant/mysql_extract_relevant_columns_metadata.sql")

        # Delete irrelevant columns from metadata registry
        delete_irrelevant_columns_task = PostgresOperator.partial(task_id=f'delete_irrelevant_columns_task_{conn_id}',
                                                                  postgres_conn_id=postgres_conn_id,
                                                                  sql="sql/metadata_registry/delete/mr_delete_columns_metadata.sql").expand(
            params=transform_relevant_entities.expand(
                relevant_entities=XComArg(extract_relevant_columns_metadata_task)))

        # ------------------------------------END OF COLUMNS-----------------------------------

        # ------------------------------------FUNCTIONS-----------------------------------

        # Extract metadata about functions
        extract_functions_metadata_task = MySqlOperator(task_id=f'extract_functions_metadata_task_{conn_id}',
                                                        mysql_conn_id=conn_id,
                                                        sql="sql/mysql/mysql_extract_functions_metadata.sql",
                                                        params={'schema': BaseHook.get_connection(conn_id).schema})


        @task(task_id=f'transform_each_function_task_{conn_id}', inlets=[routines], outlets=[datacatalog_dds_entity])
        def transform_each_function(function):
            """Transform metadata about function to make it loadable"""
            return {'entity_name': function[0],
                    'entity_name_short': function[1],
                    'urn': function[2],
                    'parent_urn': function[3],
                    'hostname': function[4],
                    'json_data': function[5],
                    'json_data_ui': function[6],
                    'notifications': '{"None": "None"}' if function[7] is None else function[7],
                    'codes': function[8],
                    'source_name': 'MySQL',
                    'exporter_name': dag.dag_id
                    }


        # Load metadata about functions to metadata registry
        load_each_function_task = PostgresOperator.partial(task_id=f'load_each_function_task_{conn_id}',
                                                           postgres_conn_id=postgres_conn_id,
                                                           sql="sql/metadata_registry/load/mr_load_function_metadata.sql").expand(
            params=transform_each_function.expand(function=XComArg(extract_functions_metadata_task)))

        # Extract metadata about relevant functions on instance
        extract_relevant_functions_metadata_task = MySqlOperator(
            task_id=f'extract_relevant_functions_metadata_task_{conn_id}',
            mysql_conn_id=conn_id,
            sql="sql/mysql/relevant/mysql_extract_relevant_functions_metadata.sql")

        # Delete irrelevant functions from metadata registry
        delete_irrelevant_functions_task = PostgresOperator.partial(
            task_id=f'delete_irrelevant_functions_task_{conn_id}',
            postgres_conn_id=postgres_conn_id,
            sql="sql/metadata_registry/delete/mr_delete_functions_metadata.sql").expand(
            params=transform_relevant_entities.expand(
                relevant_entities=XComArg(extract_relevant_functions_metadata_task)))

        # ------------------------------------END OF FUNCTIONS-----------------------------------

        # ------------------------------------PROCEDURES-----------------------------------

        # Extract metadata about procedures
        extract_procedures_metadata_task = MySqlOperator(task_id=f'extract_procedures_metadata_task_{conn_id}',
                                                         mysql_conn_id=conn_id,
                                                         sql="sql/mysql/mysql_extract_procedures_metadata.sql",
                                                         params={'schema': BaseHook.get_connection(conn_id).schema})


        @task(task_id=f'transform_each_procedure_task_{conn_id}', inlets=[routines], outlets=[datacatalog_dds_entity])
        def transform_each_procedure(procedure):
            """Transform metadata about procedure to make it loadable"""
            return {'entity_name': procedure[0],
                    'entity_name_short': procedure[1],
                    'urn': procedure[2],
                    'parent_urn': procedure[3],
                    'hostname': procedure[4],
                    'json_data': procedure[5],
                    'json_data_ui': procedure[6],
                    'notifications': '{"None": "None"}' if procedure[7] is None else procedure[7],
                    'codes': procedure[8],
                    'source_name': 'MySQL',
                    'exporter_name': dag.dag_id
                    }


        # Load metadata about procedures to metadata registry
        load_each_procedure_task = PostgresOperator.partial(task_id=f'load_each_procedure_task_{conn_id}',
                                                            postgres_conn_id=postgres_conn_id,
                                                            sql="sql/metadata_registry/load/mr_load_procedure_metadata.sql").expand(
            params=transform_each_procedure.expand(procedure=XComArg(extract_procedures_metadata_task)))

        # Extract metadata about relevant procedures on instance
        extract_relevant_procedures_metadata_task = MySqlOperator(
            task_id=f'extract_relevant_procedures_metadata_task_{conn_id}',
            mysql_conn_id=conn_id,
            sql="sql/mysql/relevant/mysql_extract_relevant_procedures_metadata.sql")

        # Delete irrelevant procedures from metadata registry
        delete_irrelevant_procedures_task = PostgresOperator.partial(
            task_id=f'delete_irrelevant_procedures_task_{conn_id}',
            postgres_conn_id=postgres_conn_id,
            sql="sql/metadata_registry/delete/mr_delete_procedures_metadata.sql").expand(
            params=transform_relevant_entities.expand(
                relevant_entities=XComArg(extract_relevant_procedures_metadata_task)))

        # ------------------------------------END OF PROCEDURES-----------------------------------

        # ------------------------------------DAG ORCHESTRATION-----------------------------------

        load_each_instance_task >> extract_schema_metadata_task
        load_each_schema_task >> airflow_bug_workaround_sleep_task() >> extract_relevant_schemas_metadata_task
        delete_irrelevant_schemas_task >> extract_tables_metadata_task
        load_each_table_task >> airflow_bug_workaround_sleep_task() >> extract_relevant_tables_metadata_task
        delete_irrelevant_schemas_task >> extract_views_metadata_task
        load_each_view_task >> airflow_bug_workaround_sleep_task() >> extract_relevant_views_metadata_task
        [delete_irrelevant_views_task,
         delete_irrelevant_tables_task] >> airflow_bug_workaround_sleep_task() >> extract_columns_metadata_task
        load_each_column_task >> airflow_bug_workaround_sleep_task() >> extract_relevant_columns_metadata_task
        delete_irrelevant_schemas_task >> extract_functions_metadata_task
        load_each_function_task >> airflow_bug_workaround_sleep_task() >> extract_relevant_functions_metadata_task
        delete_irrelevant_schemas_task >> extract_procedures_metadata_task
        load_each_procedure_task >> airflow_bug_workaround_sleep_task() >> extract_relevant_procedures_metadata_task

load_mysql_exporter_metadata >> extract_instance_metadata_tasks
