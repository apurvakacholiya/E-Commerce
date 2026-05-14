{{
    config(
        materialized='incremental',
        unique_key='report_date'  
    )
}}

WITH parsed_orders AS (
    SELECT
        RAW_DATA:order_id::string AS order_id,
        TRY_CAST(RAW_DATA:amount::string AS number(10,2)) AS amount,
        RAW_DATA:status::string AS status,
        TRY_CAST(RAW_DATA:order_time::string AS timestamp_ntz) AS order_time
    FROM {{ source('raw', 'orders_raw') }}
),

filtered_orders AS (
    SELECT * FROM parsed_orders
    
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