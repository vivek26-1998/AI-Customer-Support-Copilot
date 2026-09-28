from ..mock_data import CUSTOMERS, ORDERS

def get_customer_record(customer_id: str) -> dict | None:
    return CUSTOMERS.get(customer_id)
def get_order_record(order_id: str) -> dict | None:
    return ORDERS.get(order_id)
