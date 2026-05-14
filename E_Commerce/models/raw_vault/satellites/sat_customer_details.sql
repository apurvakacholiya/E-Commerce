{{ config(materialized='incremental') }}

{%- set source_model = "stg_customers" -%}
{%- set src_pk = "hash_customer_id" -%}
{%- set src_hashdiff = "customer_hashdiff" -%}
{%- set src_payload = ["customer_name", "email", "customer_created_at"] -%}
{%- set src_ldts = "loaded_at" -%}
{%- set src_source = "source_file_name" -%}

{{ automate_dv.sat(src_pk=src_pk, src_hashdiff=src_hashdiff,
                   src_payload=src_payload, src_ldts=src_ldts,
                   src_source=src_source, source_model=source_model) }}


--This captures the descriptive attributes using only the columns available in your staging model.