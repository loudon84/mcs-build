"""Alembic environment for listener DB (message_records)."""

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

_current_file = Path(__file__).resolve()
_migrations_dir = _current_file.parent
_db_dir = _migrations_dir.parent
_listener_dir = _db_dir.parent
_src_dir = _listener_dir.parent

if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

_project_root = _src_dir.parent
if _project_root.exists():
    os.chdir(_project_root)

from listener.db.models import Base
from settings import Settings

config = context.config
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

env_file = _project_root / ".env"
db_dsn = None
if env_file.exists():
    try:
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line and not line.startswith("="):
                    key, value = line.split("=", 1)
                    key, value = key.strip(), value.strip()
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    if key in ("LISTENER_DB_DSN", "listener_db_dsn"):
                        db_dsn = value
                        break
    except Exception:
        pass

if db_dsn is None:
    settings = Settings.from_env()
    db_dsn = settings.listener_db_dsn

if isinstance(db_dsn, bytes):
    try:
        db_dsn = db_dsn.decode("utf-8")
    except UnicodeDecodeError:
        db_dsn = db_dsn.decode(sys.getdefaultencoding(), errors="replace")
elif not isinstance(db_dsn, str):
    db_dsn = str(db_dsn)

if db_dsn.startswith("postgresql://"):
    db_dsn = db_dsn.replace("postgresql://", "postgresql+psycopg://", 1)

config.set_main_option("sqlalchemy.url", db_dsn)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
