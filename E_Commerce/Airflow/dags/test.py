from airflow import DAG
from airflow.providers.amazon.aws.operators.s3 import S3ListOperator
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator # Use this import
from datetime import datetime


with DAG(
    dag_id="test_connections",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["testing"]
) as dag:
    
    # Task 1: Test S3
    # Replace 'your-test-bucket-name' with an actual bucket name you have access to
    test_s3 = S3ListOperator(
        task_id="test_s3_connection",
        aws_conn_id="s3_default",
        bucket="luminates-project" 
    )

    # Task 2: Test Snowflake
    test_snowflake = SQLExecuteQueryOperator(
        task_id="test_snowflake_connection",
        conn_id="snowflake_default",
        sql="SELECT CURRENT_VERSION();"
    )