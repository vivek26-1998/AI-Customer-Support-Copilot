from ..schemas import (
    EmailAnalysisRequest,
    EmailExtraction,
    ValidationResult,
)
from .database import get_customer_record, get_order_record


def validate_extraction(
    request: EmailAnalysisRequest,
    extraction: EmailExtraction,
) -> ValidationResult:
    customer = get_customer_record(request.customer_id)

    if customer is None:
        return ValidationResult(
            customer_id=request.customer_id,
            customer_found=False,
            order_id=extraction.order_id,
            validation_errors=["Customer was not found"],
        )

    if extraction.order_id is None:
        return ValidationResult(
            customer_id=request.customer_id,
            customer_found=True,
            customer_name=customer["name"],
            priority_customer=customer["priority_customer"],
        )

    order = get_order_record(extraction.order_id)

    if order is None:
        return ValidationResult(
            customer_id=request.customer_id,
            customer_found=True,
            customer_name=customer["name"],
            priority_customer=customer["priority_customer"],
            order_id=extraction.order_id,
            order_found=False,
            validation_errors=["Order was not found"],
        )

    required_order_fields = {
        "customer_id",
        "status",
        "expected_delivery",
        "tracking_id",
        "product_name",
    }
    if not required_order_fields.issubset(order):
        return ValidationResult(
            customer_id=request.customer_id,
            customer_found=True,
            customer_name=customer["name"],
            priority_customer=customer["priority_customer"],
            order_id=extraction.order_id,
            order_found=True,
            validation_errors=["Order record is inconsistent"],
        )

    belongs_to_customer = (
        order["customer_id"] == request.customer_id
    )

    if not belongs_to_customer:
        return ValidationResult(
            customer_id=request.customer_id,
            customer_found=True,
            customer_name=customer["name"],
            priority_customer=customer["priority_customer"],
            order_id=extraction.order_id,
            order_found=True,
            order_belongs_to_customer=False,
            validation_errors=[
                "Order does not belong to the supplied customer"
            ],
        )

    return ValidationResult(
        customer_id=request.customer_id,
        customer_found=True,
        customer_name=customer["name"],
        priority_customer=customer["priority_customer"],
        order_id=extraction.order_id,
        order_found=True,
        order_belongs_to_customer=True,
        order_status=order["status"],
        expected_delivery=order["expected_delivery"],
        tracking_id=order["tracking_id"],
        verified_product_name=order["product_name"],
    )
