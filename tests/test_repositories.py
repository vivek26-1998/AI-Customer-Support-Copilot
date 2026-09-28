from datetime import date

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, OperationalError

from app.db.models import Customer, Order
from app.db.repositories import SqlAlchemySupportRepository
from app.db.seed import seed_demo_data
from app.services.database import get_customer_record, get_order_record
from app.services.validation import validate_extraction
from test_validation import make_request, make_extraction


def test_repository_returns_typed_records_and_unknown_ids(db_sessions):
    with db_sessions() as session:
        repository = SqlAlchemySupportRepository(session)
        customer = repository.get_customer('C-102')
        order = repository.get_order('77881')
        assert customer.id == 'C-102'
        assert customer.priority_customer is True
        assert order.expected_delivery == date(2026, 6, 25)
        assert repository.get_customer('missing') is None
        assert repository.get_order('missing') is None
    # Results remain usable after the session closes; ORM objects never escape.
    assert order.product_name == 'Lenovo ThinkPad T14'


def test_database_lookups_serialize_dates_and_preserve_nulls(db_sessions):
    with db_sessions.begin() as session:
        order = session.get(Order, '77881')
        order.expected_delivery = None
        order.tracking_id = None
    record = get_order_record('77881')
    assert record['expected_delivery'] is None
    assert record['tracking_id'] is None
    assert get_customer_record('missing') is None
    assert get_order_record('missing') is None
    result = validate_extraction(make_request(), make_extraction('77881'))
    assert result.order_belongs_to_customer is True
    assert result.expected_delivery is None
    assert result.validation_errors == []


def test_validation_reads_database_changes_not_mock_data(db_sessions):
    with db_sessions.begin() as session:
        session.get(Order, '77881').status = 'delivered'
        session.get(Customer, 'C-102').priority_customer = False
    result = validate_extraction(make_request(), make_extraction('77881'))
    assert result.order_status == 'delivered'
    assert result.priority_customer is False
    assert result.expected_delivery == '2026-06-25'


@pytest.mark.parametrize('record', [
    lambda: Customer(id='C-102', name='Duplicate', priority_customer=False),
    lambda: Customer(id='NULL', name=None, priority_customer=False),
    lambda: Order(id='orphan', customer_id='missing', status='pending', product_name='Test'),
])
def test_database_enforces_constraints(db_sessions, record):
    with pytest.raises(IntegrityError):
        with db_sessions.begin() as session:
            session.add(record())
    assert get_customer_record('C-102') is not None
    assert get_order_record('orphan') is None


def test_seed_is_repeatable_and_preserves_existing_rows(db_sessions):
    with db_sessions.begin() as session:
        session.get(Customer, 'C-102').name = 'Existing customer'
        session.get(Order, '77881').status = 'delivered'
    with db_sessions.begin() as session:
        seed_demo_data(session)
        seed_demo_data(session)
    with db_sessions() as session:
        assert session.scalar(select(func.count()).select_from(Customer)) == 2
        assert session.scalar(select(func.count()).select_from(Order)) == 2
        assert session.get(Customer, 'C-102').name == 'Existing customer'
        assert session.get(Order, '77881').status == 'delivered'


def test_transaction_rolls_back_all_changes(db_sessions):
    with pytest.raises(RuntimeError):
        with db_sessions.begin() as session:
            session.add(Customer(id='rollback', name='Rollback', priority_customer=False))
            session.flush()
            raise RuntimeError('Abort')
    assert get_customer_record('rollback') is None


@pytest.mark.parametrize('lookup', ['get_customer_record', 'get_order_record'])
def test_database_failure_returns_no_partial_facts(monkeypatch, lookup):
    def unavailable(_):
        raise OperationalError('sensitive query', {}, Exception('private connection details'))
    monkeypatch.setattr('app.services.validation.' + lookup, unavailable)
    result = validate_extraction(make_request(), make_extraction('77881'))
    assert result.validation_errors == ['Business records are temporarily unavailable']
    assert result.customer_name is None
    assert result.order_status is None
    assert result.tracking_id is None
    assert 'private' not in result.model_dump_json()


def test_invalid_persisted_record_is_rejected(db_sessions):
    with db_sessions.begin() as session:
        session.get(Order, '77881').product_name = ''
    result = validate_extraction(make_request(), make_extraction('77881'))
    assert result.validation_errors == ['Business record is inconsistent']
    assert result.order_status is None
    assert result.verified_product_name is None


def test_missing_database_configuration_fails_closed(monkeypatch):
    from app.db.session import get_session_factory
    from app.services import database
    get_session_factory.cache_clear()
    monkeypatch.delenv('DATABASE_URL', raising=False)
    monkeypatch.setattr(database, 'get_session_factory', get_session_factory)
    try:
        result = validate_extraction(make_request(), make_extraction('77881'))
        assert result.validation_errors == ['Business records are temporarily unavailable']
        assert result.tracking_id is None
    finally:
        get_session_factory.cache_clear()


def test_postgres_migration_matches_models(db_engine):
    if db_engine.dialect.name != 'postgresql':
        return  # SQLite validates models directly; Alembic targets PostgreSQL.
    from alembic.autogenerate import compare_metadata
    from alembic.migration import MigrationContext
    from app.db.base import Base
    with db_engine.connect() as connection:
        context = MigrationContext.configure(connection)
        assert compare_metadata(context, Base.metadata) == []
