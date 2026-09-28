from fastapi import FastAPI
from .schemas import EmailAnalysisRequest, EmailAnalysisResponse
from .workflow import analyze_email_workflow
app = FastAPI(title="customer Email MVP")
import logging
logging.basicConfig(level=logging.INFO) #to show logs at info level and above
logger = logging.getLogger(__name__)
@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/emails/analyze", response_model=EmailAnalysisResponse)
def analyze_email(request: EmailAnalysisRequest):
    logger.info("Received an email request for customer_id: %s", request.customer_id)
    try:
        return analyze_email_workflow(request)
    except Exception as e:
        logger.exception("Error processing email request for customer_id: %s", request.customer_id)
        raise

# @app.post("/emails/customer")
# def get_customer_info(request: EmailAnalysisRequest):
#     customer = get_customer_records(request.customer_id)
#     return {
#         "customer": customer is not None,
#         "customer_id": request.customer_id
#     }
