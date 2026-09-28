from pydantic import BaseModel, Field
from typing import Optional

class EmailAnalysisRequest(BaseModel):
    customer_id: str
    email_subject: str
    email_body: str

class EmailExtraction(BaseModel):
    category: str
    order_id: Optional[str] = None
    product_name: Optional[str] = None
    internal_summary: str

class AgentDecision(BaseModel):
    category: str
    order_id: Optional[str] = None
    product_name: Optional[str] = None
    priority_customer: bool
    requires_human_review: bool
    next_action: str
    internal_summary: str
    draft_reply: str

class EmailAnalysisResponse(BaseModel):
    category: str
    customer_id: str
    order_id: Optional[str]
    product_name: Optional[str]
    priority_customer: bool
    requires_human_review: bool
    next_action: str
    internal_summary: str
    draft_reply: str


class ValidationResult(BaseModel):
    customer_id: str
    customer_found: bool
    customer_name: Optional[str] = None
    priority_customer: bool = False

    order_id: Optional[str] = None
    order_found: bool = False
    order_belongs_to_customer: bool = False

    order_status: Optional[str] = None
    expected_delivery: Optional[str] = None
    tracking_id: Optional[str] = None
    verified_product_name: Optional[str] = None

    validation_errors: list[str] =  Field(default_factory=list)