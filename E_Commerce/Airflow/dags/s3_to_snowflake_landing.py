from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook


AWS_CONN_ID = "s3_default"
SNOWFLAKE_CONN_ID = "snowflake_default"

BUCKET_NAME = "luminates-project"
BASE_FOLDER = "apurva-kacholiya"

DATASETS = {
    "customers": {
        "stage": "ECOMMERCE_RAW.LANDING.S3_CUSTOMERS_STAGE",
        "table": "ECOMMERCE_RAW.LANDING.CUSTOMERS_RAW",
    },
    "orders": {
        "stage": "ECOMMERCE_RAW.LANDING.S3_ORDERS_STAGE",
        "table": "ECOMMERCE_RAW.LANDING.ORDERS_RAW",
    },
    "inventory": {
        "stage": "ECOMMERCE_RAW.LANDING.S3_INVENTORY_STAGE",
        "table": "ECOMMERCE_RAW.LANDING.INVENTORY_RAW",
    },
}


def copy_dataset_to_snowflake(dataset_name: str, stage_name: str, table_name: str):
    hook = SnowflakeHook(snowflake_conn_id=SNOWFLAKE_CONN_ID)

    sql = f"""
    USE WAREHOUSE ECOMMERCE_ELT_WH;

    COPY INTO {table_name}
    (
        FILE_NAME,
        RAW_DATA
    )
    FROM (
        SELECT
            METADATA$FILENAME,
            $1
        FROM @{stage_name}
    )
    FILE_FORMAT = ECOMMERCE_RAW.LANDING.JSON_FILE_FORMAT
    PATTERN = '.*[.]json'
    ON_ERROR = 'CONTINUE';
    """

    hook.run(sql)
    print(f"Loaded {dataset_name} into {table_name}")


default_args = {
    "owner": "apurva_kacholiya",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


with DAG(
    dag_id="s3_to_snowflake_landing_hourly",
    start_date=datetime(2026, 5, 8),
    schedule="@daily",
    catchup=False,
    default_args=default_args,
    tags=["s3", "snowflake", "landing", "json"],
) as dag: 

    for dataset_name, config in DATASETS.items():

        partition_key = (
            f"{BASE_FOLDER}/{dataset_name}/"
            "{{ ds_nodash[:4] }}/{{ ds_nodash[4:6] }}/{{ ds_nodash[6:8] }}/*.json"
        )

        wait_for_file = S3KeySensor(
            task_id=f"wait_for_{dataset_name}_file",
            aws_conn_id=AWS_CONN_ID,
            bucket_name=BUCKET_NAME,
            bucket_key=partition_key,
            wildcard_match=True,
            poke_interval=60,
            timeout=1800,
            mode="reschedule",
        )

        load_to_snowflake = PythonOperator(
            task_id=f"copy_{dataset_name}_to_snowflake",
            python_callable=copy_dataset_to_snowflake,
            op_kwargs={
                "dataset_name": dataset_name,
                "stage_name": config["stage"],
                "table_name": config["table"],
            },
        )

        wait_for_file >> load_to_snowflake

        #Trigger the separate dbt DAG after inventory loads
        if dataset_name == "inventory":
            trigger_snapshot = TriggerDagRunOperator(
                task_id="trigger_inventory_snapshot_dag",
                trigger_dag_id="dbt_inventory_snapshot",
                wait_for_completion=False, # Set to True if you want the landing DAG to wait for dbt to finish
            )
            
            load_to_snowflake >> trigger_snapshot