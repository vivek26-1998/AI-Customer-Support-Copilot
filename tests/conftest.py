"""Deterministic tests use an isolated DB and never load model credentials."""
import os
import uuid
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from dotenv import dotenv_values
from sqlalchemy import create_engine, event, inspect
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import CreateSchema, DropSchema
from sqlalchemy.pool import StaticPool

os.environ['PYTHON_DOTENV_DISABLED'] = '1'
os.environ.pop('OPENAI_API_KEY', None)
os.environ['OPENAI_AGENTS_DISABLE_TRACING'] = '1'

ROOT = Path(__file__).resolve().parents[1]


def pytest_addoption(parser):
    parser.addoption('--postgres', action='store_true', help='Also test isolated PostgreSQL schema using TEST_DATABASE_URL')


def pytest_generate_tests(metafunc):
    if 'db_engine' in metafunc.fixturenames:
        backends = ['sqlite', 'postgresql'] if metafunc.config.getoption('--postgres') else ['sqlite']
        metafunc.parametrize('db_engine', backends, indirect=True, scope='session')


def migrate(connection, revision, *, downgrade=False):
    config = Config(str(ROOT / 'alembic.ini'))
    config.attributes['connection'] = connection
    config.attributes['configure_logger'] = False
    (command.downgrade if downgrade else command.upgrade)(config, revision)


@pytest.fixture(scope='session')
def db_engine(request):
    from app.db.base import Base
    from app.db import models  # Register metadata.

    if request.param == 'sqlite':
        engine = create_engine('sqlite://', poolclass=StaticPool,
                               connect_args={'check_same_thread': False})
        @event.listens_for(engine, 'connect')
        def configure_sqlite(connection, _):
            connection.isolation_level = None
            connection.execute('PRAGMA foreign_keys=ON')
        @event.listens_for(engine, 'begin')
        def explicit_begin(connection):
            connection.exec_driver_sql('BEGIN')
        Base.metadata.create_all(engine)
        try:
            yield engine
        finally:
            engine.dispose()
        return

    values = dotenv_values(ROOT / '.env')
    url = os.getenv('TEST_DATABASE_URL') or values.get('TEST_DATABASE_URL')
    if not url or make_url(url).get_backend_name() != 'postgresql':
        pytest.fail('--postgres requires a PostgreSQL TEST_DATABASE_URL')
    primary = os.getenv('DATABASE_URL') or values.get('DATABASE_URL')
    def location(value):
        parsed = make_url(value)
        return parsed.host, parsed.port or 5432, parsed.database
    if primary and location(url) == location(primary):
        pytest.fail('TEST_DATABASE_URL must identify a separate test database')
    schema = 'test_copilot_' + uuid.uuid4().hex
    admin = create_engine(url, connect_args={'connect_timeout': 5})
    engine = None
    try:
        with admin.begin() as connection:
            connection.execute(CreateSchema(schema))
        engine = create_engine(url, connect_args={
            'connect_timeout': 5, 'options': '-csearch_path=' + schema,
        })
        with engine.begin() as connection:
            migrate(connection, 'head')
            assert {'customers', 'orders', 'alembic_version'} <= set(inspect(connection).get_table_names())
            migrate(connection, 'base', downgrade=True)
            assert 'customers' not in inspect(connection).get_table_names()
            assert 'orders' not in inspect(connection).get_table_names()
            migrate(connection, 'head')
        yield engine
    finally:
        if engine is not None:
            engine.dispose()
        # Only the generated test schema is removed; public tables are untouched.
        with admin.begin() as connection:
            connection.execute(DropSchema(schema, cascade=True, if_exists=True))
        admin.dispose()


@pytest.fixture(autouse=True)
def db_sessions(db_engine, monkeypatch):
    from app.db.seed import seed_demo_data
    from app.services import database

    with db_engine.connect() as connection:
        transaction = connection.begin()
        sessions = sessionmaker(bind=connection, expire_on_commit=False,
                                join_transaction_mode='create_savepoint')
        try:
            with sessions.begin() as session:
                seed_demo_data(session)
            monkeypatch.setattr(database, 'get_session_factory', lambda: sessions)
            yield sessions
        finally:
            transaction.rollback()
