from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app import workflow
from app.schemas import AgentDecision
from app.services import agent_service
from app.tools.customer import get_customer
from app.tools.order import get_order
from test_tools import invoke
from test_validation import make_request, make_extraction


def decision(order_id='77881', action='send_delivery_status_reply'):
    return AgentDecision(
        category='delivery_status_request', order_id=order_id,
        product_name='Invented product', priority_customer=False,
        requires_human_review=False, next_action=action,
        internal_summary='Test', draft_reply='Test reply',
    )


def simulate(monkeypatch, order_id, calls, output):
    monkeypatch.setattr(workflow, 'extract_email_details', lambda _: make_extraction(order_id))
    def run(agent, prompt, *, context):
        assert context.customer is None
        assert context.orders == {}
        assert 'DHL-' not in prompt
        assert {tool.name for tool in agent.tools} == {'get_customer', 'get_order'}
        for tool, arguments in calls:
            invoke(tool, context, **arguments)
        return SimpleNamespace(final_output=output)
    monkeypatch.setattr(agent_service.Runner, 'run_sync', run)


def test_workflow_uses_tool_evidence_not_model_facts(monkeypatch):
    simulate(monkeypatch, '77881', [(get_order, {'order_id': '77881'})], decision())
    result = workflow.analyze_email_workflow(make_request())
    assert result.order_id == '77881'
    assert result.product_name == 'Lenovo ThinkPad T14'
    assert result.priority_customer is True
    assert not result.requires_human_review


@pytest.mark.parametrize('customer_id,order_id', [
    ('C-999', '77881'), ('C-102', 'missing'), ('C-102', '99110'),
])
def test_api_unavailable_facts_fail_closed(monkeypatch, customer_id, order_id):
    simulate(monkeypatch, order_id, [(get_order, {'order_id': order_id})], decision(order_id))
    response = TestClient(app).post('/emails/analyze', json=make_request(customer_id).model_dump())
    assert response.status_code == 200
    assert response.json()['requires_human_review'] is True
    assert response.json()['order_id'] is None
    assert response.json()['product_name'] is None
    assert 'DHL-' not in response.text


@pytest.mark.parametrize('calls', [[], [(get_customer, {})]])
def test_skipped_order_lookup_cannot_pass(monkeypatch, calls):
    simulate(monkeypatch, '77881', calls, decision())
    result = workflow.analyze_email_workflow(make_request())
    assert result.next_action == 'route_to_human_review'
    assert result.draft_reply != 'Test reply'


def test_missing_order_id_can_ask_after_customer_lookup(monkeypatch):
    simulate(monkeypatch, None, [(get_customer, {})], decision(None, 'ask_for_order_id'))
    result = workflow.analyze_email_workflow(make_request())
    assert result.next_action == 'ask_for_order_id'
    assert result.order_id is None
    assert result.product_name is None


def test_order_action_without_order_evidence_fails(monkeypatch):
    simulate(monkeypatch, None, [(get_customer, {})], decision(None))
    assert workflow.analyze_email_workflow(make_request()).requires_human_review


def test_model_cannot_substitute_another_order(monkeypatch):
    simulate(monkeypatch, '77881', [(get_order, {'order_id': '77881'})], decision('99110'))
    assert workflow.analyze_email_workflow(make_request()).requires_human_review


def test_tool_database_failure_routes_to_review(monkeypatch):
    from sqlalchemy.exc import OperationalError
    def fail():
        raise OperationalError('private SQL', {}, Exception('private password'))
    monkeypatch.setattr('app.services.database.get_session_factory', fail)
    simulate(monkeypatch, '77881', [(get_order, {'order_id': '77881'})], decision())
    response = TestClient(app).post('/emails/analyze', json=make_request().model_dump())
    assert response.status_code == 200
    assert response.json()['requires_human_review']
    assert 'private' not in response.text
