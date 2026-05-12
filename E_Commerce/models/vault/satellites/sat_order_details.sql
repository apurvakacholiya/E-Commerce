{{ config(materialized='incremental') }}

{%- set source_model = "stg_orders" -%}
{%- set src_pk = "hash_order_id" -%}
{%- set src_hashdiff = "order_hashdiff" -%}
{%- set src_payload = ["order_date", "order_amount", "order_status", "payment_method"] -%}
{%- set src_ldts = "loaded_at" -%}
{%- set src_source = "source_file_name" -%}

{{ automate_dv.sat(src_pk=src_pk, src_hashdiff=src_hashdiff,
                   src_payload=src_payload, src_ldts=src_ldts,
                   src_source=src_source, source_model=source_model) }}



--This holds the descriptive data and handles the CDC (Change Data Capture) logic using the order_hashdiff.