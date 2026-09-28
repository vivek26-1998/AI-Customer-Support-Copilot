from .schemas import EmailAnalysisRequest, EmailAnalysisResponse
from .services.agent_service import analyze_email_with_agent
from .services.extraction import extract_email_details
from .services.validation import validate_extraction


def analyze_email_workflow(request: EmailAnalysisRequest) -> EmailAnalysisResponse:
    extraction = extract_email_details(request)
    validation = validate_extraction(request, extraction)
    if validation.validation_errors or not validation.customer_found:
        return EmailAnalysisResponse(
            category=extraction.category,
            customer_id=request.customer_id,
            order_id=None,
            product_name=None,
            priority_customer=validation.priority_customer,
            requires_human_review=True,
            next_action="route_to_human_review",
            internal_summary="Business record validation failed; human review required.",
            draft_reply="We could not verify the details of your request. Our support team will review it.",
        )
    return analyze_email_with_agent(
        request=request,
        extraction=extraction,
        validation=validation,
    )
