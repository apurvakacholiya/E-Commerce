# E-Commerce Data Warehouse

A modern data warehouse built on **Data Vault 2.0** architecture for e-commerce analytics, combining dbt transformation, Snowflake data warehousing, and Apache Airflow orchestration (via Snowflake SPCs with compute pools).

---

## 📋 Overview

This project implements a 3-layer analytics platform:

- **Staging Layer**: Raw data parsing and type casting
- **Raw Vault Layer**: Data Vault 2.0 hub-link-satellite pattern with change data capture
- **Business Vault Layer**: Analytics-ready dimensions, marts, and KPIs (customers, orders, inventory)

**Key Features**: SCD Type 2 tracking, incremental processing, late-arriving data handling, automated orchestration

---

## 🛠️ Tech Stack

- **Data Warehouse**: Snowflake
- **Transform Engine**: dbt 1.0+
- **Orchestration**: Apache Airflow (via Snowflake SPCs + Compute Pools)
- **Cloud Storage**: AWS S3
- **Data Generation**: Python Faker
- **Packages**: dbt-utils, automate_dv (Data Vault 2.0)

---

## 🚀 Quick Start

### 1. Setup Environment

```bash
git clone <repository-url>
cd E_Commerce

python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

pip install -r requirements.txt
```

### 2. Configure Snowflake

Update `profiles.yml` with your Snowflake connection details.

### 3. Run dbt

```bash
dbt debug       # Validate connection
dbt deps        # Install packages
dbt run         # Run all models
dbt test        # Run tests
```

### 4. Trigger Airflow

Airflow DAGs are orchestrated via Snowflake SPCs with compute pools. Trigger DAGs from Snowflake:

```sql
-- Trigger data generation
CALL SYSTEM$EXECUTE_JOB('s3_daily_batch_generator');

-- Trigger S3 to Snowflake load
CALL SYSTEM$EXECUTE_JOB('s3_to_snowflake_landing_hourly');

-- Run dbt snapshots
CALL SYSTEM$EXECUTE_JOB('dbt_inventory_snapshot');
```

---

## 📂 Project Structure

```
E_Commerce/
├── models/
│   ├── staging/              # Parse JSON, type casting, hashing
│   ├── raw_vault/            # Data Vault 2.0 (hubs, links, satellites)
│   └── business_vault/       # Dimensions, marts, KPIs
├── snapshots/               # SCD Type 2 tracking
├── tests/                   # dbt & Python tests
├── macros/                  # dbt custom functions
├── Airflow/                 # Airflow DAGs (deployed to SPCs)
├── scripts/                 # Utility scripts
├── dbt_project.yml          # dbt config
├── packages.yml             # dbt dependencies
└── README.md
```

---

## 📊 Available DAGs

| DAG | Purpose |
|-----|---------|
| `s3_daily_batch_generator` | Generate synthetic data to S3 |
| `s3_to_snowflake_landing_hourly` | Load S3 data to Snowflake landing |
| `dbt_inventory_snapshot` | Run inventory SCD Type 2 snapshots |

---

## 🎮 Usage

```bash
# Run all models
dbt run

# Run specific layer
dbt run --select staging
dbt run --select raw_vault
dbt run --select business_vault

# Run tests
dbt test

# Run snapshots (SCD Type 2)
dbt snapshot

# Generate documentation
dbt docs generate
dbt docs serve
```

---

## 📈 Data Models

**Staging**: stg_customers, stg_orders, stg_inventory (views)

**Raw Vault**: 
- Hubs: hub_customer, hub_order
- Links: link_order_customer
- Satellites: sat_customer_details, sat_order_details

**Business Vault**: 
- dim_customer (SCD Type 2)
- mart_daily_revenue
- mart_inventory_turnover
- KPIs: repeat_purchase_share, repurchase_cycle, revenue_realization

---

## 🧪 Testing

```bash
# Run dbt tests
dbt test

# Run Python tests
python -m pytest tests/ -v
```

---

## 🤖 AI Integration

The project includes Snowflake Cortex AI integration for SQL debugging via `dbt_agent.py`.

---

## 🤝 Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Commit changes: `git commit -m "Add your feature"`
3. Push and open a Pull Request

---

## 📚 Resources

- [dbt Docs](https://docs.getdbt.com/)
- [Data Vault 2.0](https://www.datavault.info/)
- [Snowflake Docs](https://docs.snowflake.com/)
- [automate_dv](https://github.com/Datavault-UK/automate_dv)

---

