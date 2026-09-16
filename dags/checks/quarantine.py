import json
import psycopg2
from datetime import datetime

def route_to_quarantine(record_id, pipeline_name, check_failed, error_details, raw_data):
    """
    Inserts failed records into the quarantine.failed_records Postgres table.
    """
    conn = psycopg2.connect(
        dbname="airflow",      # Changed from 'postgres' to 'airflow'
        user="airflow",        # Changed from 'postgres' to 'airflow'
        password="airflow",    # Changed from 'postgres_password' to 'airflow'
        host="postgres",
        port="5432"
    )
    cursor = conn.cursor()
    
    insert_query = """
        INSERT INTO quarantine.failed_records 
        (record_id, pipeline_name, check_failed, error_details, raw_data, quarantined_at)
        VALUES (%s, %s, %s, %s, %s, %s);
    """
    
    cursor.execute(insert_query, (
        record_id,
        pipeline_name,
        check_failed,
        error_details,
        json.dumps(raw_data),
        datetime.now()
    ))
    
    conn.commit()
    cursor.close()
    conn.close()
    print(f"Record {record_id} successfully routed to quarantine due to: {check_failed}")
