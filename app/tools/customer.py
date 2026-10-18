from agents import RunContextWrapper, function_tool

from ..db.repositories import SqlAlchemySupportRepository
from ..services import database
from .context import SupportContext
from .errors import READ_ERRORS, tool_error, unavailable
from .schemas import CustomerToolResult


@function_tool(failure_error_function=tool_error)
def get_customer(ctx: RunContextWrapper[SupportContext]) -> str:
    """Retrieve the current customer's verified profile. No customer ID argument."""
    try:
        with database.get_session_factory()() as session:
            customer = SqlAlchemySupportRepository(session).get_customer(ctx.context.customer_id)
    except READ_ERRORS as error:
        return tool_error(ctx, error)
    if customer is None:
        return unavailable(ctx.context)
    ctx.context.record_customer(customer)
    return CustomerToolResult(
        customer_id=customer.id, customer_name=customer.name,
        priority_customer=customer.priority_customer,
    ).model_dump_json()
