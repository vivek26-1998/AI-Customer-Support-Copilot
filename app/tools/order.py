from agents import RunContextWrapper, function_tool

from ..db.repositories import SqlAlchemySupportRepository
from ..services import database
from ..services.validation import order_is_owned_by
from .context import SupportContext
from .errors import READ_ERRORS, tool_error, unavailable
from .schemas import OrderToolResult, ToolFailure


@function_tool(failure_error_function=tool_error)
def get_order(ctx: RunContextWrapper[SupportContext], order_id: str) -> str:
    """Retrieve an order belonging to the current customer; IDs are untrusted inputs."""
    if not order_id.strip() or order_id != order_id.strip() or len(order_id) > 20:
        ctx.context.mark_failed()
        return ToolFailure(outcome='invalid_input').model_dump_json()
    try:
        with database.get_session_factory()() as session:
            repository = SqlAlchemySupportRepository(session)
            customer = repository.get_customer(ctx.context.customer_id)
            if customer is None:
                return unavailable(ctx.context)
            order = repository.get_order_for_customer(order_id, ctx.context.customer_id)
    except READ_ERRORS as error:
        return tool_error(ctx, error)
    if order is None or not order_is_owned_by(order, ctx.context.customer_id):
        return unavailable(ctx.context)
    ctx.context.record_customer(customer)
    ctx.context.record_order(order)
    return OrderToolResult(
        order_id=order.id, status=order.status,
        expected_delivery=order.expected_delivery.isoformat() if order.expected_delivery else None,
        tracking_id=order.tracking_id, product_name=order.product_name,
    ).model_dump_json()
