from typing import Literal

from pydantic import BaseModel, ConfigDict


class ToolResult(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)


class ToolFailure(ToolResult):
    outcome: Literal['unavailable', 'invalid_input', 'error']


class CustomerToolResult(ToolResult):
    outcome: Literal['success'] = 'success'
    customer_id: str
    customer_name: str
    priority_customer: bool


class OrderToolResult(ToolResult):
    outcome: Literal['success'] = 'success'
    order_id: str
    status: str
    expected_delivery: str | None
    tracking_id: str | None
    product_name: str
