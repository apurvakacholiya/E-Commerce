{{
    config(
        materialized='incremental',
        unique_key='report_date'  
    )
}}

WITH staged_orders AS (
    SELECT
        customer_id,
        order_timestamp
    FROM {{ ref('stg_orders') }}
),

enriched_orders AS (
    SELECT 
        *,
        LAG(order_timestamp) OVER (PARTITION BY customer_id ORDER BY order_timestamp) AS previous_order_timestamp
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
        AVG(DATEDIFF(day, previous_order_timestamp, order_timestamp)), 2
    ) AS avg_days_to_repurchase,
    MAX(order_timestamp) AS last_processed_at
FROM filtered_orders
-- We filter out first-time purchases here because they don't have a 'previous' order to compare against
WHERE previous_order_timestamp IS NOT NULL
GROUP BY DATE(order_timestamp)