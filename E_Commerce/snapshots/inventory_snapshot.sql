{% snapshot inventory_snapshot %}

{{
    config(
      target_database='ECOMMERCE_VAULT', 
      target_schema='SNAPSHOTS',       
      unique_key='product_id',
      strategy='check',
      check_cols=['stock_quantity', 'unit_cost']
    )
}}
--using the check_cols strategy, Track changes in stock_quantity or unit_cost

WITH source AS (
    SELECT
        RAW_DATA,
        LOAD_TS
    FROM {{ source('raw', 'inventory_raw') }}
),

parsed AS (
    SELECT
        --unique identifier for the snapshot
        RAW_DATA:product_id::string AS product_id,
        RAW_DATA:product_name::string AS product_name,
        
        TRY_CAST(RAW_DATA:stock_quantity::string AS integer) AS stock_quantity,
        TRY_CAST(RAW_DATA:unit_cost::string AS number(10,2)) AS unit_cost,
        
        LOAD_TS AS loaded_at
    FROM source
)

SELECT * FROM parsed

{% endsnapshot %}