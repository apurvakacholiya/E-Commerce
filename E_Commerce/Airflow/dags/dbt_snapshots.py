from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "apurva_kacholiya",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="dbt_inventory_snapshot",  # This matches the trigger_dag_id in your landing script
    start_date=datetime(2026, 5, 8),
    schedule=None,  # Scheduled by the TriggerDagRunOperator
    catchup=False,
    default_args=default_args,
    tags=["dbt", "snowflake", "inventory", "snapshot"],
) as dag:

    run_staging = BashOperator(
        task_id='run_stg_inventory',
        bash_command='cd /opt/airflow/dbt_project && dbt run --select stg_inventory --profiles-dir .',
    )

    run_inventory_snapshot = BashOperator(
        task_id="run_dbt_snapshot_inventory",
        # Added --profiles-dir . so dbt knows how to connect to Snowflake
        bash_command="cd /opt/airflow/dbt_project && dbt snapshot --select inventory_snapshot --profiles-dir .",
    )

    # Define the new execution order
    run_staging >> run_inventory_snapshot