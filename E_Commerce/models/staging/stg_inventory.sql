WITH source AS (

    SELECT
        RAW_DATA,
        LOAD_TS
    FROM {{ source('raw', 'inventory_raw') }}

),

staged AS (

    SELECT
        RAW_DATA:product_id::string AS product_id,
        RAW_DATA:product_name::string AS product_name,
        TRY_CAST(RAW_DATA:stock::string AS integer) AS stock,
        TRY_TO_TIMESTAMP_TZ(RAW_DATA:updated_at::string) AS updated_at,
        LOAD_TS AS loaded_at
    FROM source

)

SELECT
    {{ dbt_utils.generate_surrogate_key(['product_id']) }} AS hash_product_id,
    product_id,
    product_name,
    stock,
    updated_at,
    loaded_at
FROM staged