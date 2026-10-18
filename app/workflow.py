from .schemas import EmailAnalysisRequest, EmailAnalysisResponse
from .services.agent_service import analyze_email_with_agent
from .services.extraction import extract_email_details
from .tools.context import SupportContext


ORDER_ACTIONS = {
    'send_delivery_status_reply', 'send_delay_information_reply',
    'escalate_priority_customer_delay',
}


def review_response(request: EmailAnalysisRequest, category: str) -> EmailAnalysisResponse:
    return EmailAnalysisResponse(
        category=category, customer_id=request.customer_id,
        order_id=None, product_name=None, priority_customer=False,
        requires_human_review=True, next_action='route_to_human_review',
        internal_summary='Required business facts could not be verified; human review required.',
        draft_reply='We could not verify the details of your request. Our support team will review it.',
    )


def analyze_email_workflow(request: EmailAnalysisRequest) -> EmailAnalysisResponse:
    extraction = extract_email_details(request)
    if not request.customer_id.strip() or len(request.customer_id) > 20:
        return review_response(request, extraction.category)
    context = SupportContext(customer_id=request.customer_id)
    decision = analyze_email_with_agent(request, extraction, context)

    # Check tool evidence, not model assertions. Full business policy is Phase 7.
    requested_order_id = extraction.order_id or decision.order_id
    order = context.orders.get(requested_order_id) if requested_order_id else None
    if (
        context.failed
        or context.customer is None
        or (requested_order_id is not None and order is None)
        or (decision.order_id is not None and decision.order_id != requested_order_id)
        or (decision.next_action in ORDER_ACTIONS and order is None)
    ):
        return review_response(request, extraction.category)

    return EmailAnalysisResponse(
        category=extraction.category, customer_id=request.customer_id,
        order_id=order.id if order else None,
        product_name=order.product_name if order else None,
        priority_customer=context.customer.priority_customer,
        requires_human_review=decision.requires_human_review,
        next_action=decision.next_action,
        internal_summary=decision.internal_summary, draft_reply=decision.draft_reply,
    )
