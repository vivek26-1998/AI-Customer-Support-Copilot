"""Internal persistence contracts, separate from SQLAlchemy models."""
from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class CustomerRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    priority_customer: bool


class OrderRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: str = Field(min_length=1)
    customer_id: str = Field(min_length=1)
    status: str = Field(min_length=1)
    expected_delivery: date | None
    tracking_id: str | None
    product_name: str = Field(min_length=1)
