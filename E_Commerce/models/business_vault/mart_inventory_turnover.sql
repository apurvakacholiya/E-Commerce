{{
    config(
        materialized='incremental',
        unique_key='report_date'
    )
}}

WITH active_inventory AS (
    SELECT 
        product_id,
        stock_quantity,
        unit_cost,
        product_updated_at
    FROM {{ ref('inventory_snapshot') }}
    --only look at currently active stock
    WHERE dbt_valid_to IS NULL
),

filtered_inventory AS (
    SELECT * FROM active_inventory
    
    --late-arriving logic with a 48-hour look-back window
    {% if is_incremental() %}
        WHERE product_updated_at >= (
            SELECT DATEADD(hour, -48, MAX(last_inventory_update)) 
            FROM {{ this }}
        )
    {% endif %}
)

--final inventory KPIs
SELECT 
    DATE(product_updated_at) AS report_date,
    COUNT(DISTINCT product_id) AS total_unique_products,
    SUM(stock_quantity) AS total_items_in_stock,
    SUM(stock_quantity * unit_cost) AS total_inventory_value,
    MAX(product_updated_at) AS last_inventory_update
FROM filtered_inventory
GROUP BY DATE(product_updated_at)