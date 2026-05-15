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

WITH staging AS (
    SELECT
        hash_product_id,
        product_id,
        product_name,
        stock AS stock_quantity,
        unit_cost,
        updated_at AS product_updated_at,
        loaded_at
    FROM {{ ref('stg_inventory') }}
)

SELECT * FROM staging

{% endsnapshot %}