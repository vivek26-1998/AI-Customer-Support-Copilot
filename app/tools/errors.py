from agents import RunContextWrapper
from agents.exceptions import ModelBehaviorError
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from ..db.session import DatabaseConfigurationError

from .context import SupportContext
from .schemas import ToolFailure

READ_ERRORS = (SQLAlchemyError, DatabaseConfigurationError, ValidationError)


def tool_error(ctx: RunContextWrapper[SupportContext], error: Exception) -> str:
    """Never return exception text, SQL, or credentials to the model."""
    ctx.context.mark_failed()
    outcome = 'invalid_input' if isinstance(error, ModelBehaviorError) else 'error'
    return ToolFailure(outcome=outcome).model_dump_json()


def unavailable(context: SupportContext) -> str:
    context.mark_failed()
    return ToolFailure(outcome='unavailable').model_dump_json()
