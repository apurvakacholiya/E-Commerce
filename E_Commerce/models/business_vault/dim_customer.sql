{{ config(
    materialized='table',
    description='SCD Type 2 Customer Dimension built from Raw Vault'
) }}

WITH hub AS (
    SELECT 
        hash_customer_id,
        customer_id
    FROM {{ ref('hub_customer') }}
),

sat AS (
    SELECT 
        hash_customer_id,
        customer_name,
        email,
        customer_created_at,
        loaded_at AS valid_from
    FROM {{ ref('sat_customer_details') }}
),

-- 1. Join Hub and Satellite to get Business Keys and Attributes
joined AS (
    SELECT 
        h.customer_id,
        s.customer_name,
        s.email,
        s.customer_created_at,
        s.valid_from,
        -- 2. Use LEAD to find the start date of the NEXT record for this customer
        LEAD(s.valid_from) OVER (
            PARTITION BY h.hash_customer_id 
            ORDER BY s.valid_from
        ) AS valid_to
    FROM hub h
    JOIN sat s ON h.hash_customer_id = s.hash_customer_id
),

-- 3. Clean up the SCD Type 2 columns (Active flags and default end dates)
scd_logic AS (
    SELECT
        -- Create a unique Surrogate Key for the dimension row
        {{ dbt_utils.generate_surrogate_key(['customer_id', 'valid_from']) }} AS customer_sk,
        customer_id,
        customer_name,
        email,
        customer_created_at,
        valid_from,
        -- If valid_to is null, it means this is the most current record
        COALESCE(valid_to, '9999-12-31 23:59:59'::timestamp_ntz) AS valid_to,
        -- Boolean flag for easy BI filtering
        CASE 
            WHEN valid_to IS NULL THEN TRUE 
            ELSE FALSE 
        END AS is_current
    FROM joined
)

SELECT * FROM scd_logic