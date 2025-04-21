#!/bin/bash

# Apply Migrations to a Specific Tenant Schema:
#     When a new tenant `alpha` (schema: `tenant_alpha`) is created via the API:
#     1.  API creates the `public.tenants` record.
#     2.  API executes `CREATE SCHEMA tenant_alpha;`.
#     3.  Separate Process/Script: Run `alembic -x schema_name=tenant_alpha upgrade head`. This applies all migration scripts (including the one for tenant tables) to the `tenant_alpha` schema.
# Apply Migrations to All Existing Tenants (e.g., after adding a new table):
#     Create a new migration: `alembic -x schema_name=tenant_template revision --autogenerate -m "Add description to items"`
#     Create a script (`run_migrations.py` or shell script) to:
#         Connect to the database (using standard SQL connection, not tenant-specific one).
#         Query `SELECT schema_name FROM public.tenants WHERE is_active = true;`.
#         For each `schema_name`:
#             Execute `alembic -x schema_name={schema_name} upgrade head`.
#         Also run for public schema if needed: `alembic -x schema_name=public upgrade head`.

# （每次变更数据库模型时）只需要执行一次
alembic -c ./alembic-tenants.ini -x schema_name=tenant_nike revision --autogenerate -m "init all tables"
alembic -c ./alembic-tenants.ini -x schema_name=tenant_nike revision --autogenerate -m "add more tables and columns"
# 新建租户时执行一次
alembic -c ./alembic-tenants.ini -x schema_name=tenant_nike upgrade head
