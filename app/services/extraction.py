from agents import Agent, Runner

from ..schemas import EmailAnalysisRequest, EmailExtraction


extraction_agent = Agent(
    name="Customer Email Extraction Agent",
    model="gpt-4.1-mini",
    instructions="""
    You extract structured information from customer emails for a B2B IT distributor.

    Classify the request into exactly one of these categories:
    - delivery_status_request
    - rma_request
    - invoice_issue
    - product_availability_request
    - quote_request
    - general_support

    Extract the order_id and product_name when present, and write a concise internal_summary.
    Do not validate customers or orders, apply business rules, make routing decisions, or
    generate a customer reply. Do not invent information that is not in the email.
    """,
    output_type=EmailExtraction,
)


def extract_email_details(request: EmailAnalysisRequest) -> EmailExtraction:
    prompt = f"""
    Email Subject:
    {request.email_subject}

    Email Body:
    {request.email_body}

    Classify this email and extract its structured details.
    """
    result = Runner.run_sync(extraction_agent, prompt)
    return result.final_output
