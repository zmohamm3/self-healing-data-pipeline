import os
import csv
from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook

AIRFLOW_HOME = os.environ.get("AIRFLOW_HOME", "/opt/airflow")
DATA_DIR = os.path.join(AIRFLOW_HOME, "data")

default_args = {
    "owner": "airflow",
    "start_date": datetime(2026, 8, 1),
    "retries": 1,
}

def ingest_raw(**context):
    execution_date = context["ds"]
    file_name = f"orders_{execution_date}.csv"
    file_path = os.path.join(DATA_DIR, file_name)

    if not os.path.exists(file_path):
        print(f"File {file_path} not found. Skipping ingestion for date {execution_date}.")
        return

    pg_hook = PostgresHook(postgres_conn_id="postgres_default")
    conn = pg_hook.get_conn()
    cursor = conn.cursor()

    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [
            (
                row.get("order_id"),
                row.get("customer_id"),
                row.get("order_date"),
                row.get("product_category"),
                row.get("quantity"),
                row.get("unit_price"),
                row.get("total_amount"),
                row.get("region"),
                file_name,
            )
            for row in reader
        ]

    insert_sql = """
        INSERT INTO bronze.orders_raw (
            order_id, customer_id, order_date, product_category,
            quantity, unit_price, total_amount, region, source_file
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
    """
    cursor.executemany(insert_sql, rows)
    conn.commit()
    cursor.close()
    conn.close()
    print(f"Successfully ingested {len(rows)} records into bronze.orders_raw.")

def transform_silver(**context):
    execution_date = context["ds"]
    pg_hook = PostgresHook(postgres_conn_id="postgres_default")

    # Cast types, filter invalid NULLs, and dedupe using ON CONFLICT
    silver_sql = f"""
        INSERT INTO silver.orders (
            order_id, customer_id, order_date, product_category,
            quantity, unit_price, total_amount, region
        )
        SELECT DISTINCT ON (order_id)
            order_id,
            customer_id,
            CAST(order_date AS DATE),
            TRIM(product_category),
            CAST(quantity AS INT),
            CAST(unit_price AS NUMERIC(10,2)),
            CAST(total_amount AS NUMERIC(10,2)),
            TRIM(region)
        FROM bronze.orders_raw
        WHERE source_file = 'orders_{execution_date}.csv'
          AND order_id IS NOT NULL
          AND customer_id IS NOT NULL
        ON CONFLICT (order_id) DO NOTHING;
    """
    pg_hook.run(silver_sql)
    print(f"Transformed bronze records for {execution_date} into silver.orders.")

def aggregate_gold(**context):
    execution_date = context["ds"]
    pg_hook = PostgresHook(postgres_conn_id="postgres_default")

    gold_sql = f"""
        INSERT INTO gold.daily_revenue (
            order_date, region, product_category, total_orders, total_revenue
        )
        SELECT 
            order_date,
            region,
            product_category,
            COUNT(order_id) AS total_orders,
            SUM(total_amount) AS total_revenue
        FROM silver.orders
        WHERE order_date = '{execution_date}'
        GROUP BY order_date, region, product_category
        ON CONFLICT (order_date, region, product_category) 
        DO UPDATE SET 
            total_orders = EXCLUDED.total_orders,
            total_revenue = EXCLUDED.total_revenue,
            created_at = CURRENT_TIMESTAMP;
    """
    pg_hook.run(gold_sql)
    print(f"Aggregated silver records for {execution_date} into gold.daily_revenue.")

with DAG(
    dag_id="happy_path_pipeline",
    default_args=default_args,
    schedule_interval="@daily",
    catchup=False,
) as dag:

    t1 = PythonOperator(
        task_id="ingest_raw",
        python_callable=ingest_raw,
    )

    t2 = PythonOperator(
        task_id="transform_silver",
        python_callable=transform_silver,
    )

    t3 = PythonOperator(
        task_id="aggregate_gold",
        python_callable=aggregate_gold,
    )

    t1 >> t2 >> t3
