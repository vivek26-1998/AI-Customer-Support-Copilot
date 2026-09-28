"""Internal reads for validation; callers must verify ownership before disclosure."""
from typing import Protocol

from sqlalchemy.orm import Session

from .models import Customer, Order
from .schemas import CustomerRecord, OrderRecord


class SupportRepository(Protocol):
    def get_customer(self, customer_id: str) -> CustomerRecord | None: ...
    def get_order(self, order_id: str) -> OrderRecord | None: ...


class SqlAlchemySupportRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_customer(self, customer_id: str) -> CustomerRecord | None:
        record = self.session.get(Customer, customer_id)
        return CustomerRecord.model_validate(record) if record is not None else None

    def get_order(self, order_id: str) -> OrderRecord | None:
        record = self.session.get(Order, order_id)
        return OrderRecord.model_validate(record) if record is not None else None
