CUSTOMERS = {
    "C-102": {
        "name": "Müller IT Services",
        "priority_customer": True,
    },
    "C-205": {
        "name": "Schmidt Electronics",
        "priority_customer": False,
    },
}


ORDERS = {
    "77881": {
        "customer_id": "C-102",
        "status": "in_transit",
        "expected_delivery": "2026-06-25",
        "tracking_id": "DHL-993812",
        "product_name": "Lenovo ThinkPad T14",
    },
    "99110": {
        "customer_id": "C-205",
        "status": "delayed",
        "expected_delivery": "2026-06-28",
        "tracking_id": "DHL-882100",
        "product_name": "HP EliteBook 840",
    },
}