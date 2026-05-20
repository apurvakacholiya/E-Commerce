{{
    config(
        materialized='incremental',
        unique_key='report_date'  
    )
}}

WITH staged_orders AS (
    SELECT
        customer_id,
        order_amount,
        order_timestamp
    FROM {{ ref('stg_orders') }}
),

enriched_orders AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_timestamp) AS customer_order_seq
    FROM staged_orders
),

filtered_orders AS (
    SELECT * FROM enriched_orders
    {% if is_incremental() %}
        WHERE order_timestamp >= (
            SELECT DATEADD(hour, -48, MAX(last_processed_at)) 
            FROM {{ this }}
        )
    {% endif %}
)

SELECT 
    DATE(order_timestamp) AS report_date,
    ROUND(
        SUM(CASE WHEN customer_order_seq > 1 THEN order_amount ELSE 0 END) / NULLIF(SUM(order_amount), 0), 4
    ) AS repeat_revenue_share,
    MAX(order_timestamp) AS last_processed_at
FROM filtered_orders
GROUP BY DATE(order_timestamp)