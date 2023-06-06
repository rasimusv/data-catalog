#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username metadata --dbname datacatalog <<-EOSQL
    CREATE DATABASE airflow;
CREATE USER airflow WITH PASSWORD 'airflow';
GRANT ALL PRIVILEGES ON DATABASE airflow TO airflow;
EOSQL

psql -v ON_ERROR_STOP=1 --username metadata --dbname airflow <<-EOSQL
    GRANT ALL ON SCHEMA public TO airflow;
EOSQL