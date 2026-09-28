"""Explicit, insert-only demo seeding. Never runs at application startup."""
from datetime import date

from sqlalchemy.orm import Session

from ..mock_data import CUSTOMERS, ORDERS
from .models import Customer, Order
from .session import get_session_factory


def seed_demo_data(session: Session) -> None:
    """Insert missing demo rows without overwriting data; caller owns transaction."""
    for customer_id, fields in CUSTOMERS.items():
        if session.get(Customer, customer_id) is None:
            session.add(Customer(id=customer_id, **fields))
    session.flush()
    for order_id, fields in ORDERS.items():
        if session.get(Order, order_id) is None:
            values = dict(fields)
            delivery = values['expected_delivery']
            values['expected_delivery'] = date.fromisoformat(delivery) if delivery else None
            session.add(Order(id=order_id, **values))
    session.flush()


def main() -> None:
    with get_session_factory().begin() as session:
        seed_demo_data(session)
    print('Demo seed completed; existing rows were preserved.')


if __name__ == '__main__':
    main()
