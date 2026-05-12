{{ config(materialized='incremental') }}

{%- set source_model = "stg_orders" -%}
{%- set src_pk = "hash_order_customer_id" -%}
{%- set src_fk = ["hash_order_id", "hash_customer_id"] -%}
{%- set src_ldts = "loaded_at" -%}
{%- set src_source = "source_file_name" -%}

{{ automate_dv.link(src_pk=src_pk, src_fk=src_fk, 
                    src_ldts=src_ldts, src_source=src_source,
                    source_model=source_model) }}



--This records the relationship between an Order and a Customer.