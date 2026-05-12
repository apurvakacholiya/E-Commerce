WITH source AS (
    SELECT
        RAW_DATA,
        FILE_NAME,
        LOAD_TS
    FROM {{ source('raw', 'customers_raw') }}
),

parsed AS (
    SELECT
        RAW_DATA:customer_id::string AS customer_id,
        RAW_DATA:name::string AS customer_name,
        RAW_DATA:email::string AS email,
        TRY_CAST(RAW_DATA:created_at::string AS timestamp_ntz) AS customer_created_at,
        FILE_NAME AS source_file_name,
        LOAD_TS AS loaded_at
    FROM source
)

SELECT
    -- Convert Primary Key to BINARY for Data Vault compatibility
    TO_BINARY({{ dbt_utils.generate_surrogate_key(['customer_id']) }}, 'HEX') AS hash_customer_id,
    
    -- Hashdiff for Satellite CDC (tracks changes to name and email)
    TO_BINARY({{ dbt_utils.generate_surrogate_key([
        'customer_name', 
        'email'
    ]) }}, 'HEX') AS customer_hashdiff,

    customer_id,
    customer_name,
    email,
    customer_created_at,
    source_file_name,
    loaded_at
FROM parsed