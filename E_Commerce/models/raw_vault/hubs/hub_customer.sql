{{ config(materialized='incremental') }}

{%- set source_model = "stg_customers" -%}
{%- set src_pk = "hash_customer_id" -%}
{%- set src_nk = "customer_id" -%}
{%- set src_ldts = "loaded_at" -%}
{%- set src_source = "source_file_name" -%}

{{ automate_dv.hub(src_pk=src_pk, src_nk=src_nk, 
                   src_ldts=src_ldts, src_source=src_source,
                   source_model=source_model) }}



--This captures the unique business key.