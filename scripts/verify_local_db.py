from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import asyncpg
from sqlalchemy.engine import make_url

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings


async def main() -> int:
    database_url = os.environ.get("DATABASE_URL") or settings.database_url
    url = make_url(database_url)
    connect_kwargs: dict[str, object] = {
        "user": url.username,
        "password": url.password,
        "host": url.host,
        "port": url.port,
        "database": url.database,
    }

    ssl_mode = url.query.get("ssl")
    if ssl_mode == "require":
        connect_kwargs["ssl"] = "require"

    conn = await asyncpg.connect(**connect_kwargs)
    try:
        database_name = await conn.fetchval("select current_database()")
        table_rows = await conn.fetch(
            """
            select table_name
            from information_schema.tables
            where table_schema = 'public'
              and table_name like 'ai_%'
            order by table_name
            """
        )

        version_exists = await conn.fetchval(
            """
            select exists (
                select 1
                from information_schema.tables
                where table_schema = 'public'
                  and table_name = 'alembic_version'
            )
            """
        )
        alembic_version = None
        if version_exists:
            alembic_version = await conn.fetchval("select version_num from alembic_version limit 1")

        table_names = [row["table_name"] for row in table_rows]

        print(f"DATABASE={database_name}")
        print(f"TABLE_COUNT={len(table_names)}")
        print(f"ALEMBIC_VERSION={alembic_version or 'missing'}")
        for name in table_names:
            print(f"TABLE={name}")

        expected = {
            "ai_conversations",
            "ai_messages",
            "ai_recommendation_logs",
        }
        missing = sorted(expected.difference(table_names))
        if missing:
            print("MISSING_TABLES=" + ",".join(missing))
            return 1
        return 0
    finally:
        await conn.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
