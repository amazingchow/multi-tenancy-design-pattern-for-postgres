# -*- coding: utf-8 -*-
import logging
import os
import subprocess

import psycopg
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

# Simple parsing for asyncpg DSN or connection string components
# This is basic, consider using a proper URL parser like sqlalchemy.engine.url.make_url
conn_details = {}
if DATABASE_URL.startswith("postgresql+psycopg://"):
    parts = DATABASE_URL.split("://")[1]
    user_pass, host_db = parts.split("@")
    user, password = user_pass.split(":")
    host_port, database = host_db.split("/")
    if ":" in host_port:
        host, port = host_port.split(":")
    else:
        host = host_port
        port = 5432
    conn_details = {
        "user": user, "password": password, "dbname": database, "host": host, "port": int(port)
    }
else:
    logger.error(f"Unsupported DATABASE_URL format: {DATABASE_URL}")
    exit(1)


def get_active_tenant_schemas():
    conn = None
    try:
        conn = psycopg.connect(**conn_details)
        with conn.cursor() as cur:
            cur.execute("SELECT schema_name FROM public.tenants WHERE is_active = true;")
            rows = cur.fetchall()
            return [row[0] for row in rows]
    except Exception as e:
        logger.error(f"Error connecting to database or fetching tenants: {e}")
        return []
    finally:
        if conn:
            conn.close()


def run_alembic_for_schema(schema_name):
    logger.info(f"--- Running migrations for schema: {schema_name} ---")
    if schema_name == "public":
        command = ["alembic", "-x", f"schema_name={schema_name}", "upgrade", "head"]
    else:
        command = ["alembic", "-c", "./alembic-tenants.ini", "-x", f"schema_name={schema_name}", "upgrade", "head"]
    try:
        # Run Alembic command
        # capture_output=True might hide Alembic's own progress output
        result = subprocess.run(command, check=True, text=True, capture_output=True)
        logger.info(result.stdout)
        if result.stderr:
            logger.info("--- Alembic stderr ---")
            logger.info(result.stderr)
        logger.info(f"--- Migrations for {schema_name} completed successfully ---")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"!!! Error running migrations for schema: {schema_name} !!!")
        logger.error(e)
        logger.error("--- Alembic stdout ---")
        logger.error(e.stdout)
        logger.error("--- Alembic stderr ---")
        logger.error(e.stderr)
        return False
    except FileNotFoundError:
        logger.error("Error: 'alembic' command not found. Is your virtual environment activated and Alembic installed?")
        return False


def main():
    logger.info("Starting migration process for all active tenants and public schema...")

    # 1. Migrate public schema first (optional, depends if public schema has changes)
    logger.info("Migrating 'public' schema...")
    if not run_alembic_for_schema("public"):
        logger.error("Halting due to error in public schema migration.")
        return

    # 2. Get active tenant schemas
    logger.info("Fetching active tenant schemas...")
    tenant_schemas = get_active_tenant_schemas()
    if not tenant_schemas:
        logger.error("No active tenant schemas found or error fetching them.")
        return
    logger.info(f"Found {len(tenant_schemas)} active tenant schemas: {tenant_schemas}")

    # 3. Migrate each tenant schema
    success_count = 0
    failure_count = 0
    for schema in tenant_schemas:
        if run_alembic_for_schema(schema):
            success_count += 1
        else:
            failure_count += 1

    logger.info("--- Migration Summary ---")
    logger.info(f"Successfully migrated schemas: {success_count}")
    logger.info(f"Failed schemas: {failure_count}")
    if failure_count > 0:
        logger.error("!!! Please check the logs for errors in failed schema migrations. !!!")
    logger.info("Migration process finished.")


if __name__ == "__main__":
    main()
