import asyncio
import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from agents.tool_context import ToolContext

from app.main import app
from app import workflow
from app.schemas import AgentDecision
from app.services import agent_service
from app.services.validation import validate_extraction
from test_validation import make_request, make_extraction


@pytest.mark.parametrize('customer_id,order_id', [
    ('C-999', '77881'), ('C-102', '00000'), ('C-102', '99110'),
])
def test_api_validation_failure_never_calls_decision_agent(monkeypatch, customer_id, order_id):
    monkeypatch.setattr(workflow, 'extract_email_details', lambda _: make_extraction(order_id))
    def forbidden(**kwargs):
        pytest.fail('Invalid facts reached decision agent')
    monkeypatch.setattr(workflow, 'analyze_email_with_agent', forbidden)
    response = TestClient(app).post('/emails/analyze', json=make_request(customer_id).model_dump())
    assert response.status_code == 200
    result = response.json()
    assert result['requires_human_review'] is True
    assert result['next_action'] == 'route_to_human_review'
    assert result['order_id'] is None
    assert result['product_name'] is None
    assert 'DHL-' not in response.text
    assert 'HP EliteBook' not in response.text


def test_inconsistent_record_routes_to_review(monkeypatch):
    monkeypatch.setattr(workflow, 'extract_email_details', lambda _: make_extraction('77881'))
    monkeypatch.setattr('app.services.validation.get_order_record', lambda _: {})
    monkeypatch.setattr(workflow, 'analyze_email_with_agent', lambda **_: pytest.fail('Agent called'))
    assert workflow.analyze_email_workflow(make_request()).requires_human_review


@pytest.mark.parametrize('order_id', ['77881', None])
def test_valid_context_reaches_agent_and_response_facts_are_authoritative(monkeypatch, order_id):
    extraction = make_extraction(order_id)
    monkeypatch.setattr(workflow, 'extract_email_details', lambda _: extraction)
    def fake_run(agent, prompt, *, context):
        assert context.customer_id == 'C-102'
        assert context.order_id == order_id
        assert {tool.name for tool in agent.tools} == {'get_customer', 'get_order'}
        return SimpleNamespace(final_output=AgentDecision(
            category=extraction.category, order_id='99110', product_name='Unverified',
            priority_customer=False, requires_human_review=False,
            next_action='ask_for_order_id' if order_id is None else 'send_delivery_status_reply',
            internal_summary='Test', draft_reply='Test draft',
        ))
    monkeypatch.setattr(agent_service.Runner, 'run_sync', fake_run)
    result = workflow.analyze_email_workflow(make_request())
    assert result.order_id == order_id
    assert result.priority_customer is True
    assert result.product_name == ('Lenovo ThinkPad T14' if order_id else None)


def invoke(tool, facts, **arguments):
    payload = json.dumps(arguments)
    context = ToolContext(context=facts, tool_name=tool.name,
                          tool_call_id="test-call", tool_arguments=payload)
    return asyncio.run(tool.on_invoke_tool(context, payload))


@pytest.mark.parametrize('customer_id,order_id', [
    ('C-205', '99110'), ('C-205', '77881'), ('C-102', '99110'), ('C-102', '00000'),
])
def test_order_tool_blocks_model_selected_identity(customer_id, order_id):
    facts = validate_extraction(make_request(), make_extraction('77881'))
    result = invoke(agent_service.get_order, facts, customer_id=customer_id, order_id=order_id)
    assert result == {'authorized': False}


def test_tools_return_only_verified_snapshot():
    facts = validate_extraction(make_request(), make_extraction('77881'))
    assert invoke(agent_service.get_customer, facts, customer_id='C-102')['priority_customer'] is True
    assert invoke(agent_service.get_customer, facts, customer_id='C-205') == {'authorized': False}
    order = invoke(agent_service.get_order, facts, customer_id='C-102', order_id='77881')
    assert order['tracking_id'] == facts.tracking_id
    assert set(order) == {'found', 'authorized', 'order_id', 'status', 'expected_delivery', 'tracking_id', 'product_name'}


@pytest.mark.parametrize('customer_id,order_id', [('C-999', '77881'), ('C-102', '99110'), ('C-102', None)])
def test_order_tool_denies_unverified_context(customer_id, order_id):
    facts = validate_extraction(make_request(customer_id), make_extraction(order_id))
    assert invoke(agent_service.get_order, facts, customer_id=customer_id, order_id=order_id or '77881') == {'authorized': False}


def test_customer_tool_denies_unknown_customer():
    facts = validate_extraction(make_request('C-999'), make_extraction(None))
    assert invoke(agent_service.get_customer, facts, customer_id='C-999') == {'authorized': False}


def test_missing_tool_arguments_return_no_business_facts():
    facts = validate_extraction(make_request(), make_extraction('77881'))
    result = invoke(agent_service.get_order, facts, order_id='77881')
    assert 'DHL-' not in str(result)
    assert 'Lenovo' not in str(result)


def test_api_database_failure_routes_to_review(monkeypatch):
    from sqlalchemy.exc import OperationalError
    monkeypatch.setattr(workflow, 'extract_email_details', lambda _: make_extraction('77881'))
    def unavailable(_):
        raise OperationalError('private SQL', {}, Exception('private database password'))
    monkeypatch.setattr('app.services.validation.get_order_record', unavailable)
    monkeypatch.setattr(workflow, 'analyze_email_with_agent', lambda **_: pytest.fail('Agent called'))
    response = TestClient(app).post('/emails/analyze', json=make_request().model_dump())
    assert response.status_code == 200
    assert response.json()['requires_human_review'] is True
    assert response.json()['order_id'] is None
    assert 'private' not in response.text
    assert 'DHL-' not in response.text
