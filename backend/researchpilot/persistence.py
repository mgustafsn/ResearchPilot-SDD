"""PostgreSQL storage and small, transactional, versioned SQL migrations."""

import os
from pathlib import Path

from sqlalchemy import MetaData, Table, create_engine, text

MIGRATIONS = Path(__file__).resolve().parents[2] / "migrations"


class Database:
    def __init__(self, url: str):
        self.engine = create_engine(url, echo=False, hide_parameters=True, pool_pre_ping=True)

    def migrate(self):
        with self.engine.begin() as connection:
            # Serialize startup migrations, including initial schema-version creation.
            connection.execute(text("SELECT pg_advisory_xact_lock(746201001)"))
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY)
            """))
            applied = set(
                connection.execute(text("SELECT version FROM schema_migrations")).scalars()
            )
            for migration in sorted(MIGRATIONS.glob("*.sql")):
                if migration.name not in applied:
                    connection.exec_driver_sql(migration.read_text())
                    connection.execute(text("INSERT INTO schema_migrations VALUES (:version)"),
                                       {"version": migration.name})
        self.projects = Table("projects", MetaData(), autoload_with=self.engine)

    def close(self):
        self.engine.dispose()


if __name__ == "__main__":
    database = None
    try:
        database = Database(os.environ["DATABASE_URL"])
        database.migrate()
    except Exception:
        raise SystemExit(
            "Database startup failed; check local configuration and availability"
        ) from None
    finally:
        if database is not None:
            database.close()
