{{ config(materialized='incremental') }}

{%- set source_model = "stg_orders" -%}
{%- set src_pk = "hash_order_id" -%}
{%- set src_nk = "order_id" -%}
{%- set src_ldts = "loaded_at" -%}
{%- set src_source = "source_file_name" -%}

{{ automate_dv.hub(src_pk=src_pk, src_nk=src_nk, 
                   src_ldts=src_ldts, src_source=src_source,
                   source_model=source_model) }}



--This Hub ensures that every unique Business Key (order_id) is captured only once.