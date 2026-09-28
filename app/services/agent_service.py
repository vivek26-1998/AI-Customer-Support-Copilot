from ..schemas import (
    AgentDecision,
    EmailAnalysisRequest,
    EmailAnalysisResponse,
    EmailExtraction,
    ValidationResult,
)
from agents import Agent, Runner, RunContextWrapper, function_tool
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

load_dotenv()

@function_tool
def get_customer(ctx: RunContextWrapper[ValidationResult], customer_id: str) -> dict:
    """Return only the customer verified for this request."""
    facts = ctx.context
    if customer_id != facts.customer_id or not facts.customer_found or facts.validation_errors:
        return {"authorized": False}
    return {
        "found": True,
        "customer_id": facts.customer_id,
        "customer_name": facts.customer_name,
        "priority_customer": facts.priority_customer,
    }


@function_tool
def get_order(
    ctx: RunContextWrapper[ValidationResult], order_id: str, customer_id: str
) -> dict:
    """Return only ownership-verified order facts for this request."""
    facts = ctx.context
    if (
        customer_id != facts.customer_id
        or order_id != facts.order_id
        or not facts.customer_found
        or not facts.order_found
        or not facts.order_belongs_to_customer
        or facts.validation_errors
    ):
        return {"authorized": False}
    return {
        "found": True,
        "authorized": True,
        "order_id": facts.order_id,
        "status": facts.order_status,
        "expected_delivery": facts.expected_delivery,
        "tracking_id": facts.tracking_id,
        "product_name": facts.verified_product_name,
    }


email_agent = Agent(
    name="Customer Email agent",
    model="gpt-4.1-mini",
    instructions="""
    You are an AI assistant for a B2B IT distributor.

    You receive a customer_id, email subject, and email body.

    You receive a customer email together with its extraction and a deterministic
    validation result. The validation result is the source of truth for customer and
    order facts.

    Your job:
    1. Use the supplied validation result for customer existence, order existence,
       ownership, and all verified business facts.
    2. Existing read tools remain available when useful, but they must never override
       validation. Always supply both order_id and customer_id to get_order.
    3. Apply the business rules.
    4. Choose the next action and whether human review is required.
    5. Generate the draft reply and return a structured decision.

    Business rules:
    - If customer is not found, requires_human_review=true and next_action="route_to_human_review".
    - If the email is order-related but no order_id is found, requires_human_review=false and next_action="ask_for_order_id".
    - If order is not found, requires_human_review=true and next_action="route_to_human_review".
    - If order exists but belongs to another customer, requires_human_review=true and next_action="route_to_human_review".
    - If order is delayed and customer is priority customer, requires_human_review=true and next_action="escalate_priority_customer_delay".
    - If order is delayed and customer is not priority customer, requires_human_review=false and next_action="send_delay_information_reply".
    - If order is in_transit and belongs to the customer, requires_human_review=false and next_action="send_delivery_status_reply".

    Important:
    - Preserve the supplied category, order_id, product_name, and internal_summary in the decision.
    - Do not invent delivery dates, tracking IDs, order status, customer name, or priority status.
    - The supplied validation result is the source of truth.
    - Never disclose or infer order details when order_belongs_to_customer is false.

  """,
  tools=[get_customer, get_order],
  output_type= AgentDecision
)


def analyze_email_with_agent(
    request: EmailAnalysisRequest,
    extraction: EmailExtraction,
    validation: ValidationResult,
) -> EmailAnalysisResponse:
    validation_context = validation.model_dump_json()
    prompt = f"""
    Customer ID:
    {request.customer_id}

    Email Subject:
    {request.email_subject}

    Email Body:
    {request.email_body}

    Extracted Category:
    {extraction.category}

    Extracted Order ID:
    {extraction.order_id}

    Extracted Product Name:
    {extraction.product_name}

    Internal Summary:
    {extraction.internal_summary}

    Deterministic Validation Result (authoritative):
    {validation_context}

    Use the supplied extraction and authoritative validation result to return a
    structured decision. Never expose order facts unless ownership is verified.
    """
    try:
        result = Runner.run_sync(email_agent, prompt, context=validation)
        decision = result.final_output
    except Exception as e:
        logger.exception("Error processing email request for customer_id: %s", request.customer_id)
        raise

    return EmailAnalysisResponse(
        category=decision.category,
        customer_id=request.customer_id,
        order_id=validation.order_id,
        product_name=validation.verified_product_name,
        priority_customer=validation.priority_customer,
        requires_human_review=decision.requires_human_review,
        next_action=decision.next_action,
        internal_summary=decision.internal_summary,
        draft_reply=decision.draft_reply,
    )
