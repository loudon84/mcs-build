"""Database engine and session management."""

import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from settings import Settings


def create_db_engine(settings: Settings):
    """Create database engine."""
    # 确保 DSN 是 UTF-8 编码的字符串
    db_dsn = settings.db_dsn
    
    # 如果是字节串，尝试解码为 UTF-8
    if isinstance(db_dsn, bytes):
        try:
            db_dsn = db_dsn.decode('utf-8')
        except UnicodeDecodeError:
            # 如果 UTF-8 解码失败，尝试使用系统默认编码
            db_dsn = db_dsn.decode(sys.getdefaultencoding(), errors='replace')
    elif not isinstance(db_dsn, str):
        db_dsn = str(db_dsn)
    
    # 确保使用 psycopg (v3) 驱动，而不是 psycopg2
    # 如果 DSN 使用 postgresql://，SQLAlchemy 2.0+ 会自动使用 psycopg
    # 但为了明确，我们可以使用 postgresql+psycopg://
    if db_dsn.startswith('postgresql://'):
        # 替换为使用 psycopg3 驱动
        db_dsn = db_dsn.replace('postgresql://', 'postgresql+psycopg://', 1)
    
    return create_engine(db_dsn, echo=settings.app_env == "dev")


def create_session_factory(engine):
    """Create session factory."""
    return sessionmaker(bind=engine)

