#!/usr/bin/env bash
airflow db init
airflow users  create --role Admin --username metadata --email metadata --firstname metadata --lastname metadata --password metadata
airflow webserver
