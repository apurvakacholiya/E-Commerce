WITH source AS (
    SELECT
        RAW_DATA,
        FILE_NAME,
        LOAD_TS
    FROM {{ source('raw', 'orders_raw') }}
),

parsed AS (
    SELECT
        RAW_DATA:order_id::string AS order_id,
        RAW_DATA:customer_id::string AS customer_id,
        TRY_CAST(RAW_DATA:order_time::string AS timestamp_ntz) AS order_timestamp,
        TRY_CAST(RAW_DATA:order_time::string AS date) AS order_date,
        TRY_CAST(RAW_DATA:amount::string AS number(10,2)) AS order_amount,
        RAW_DATA:status::string AS order_status,
        RAW_DATA:payment_method::string AS payment_method,
        FILE_NAME AS source_file_name,
        LOAD_TS AS loaded_at
    FROM source
)

SELECT
    -- Convert dbt_utils VARCHAR hex string to BINARY(16)
    TO_BINARY({{ dbt_utils.generate_surrogate_key(['order_id']) }}, 'HEX') AS hash_order_id,
    TO_BINARY({{ dbt_utils.generate_surrogate_key(['customer_id']) }}, 'HEX') AS hash_customer_id,
    TO_BINARY({{ dbt_utils.generate_surrogate_key(['order_id', 'customer_id']) }}, 'HEX') AS hash_order_customer_id,

    -- Convert Hashdiff to BINARY(16)
    TO_BINARY({{ dbt_utils.generate_surrogate_key([
        'order_status', 
        'order_amount', 
        'payment_method'
    ]) }}, 'HEX') AS order_hashdiff,

    order_id,
    customer_id,
    order_timestamp,
    order_date,
    order_amount,
    order_status,
    payment_method,
    source_file_name,
    loaded_at
FROM parsed