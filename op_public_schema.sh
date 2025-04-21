#!/bin/bash

# 只需要执行一次
alembic -c ./alembic.ini -x schema_name=public revision --autogenerate -m "create tenants table"
# 只需要执行一次
alembic -c ./alembic.ini -x schema_name=public upgrade head