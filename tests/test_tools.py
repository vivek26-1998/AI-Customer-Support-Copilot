import asyncio
import json

import pytest
from agents.tool_context import ToolContext
from pydantic import ValidationError
from sqlalchemy.exc import OperationalError

from app.db.models import Order
from app.tools.context import SupportContext
from app.tools.customer import get_customer
from app.tools.order import get_order
from app.tools.schemas import ToolFailure


def invoke(tool, context, **arguments):
    payload = json.dumps(arguments)
    wrapped = ToolContext(context=context, tool_name=tool.name,
                          tool_call_id='test', tool_arguments=payload)
    return json.loads(asyncio.run(tool.on_invoke_tool(wrapped, payload)))


def test_customer_has_no_model_selected_identity():
    assert get_customer.params_json_schema['properties'] == {}
    assert set(get_order.params_json_schema['properties']) == {'order_id'}
    context = SupportContext(customer_id='C-102')
    result = invoke(get_customer, context)
    assert result['customer_id'] == 'C-102'
    assert result['priority_customer'] is True
    assert context.customer.id == 'C-102'
    with pytest.raises(ValidationError):
        context.customer_id = 'C-205'


def test_order_reads_database_and_records_verified_evidence(db_sessions):
    context = SupportContext(customer_id='C-102')
    with db_sessions.begin() as session:
        session.get(Order, '77881').status = 'delivered'
    result = invoke(get_order, context, order_id='77881')
    assert result['status'] == 'delivered'
    assert result['expected_delivery'] == '2026-06-25'
    assert 'customer_id' not in result
    assert context.orders['77881'].status == 'delivered'
    assert context.customer.id == 'C-102'


def test_unknown_and_foreign_orders_are_indistinguishable():
    results = []
    for order_id in ['missing', '99110']:
        context = SupportContext(customer_id='C-102')
        results.append(invoke(get_order, context, order_id=order_id))
        assert context.failed
        assert not context.orders
    assert results == [{'outcome': 'unavailable'}] * 2


def test_unknown_customer_cannot_read_orders():
    context = SupportContext(customer_id='missing')
    assert invoke(get_customer, context) == {'outcome': 'unavailable'}
    assert invoke(get_order, context, order_id='77881') == {'outcome': 'unavailable'}


@pytest.mark.parametrize('arguments', [{}, {'order_id': ''}, {'order_id': ' '},
                                      {'order_id': 123}, {'order_id': 'x' * 21}])
def test_invalid_order_arguments_fail_safely(arguments):
    context = SupportContext(customer_id='C-102')
    assert invoke(get_order, context, **arguments) == {'outcome': 'invalid_input'}
    assert context.failed
    assert not context.orders


@pytest.mark.parametrize('tool,arguments', [(get_customer, {}), (get_order, {'order_id': '77881'})])
def test_database_failure_is_sanitized(monkeypatch, tool, arguments):
    def fail():
        raise OperationalError('secret SQL', {}, Exception('secret password'))
    monkeypatch.setattr('app.services.database.get_session_factory', fail)
    context = SupportContext(customer_id='C-102')
    assert invoke(tool, context, **arguments) == {'outcome': 'error'}
    assert context.failed


def test_malformed_owned_record_fails_safely(db_sessions):
    with db_sessions.begin() as session:
        session.get(Order, '77881').product_name = ''
    context = SupportContext(customer_id='C-102')
    assert invoke(get_order, context, order_id='77881') == {'outcome': 'error'}
    assert not context.orders


def test_failure_contract_cannot_contain_business_facts():
    with pytest.raises(ValidationError):
        ToolFailure(outcome='unavailable', tracking_id='secret')


def test_run_evidence_is_not_shared():
    first = SupportContext(customer_id='C-102')
    second = SupportContext(customer_id='C-205')
    invoke(get_order, first, order_id='77881')
    assert second.customer is None
    assert second.orders == {}


def test_failure_remains_visible_after_success():
    context = SupportContext(customer_id='C-102')
    invoke(get_order, context, order_id='99110')
    invoke(get_order, context, order_id='77881')
    assert context.failed


def test_forged_customer_argument_cannot_expand_access():
    context = SupportContext(customer_id='C-102')
    result = invoke(get_order, context, order_id='99110', customer_id='C-205')
    assert result['outcome'] != 'success'
    assert context.customer_id == 'C-102'
    assert context.orders == {}


def test_repository_filters_ownership_before_parsing(db_sessions):
    from app.db.repositories import SqlAlchemySupportRepository
    with db_sessions.begin() as session:
        session.get(Order, '99110').product_name = ''
    with db_sessions() as session:
        repository = SqlAlchemySupportRepository(session)
        assert repository.get_order_for_customer('99110', 'C-102') is None
        assert repository.get_order_for_customer('missing', 'C-102') is None
        assert repository.get_order_for_customer('77881', 'C-102').id == '77881'


def test_tool_defends_against_repository_ownership_mismatch(monkeypatch):
    from app.db.schemas import OrderRecord
    foreign = OrderRecord(id='99110', customer_id='C-205', status='delayed',
                          expected_delivery=None, tracking_id='private', product_name='private')
    monkeypatch.setattr('app.db.repositories.SqlAlchemySupportRepository.get_order_for_customer',
                        lambda *args: foreign)
    context = SupportContext(customer_id='C-102')
    assert invoke(get_order, context, order_id='99110') == {'outcome': 'unavailable'}
    assert not context.orders


def test_nullable_order_fields_are_preserved(db_sessions):
    with db_sessions.begin() as session:
        order = session.get(Order, '77881')
        order.expected_delivery = None
        order.tracking_id = None
    result = invoke(get_order, SupportContext(customer_id='C-102'), order_id='77881')
    assert result['outcome'] == 'success'
    assert result['expected_delivery'] is None
    assert result['tracking_id'] is None
