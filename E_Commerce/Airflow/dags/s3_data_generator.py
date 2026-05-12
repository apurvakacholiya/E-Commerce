import json
import random
from datetime import datetime, timedelta

from airflow.decorators import dag, task
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from faker import Faker

# Configuration
AWS_CONN_ID = "s3_default"
BUCKET_NAME = "luminates-project"
BASE_FOLDER = "apurva-kacholiya"  # Your requested folder name
TOTAL_ROWS = 10000            # 10k rows daily

fake = Faker()

# ---------- UTILITIES ---------- #
def get_late_timestamp(base_date):
    """30% chance of being 1-3 days late."""
    if random.random() < 0.3:
        delay = random.randint(1, 3)
        return (base_date - timedelta(days=delay)).isoformat()
    return base_date.isoformat()

# ---------- DAG DEFINITION ---------- #
@dag(
    dag_id="s3_daily_batch_generator",
    start_date=datetime(2026, 4, 15),
    schedule="@daily",  # Changed to Daily
    catchup=False,
    default_args={
        "owner": "airflow",
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
    },
    tags=["apurva_kacholiya", "large_batch"],
)
def s3_data_generator():

    @task
    def generate_and_upload_data(**context):
        hook = S3Hook(aws_conn_id=AWS_CONN_ID)
        
        # Use logical_date for consistent daily folder partitioning
        execution_date = context["logical_date"]
        path_suffix = execution_date.strftime("%Y/%m/%d")
        
        # Batch generation logic
        def upload_batch(data_type, generator_func):
            # Generate 10k rows in memory
            batch_data = [generator_func(execution_date) for _ in range(TOTAL_ROWS)]
            
            # Final path: apurva-kacholiya/orders/2026/04/30/data_uniqueid.json
            file_name = f"batch_{fake.uuid4()}.json"
            key = f"{BASE_FOLDER}/{data_type}/{path_suffix}/{file_name}"
            
            # Upload the entire list as one JSON file
            hook.load_string(
                string_data=json.dumps(batch_data),
                key=key,
                bucket_name=BUCKET_NAME,
                replace=True
            )
            print(f"Uploaded {TOTAL_ROWS} rows to: s3://{BUCKET_NAME}/{key}")

        # Record Generators
        def gen_customer(ts):
            return {
                "customer_id": fake.uuid4(),
                "name": fake.name(),
                "email": fake.email(),
                "created_at": get_late_timestamp(ts)
            }

        def gen_order(ts):
            return {
                "order_id": fake.uuid4(),
                "customer_id": fake.uuid4(),
                "amount": round(random.uniform(10, 5000), 2),
                "status": random.choice(["placed", "shipped", "delivered"]),
                "order_time": get_late_timestamp(ts)
            }

        def gen_inventory(ts):
            return {
                "product_id": fake.uuid4(),
                "product_name": fake.word(),
                "stock": random.randint(0, 100),
                "updated_at": get_late_timestamp(ts)
            }

        # Run uploads for each table
        upload_batch("customers", gen_customer)
        upload_batch("orders", gen_order)
        upload_batch("inventory", gen_inventory)

    generate_and_upload_data()

s3_data_generator()