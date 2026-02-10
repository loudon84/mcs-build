"""Alembic environment configuration."""

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# 确保 src/ 目录在 Python 路径中，以便导入模块
# alembic 从 migrations/ 目录运行，需要向上两级找到 src/
_current_file = Path(__file__).resolve()
_src_dir = _current_file.parent.parent.parent  # src/ 目录
_project_root = _src_dir.parent  # 项目根目录（orchestrator）

if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

# 确保从项目根目录读取 .env 文件
# 切换到项目根目录，这样 Settings 能找到 .env 文件
if _project_root.exists():
    os.chdir(_project_root)

from db.models import Base
from settings import Settings

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Get settings and set database URL
# 确保使用 UTF-8 编码读取环境变量
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

# 直接从 .env 文件读取 ORCHESTRATION_DB_DSN，避免 PowerShell 环境变量编码问题
env_file = _project_root / ".env"
db_dsn = None

if env_file.exists():
    try:
        # 直接读取 .env 文件，查找 ORCHESTRATION_DB_DSN 或 DB_DSN（向后兼容）
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # 跳过注释和空行
                if not line or line.startswith("#"):
                    continue
                # 解析 KEY=VALUE
                if "=" in line and not line.startswith("="):
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    # 移除引号
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    if key == "ORCHESTRATION_DB_DSN":
                        db_dsn = value
                        break
                    elif key == "DB_DSN" and db_dsn is None:
                        # 向后兼容：如果没有 ORCHESTRATION_DB_DSN，使用 DB_DSN
                        db_dsn = value
    except Exception:
        # 如果读取失败，回退到 Settings
        pass

# 如果从 .env 文件读取失败，使用 Settings
if db_dsn is None:
    settings = Settings.from_env()
    db_dsn = settings.get_orchestration_db_dsn()

# 确保 DSN 是 UTF-8 编码的字符串
if isinstance(db_dsn, bytes):
    try:
        db_dsn = db_dsn.decode('utf-8')
    except UnicodeDecodeError:
        db_dsn = db_dsn.decode(sys.getdefaultencoding(), errors='replace')
elif not isinstance(db_dsn, str):
    db_dsn = str(db_dsn)

# 确保 DSN 使用 psycopg3 驱动（如果可用）
if db_dsn.startswith('postgresql://'):
    # 替换为使用 psycopg3 驱动
    db_dsn = db_dsn.replace('postgresql://', 'postgresql+psycopg://', 1)

config.set_main_option("sqlalchemy.url", db_dsn)

# add your model's MetaData object here
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
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
    """Run migrations in 'online' mode."""
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

