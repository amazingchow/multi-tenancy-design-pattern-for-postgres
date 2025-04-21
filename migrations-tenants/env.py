# -*- coding: utf-8 -*-
import os
import sys

sys.path.append(os.path.join(os.path.abspath(os.curdir), 'models'))

import logging
from logging.config import fileConfig

from models.public import Tenant
from models.tenant import User

from alembic import context
from sqlalchemy import engine_from_config, pool

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
logger = logging.getLogger('alembic')


def get_schema_name_from_context() -> str:
    """Get schema name from -x argument"""
    return context.get_x_argument(as_dictionary=True).get('schema_name', 'public')


def include_name(name, type_, parent_names):
    return True


def include_object(object, name, type_, reflected, compare_to):
    """
    Control which objects are included in the migration generation (autogenerate).
    We want to conditionally include objects based on the target schema.
    """
    target_schema = get_schema_name_from_context()
    if type_ == "table":
        if target_schema:
            if object.schema == 'public':
                return target_schema == 'public'
            elif object.schema is None:
                return target_schema != 'public'
            else:
                return object.schema == target_schema
        else:
            if context.is_autogenerate_command():
                logger.warning("WARNING: Autogenerate requires -x schema_name=public or -x schema_name=<tenant_schema>")
                logger.warning("         Including all objects for now, but migrations should target specific schemas.")
                raise ValueError("Please specify the target schema for autogenerate using -x schema_name=<name> (e.g., public or a tenant schema)")
    elif type_ == "schema":
        return name == target_schema
    else:
        return True


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    schema_name = get_schema_name_from_context()
    if not schema_name:
        raise ValueError("Schema name must be provided using -x schema_name=<name>")
    
    logger.info(f"Running migrations under schema: '{schema_name}'")

    # --- 设置 search_path ---
    # PostgreSQL 的连接选项通过 'options' 参数传递，格式是 '-c <parameter>=<value>'
    search_path_option = f"-c search_path={schema_name}"
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args={'options': search_path_option}
    )

    if schema_name == 'public':
        target_metadata = Tenant.metadata
    else:
        target_metadata = User.metadata
    
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema=schema_name,
            include_schemas=True,
            include_name=include_name,
            include_object=include_object,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
