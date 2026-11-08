import pytest
from app.services.dag_validator import DAGValidator


def test_dag_validator_valid_flow():
    nodes = [
        {"id": "node_1", "type": "trigger", "data": {}},
        {"id": "node_2", "type": "send_message", "data": {"text": "Salom!"}},
        {"id": "node_3", "type": "handoff", "data": {}}
    ]
    edges = [
        {"source": "node_1", "target": "node_2"},
        {"source": "node_2", "target": "node_3"}
    ]

    is_valid, err = DAGValidator.validate_flow(nodes, edges)
    assert is_valid is True
    assert err is None


def test_dag_validator_cycle_detection():
    # A -> B -> C -> A sikli
    nodes = [
        {"id": "node_1", "type": "trigger", "data": {}},
        {"id": "node_2", "type": "send_message", "data": {}},
        {"id": "node_3", "type": "send_message", "data": {}}
    ]
    edges = [
        {"source": "node_1", "target": "node_2"},
        {"source": "node_2", "target": "node_3"},
        {"source": "node_3", "target": "node_1"}  # Sikl!
    ]

    is_valid, err = DAGValidator.validate_flow(nodes, edges)
    assert is_valid is False
    assert "sikl" in err.lower() or "cycle" in err.lower()


def test_dag_validator_missing_trigger():
    nodes = [
        {"id": "node_1", "type": "send_message", "data": {}}
    ]
    edges = []

    is_valid, err = DAGValidator.validate_flow(nodes, edges)
    assert is_valid is False
    assert "trigger" in err.lower()


def test_dag_validator_self_loop():
    nodes = [
        {"id": "node_1", "type": "trigger", "data": {}}
    ]
    edges = [
        {"source": "node_1", "target": "node_1"}
    ]

    is_valid, err = DAGValidator.validate_flow(nodes, edges)
    assert is_valid is False
    assert "taqiqlanadi" in err.lower()
