"""Lazy database setup: imports and deterministic tests need no database URL."""
import os
from functools import lru_cache

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class DatabaseConfigurationError(RuntimeError):
    pass


@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker:
    load_dotenv()
    url = os.getenv('DATABASE_URL')
    if not url:
        raise DatabaseConfigurationError('DATABASE_URL is not configured')
    engine = create_engine(url, pool_pre_ping=True)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
