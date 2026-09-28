"""Compatibility lookups backed by repositories, never by mock dictionaries."""
from ..db.repositories import SqlAlchemySupportRepository, SupportRepository
from ..db.session import get_session_factory


def get_customer_record(customer_id: str) -> dict | None:
    with get_session_factory()() as session:
        repository: SupportRepository = SqlAlchemySupportRepository(session)
        record = repository.get_customer(customer_id)
        return record.model_dump(mode='json', exclude={'id'}) if record else None


def get_order_record(order_id: str) -> dict | None:
    with get_session_factory()() as session:
        repository: SupportRepository = SqlAlchemySupportRepository(session)
        record = repository.get_order(order_id)
        return record.model_dump(mode='json', exclude={'id'}) if record else None
