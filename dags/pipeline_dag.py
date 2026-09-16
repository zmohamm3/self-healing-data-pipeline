from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

from checks.schema_check import check_schema
from checks.null_check import check_nulls
from checks.outlier_check import check_outliers
from checks.volume_check import check_volume

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'email_on_failure': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'self_healing_pipeline',
    default_args=default_args,
    schedule_interval='@daily',
    catchup=False,
) as dag:

    t_schema = PythonOperator(
        task_id='schema_check',
        python_callable=check_schema,
    )

    t_nulls = PythonOperator(
        task_id='null_check',
        python_callable=check_nulls,
    )

    t_outliers = PythonOperator(
        task_id='outlier_check',
        python_callable=check_outliers,
    )

    t_volume = PythonOperator(
        task_id='volume_check',
        python_callable=check_volume,
    )

    # Pipeline task dependencies
    t_schema >> t_nulls >> t_outliers >> t_volume
