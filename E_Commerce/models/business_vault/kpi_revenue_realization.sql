{{
    config(
        materialized='incremental',
        unique_key='report_date'  
    )
}}

WITH staged_orders AS (
    SELECT
        order_amount,
        order_status,
        order_timestamp
    FROM {{ ref('stg_orders') }}
),

filtered_orders AS (
    SELECT * FROM staged_orders
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
        SUM(CASE WHEN order_status = 'delivered' THEN order_amount ELSE 0 END) / NULLIF(SUM(order_amount), 0), 4
    ) AS revenue_realization_rate,
    MAX(order_timestamp) AS last_processed_at
FROM filtered_orders
GROUP BY DATE(order_timestamp)