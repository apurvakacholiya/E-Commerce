{{
    config(
        materialized='incremental',
        unique_key='report_date'  
    )
}}

WITH staged_orders AS (
    SELECT
        order_id,
        amount,
        status,
        order_time
    FROM {{ ref('stg_orders') }}
),

filtered_orders AS (
    SELECT * FROM staged_orders
    
    --late-arriving logic with a 48-hour look-back window
    {% if is_incremental() %}
        WHERE order_time >= (
            SELECT DATEADD(hour, -48, MAX(LAST_ORDER_PROCESSED_AT)) 
            FROM {{ this }}
        )
    {% endif %}
)

--final business KPIs
SELECT 
    DATE(order_time) AS report_date,
    COUNT(DISTINCT order_id) AS total_orders,
    SUM(amount) AS daily_revenue,
    SUM(CASE WHEN status = 'delivered' THEN amount ELSE 0 END) AS delivered_revenue,
    MAX(order_time) AS last_order_processed_at
FROM filtered_orders
GROUP BY DATE(order_time)