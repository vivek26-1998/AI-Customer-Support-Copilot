from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from ..db.schemas import CustomerRecord, OrderRecord


class SupportContext(BaseModel):
    """Scope is fixed by application code; private evidence is written by tools.

    A caller-supplied customer ID is still not authentication.
    """
    model_config = ConfigDict(extra='forbid', frozen=True)
    customer_id: str = Field(min_length=1, max_length=20)
    _customer: CustomerRecord | None = PrivateAttr(default=None)
    _orders: dict[str, OrderRecord] = PrivateAttr(default_factory=dict)
    _failed: bool = PrivateAttr(default=False)

    @property
    def customer(self) -> CustomerRecord | None:
        return self._customer

    @property
    def orders(self) -> dict[str, OrderRecord]:
        return dict(self._orders)

    @property
    def failed(self) -> bool:
        return self._failed

    def record_customer(self, customer: CustomerRecord) -> None:
        if customer.id != self.customer_id:
            raise ValueError('Customer scope mismatch')
        self._customer = customer

    def record_order(self, order: OrderRecord) -> None:
        if order.customer_id != self.customer_id:
            raise ValueError('Order scope mismatch')
        self._orders[order.id] = order

    def mark_failed(self) -> None:
        self._failed = True
