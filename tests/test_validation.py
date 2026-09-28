from app.schemas import EmailAnalysisRequest, EmailExtraction
from app.services.validation import validate_extraction


def make_request(customer_id: str = "C-102") -> EmailAnalysisRequest:
    return EmailAnalysisRequest(
        customer_id=customer_id,
        email_subject="Order question",
        email_body="Please provide an update.",
    )


def make_extraction(order_id: str | None) -> EmailExtraction:
    return EmailExtraction(
        category="delivery_status_request",
        order_id=order_id,
        internal_summary="Customer requests an order update.",
    )


def test_valid_order_ownership_returns_verified_facts():
    result = validate_extraction(make_request(), make_extraction("77881"))

    assert result.customer_found is True
    assert result.order_found is True
    assert result.order_belongs_to_customer is True
    assert result.order_status == "in_transit"
    assert result.tracking_id == "DHL-993812"
    assert result.verified_product_name == "Lenovo ThinkPad T14"
    assert result.validation_errors == []


def test_unknown_customer_stops_before_order_disclosure():
    result = validate_extraction(make_request("C-999"), make_extraction("77881"))

    assert result.customer_found is False
    assert result.order_found is False
    assert result.order_status is None
    assert result.tracking_id is None
    assert result.validation_errors == ["Customer was not found"]


def test_missing_order_id_preserves_verified_customer():
    result = validate_extraction(make_request(), make_extraction(None))

    assert result.customer_found is True
    assert result.customer_name is not None
    assert result.order_id is None
    assert result.order_found is False


def test_unknown_order_returns_no_order_facts():
    result = validate_extraction(make_request(), make_extraction("00000"))

    assert result.order_found is False
    assert result.order_status is None
    assert result.tracking_id is None
    assert result.validation_errors == ["Order was not found"]


def test_cross_customer_order_returns_no_order_facts():
    result = validate_extraction(make_request(), make_extraction("99110"))

    assert result.order_found is True
    assert result.order_belongs_to_customer is False
    assert result.order_status is None
    assert result.expected_delivery is None
    assert result.tracking_id is None
    assert result.verified_product_name is None
    assert result.validation_errors == [
        "Order does not belong to the supplied customer"
    ]


def test_inconsistent_order_record_returns_safe_error(monkeypatch):
    monkeypatch.setattr(
        "app.services.validation.get_order_record",
        lambda _order_id: {"customer_id": "C-102", "status": "in_transit"},
    )

    result = validate_extraction(make_request(), make_extraction("77881"))

    assert result.order_found is True
    assert result.order_belongs_to_customer is False
    assert result.order_status is None
    assert result.validation_errors == ["Order record is inconsistent"]
