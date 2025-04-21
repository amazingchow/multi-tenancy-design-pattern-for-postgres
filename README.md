
我们将采用**基于 Schema 的多租户策略 (Schema per Tenant)**, 这是 PostgreSQL 中一种非常流行的方案，兼顾了数据隔离性、性能和管理复杂度。

该方案的核心设计思路总结为4点:
* **共享数据库:** 所有租户共享同一个 PostgreSQL 数据库实例。
* **独立 Schema:** 每个租户拥有独立的数据库 Schema (例如 `tenant_company_a`, `tenant_company_b`)。租户特定的数据表（如 `users`, `products`, `orders`）将存在于各自的 Schema 中。
* **公共 Schema:** 一个 `public` Schema 用于存放所有租户共享的信息，主要是 `tenants` 表，用于记录所有租户的元数据（ID、名称、Schema 名称、状态等）。
* **动态切换:** 应用程序在处理请求时，需要识别当前请求属于哪个租户，然后在数据库会话/连接中动态设置 `search_path`，只搜索当前租户的 Schema。这样，标准的 ORM 查询（如 `SELECT * FROM users`）就会自动访问到租户专属的数据。

## **架构方案详解**

1.  **数据库设计**
    *   **数据库:** 单一数据库 (e.g., `crm`)
    *   **`public` Schema:**
        *   `tenants` 表:
            *   `id`: SERIAL PRIMARY KEY
            *   `name`: VARCHAR(64) NOT NULL UNIQUE (租户名称)
            *   `schema_name`: VARCHAR(64) NOT NULL UNIQUE (数据库 Schema 名称, e.g., `tenant_company_a`)
            *   `subdomain`: VARCHAR(64) NOT NULL UNIQUE (用于识别租户的子域名, e.g., `company_a`)
            *   `created_at`: TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            *   `is_active`: BOOLEAN DEFAULT TRUE
            *   *(可选)* 其他元数据字段 (配置、状态等)
    *   **租户 Schemas (e.g., `tenant_company_a`, `tenant_company_b`, ...):**
        *   每个 Schema 包含一套相同的表结构，例如：
            *   `users` 表 (id, username, email, ...)
            *   `products` 表 (id, name, price, ...)
            *   `orders` 表 (id, user_id, total, ...)
        *   这些表的结构由应用程序的模型定义。

2.  **租户识别**
    *   需要一种方法来确定每个传入请求属于哪个租户。常用方法包括：
        *   **子域名:** `alpha.myapp.com`, `beta.myapp.com` (推荐，清晰)
        *   **URL 路径:** `myapp.com/alpha/users`, `myapp.com/beta/users`
        *   **HTTP Header:** `X-Tenant-ID: alpha`
        *   **JWT Claim:** 在身份验证令牌中包含 `tenant_id`。
    *   **实现:** 我们将以 **HTTP Header** 为例。Web 框架的中间件将负责解析 HTTP header，提取 `tenant id`，并查询 `public.tenants` 表以获取 `schema_name`。

3.  **应用程序架构 (FastAPI + SQLAlchemy)**
    *   **Web 框架:** FastAPI (异步、高性能、依赖注入友好)
    *   **ORM:** SQLAlchemy (成熟、强大，支持异步)
    *   **数据库驱动:** `psycopg` (PostgreSQL 官方推荐的异步驱动)
    *   **中间件:**
        *   在每个请求处理之前运行。
        *   从请求头中提取租户标识符。
        *   查询 `public.tenants` 表验证租户并获取 `schema_name`。
        *   将 `schema_name` 存储在请求上下文 (Request State) 中，供后续依赖项使用。
        *   如果租户无效或未找到，返回 404 或 403 错误。
    *   **数据库会话管理 (依赖注入):**
        *   创建一个 FastAPI 依赖项 (e.g., `get_db`)。
        *   该依赖项从请求上下文中获取 `schema_name`。
        *   从 SQLAlchemy 的 `async_sessionmaker` 创建一个新的异步会话 (`AsyncSession`)。
        *   **关键步骤:** 在将会话传递给路由处理函数之前，执行 `SET LOCAL search_path = '{tenant_schema}';`。`SET LOCAL` 确保 `search_path` 的更改仅限于当前事务/会话。
        *   使用 `yield` 提供会话，并在 `finally` 块中确保会话关闭 (`await session.close()`)。
    *   **模型:**
        *   **公共模型:** 定义 `Tenant` 模型，并明确指定 `__table_args__ = {"schema": "public"}`。
        *   **租户模型:** 定义 `User`, `Product`, `Order` 等模型。这些模型不需要指定 Schema，因为 `search_path` 会确保它们在正确的租户 Schema 中被查找。
    *   **CRUD 操作:** 在 API 路由中使用注入的、已设置好 `search_path` 的数据库会话执行标准的 SQLAlchemy CRUD 操作。ORM 会自动查询正确 Schema 中的表。
    *   **数据库迁移:**
        *   Alembic 用于管理数据库 Schema 的变更。
        *   需要 **定制** Alembic 的 `env.py` 或编写脚本来处理多 Schema 迁移。
        *   **策略:**
            1.  有一个基础迁移脚本用于创建 `public.tenants` 表。
            2.  有另一套迁移脚本用于定义租户特定的表 (User, Product 等)。
            3.  需要一个脚本或命令行工具：
                *   遍历 `public.tenants` 中所有活跃的 `schema_name`。
                *   对每个 `schema_name`，运行 Alembic 迁移命令，并通过参数 (e.g., `-x schema_name=tenant_alpha`) 告知 Alembic 当前要操作的 Schema。
                *   Alembic 的 `env.py` 需要读取这个参数并相应地配置 `search_path` 或 `version_table_schema`。
    *   **租户创建/配置:**
        *   通常需要一个管理接口或命令行工具。
        *   **流程:**
            1.  在 `public.tenants` 表中创建一条新记录（包含唯一的 `name`、`schema_name` 和 `subdomain`）。
            2.  执行 SQL `CREATE SCHEMA tenant_new_schema;`。
            3.  运行针对 **新 Schema** 的 Alembic 迁移，以创建所有必要的租户表 (`alembic -x schema_name=tenant_new_schema upgrade head`)。
            4.  *(可选)* 初始化租户数据（如默认管理员用户）。

**优势:**

*   **强数据隔离:** 每个租户的数据物理上位于不同的 Schema 中，意外访问其他租户数据的风险较低。
*   **简化应用层:** ORM 查询看起来是标准的，不需要在每个查询中手动添加 `tenant_id` 条件。
*   **性能:** 查询通常只涉及单个 Schema，索引效率高。
*   **备份/恢复:** 可以相对容易地按 Schema 进行备份和恢复。

**挑战:**

*   **迁移管理:** 跨多个 Schema 应用数据库迁移需要额外的脚本和管理。
*   **连接管理:** 虽然共享数据库，但频繁切换 `search_path` 会有微小的开销。
*   **租户数量:** 大量 Schema (成千上万) 可能会给 PostgreSQL 的元数据管理带来一些压力，但通常不是主要瓶颈。
*   **跨租户查询:** 如果需要跨多个租户进行聚合查询（如平台级报表），会稍微复杂一些（需要显式指定 Schema 或使用 UNION ALL）。

---

**运行应用:**

1.  确保 PostgreSQL 服务器正在运行，并且数据库已创建。
2.  设置 `.env` 文件。
3.  激活虚拟环境。
4.  运行 Alembic 迁移以创建 `public.tenants` 表: `alembic -x schema_name=public upgrade head`
5.  启动 FastAPI 应用: `make local_run`
6.  **测试:**
    *   **创建租户 (需要 Admin Key):**
        ```bash
        curl -X POST "http://localhost:17891/api/v1/admin/tenants/" \
            -H "Content-Type: application/json" \
            -H "X-Admin-Key: your_secret_admin_key" \
            -d '{"name": "Adidas", "schema_name": "tenant_adidas", "subdomain": "adidas"}'
        ```
    *   **手动运行新租户的迁移:**
        `python run_migrations.py` (或 `alembic -x schema_name=tenant_alpha upgrade head`)
    *   **为租户添加数据:**
        ```bash
        curl -X POST "http://localhost:17891/api/v1/users/" \
             -H "Content-Type: application/json" \
             -H "X-Tenant-ID: 2" \
             -d '{"name": "Super Widget", "price": 99.99}'
        ```
    *   **获取租户数据:**
        ```bash
        curl -X GET "http://localhost:17891/api/v1/users/" \
             -H "X-Tenant-ID: 2"
        ```
    *   尝试访问不存在的租户或没有 Host header 应该返回错误。
    *   创建第二个租户 `beta`，运行迁移，然后添加和获取其数据，验证隔离性。

这是一个相当完整的方案，涵盖了核心概念和实现细节。根据实际需求，可能还需要考虑更复杂的权限管理、后台任务处理、更健壮的错误处理和日志记录等。
