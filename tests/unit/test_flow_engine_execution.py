import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from app.models.flow import FlowDefinition, FlowVersion, FlowExecution
from app.services.flow_engine import FlowEngine
from app.repositories.flow_repo import FlowRepository
from app.repositories.conversation_repo import ConversationRepository


@pytest.mark.asyncio
async def test_flow_engine_execution_send_message_and_complete():
    """
    Tugunlar bo'yicha ketma-ket harakatlanish:
    trigger -> send_message -> tugash (completed)
    """
    mock_session = AsyncMock()
    engine = FlowEngine(mock_session)

    tenant_id = uuid.uuid4()
    exec_id = uuid.uuid4()
    ver_id = uuid.uuid4()
    account_id = uuid.uuid4()
    conv_id = uuid.uuid4()

    execution = FlowExecution(
        id=exec_id,
        tenant_id=tenant_id,
        flow_version_id=ver_id,
        flow_definition_id=uuid.uuid4(),
        instagram_account_id=account_id,
        conversation_id=conv_id,
        recipient_id="user_123",
        status="running",
        step_count=0,
        current_node_id=None
    )

    version = FlowVersion(
        id=ver_id,
        tenant_id=tenant_id,
        flow_definition_id=execution.flow_definition_id,
        version_number=1,
        trigger_type="keyword_dm",
        trigger_config={},
        nodes=[
            {"id": "node_1", "type": "trigger", "data": {}},
            {"id": "node_2", "type": "send_message", "data": {"text": "Salom! Xush kelibsiz!"}}
        ],
        edges=[
            {"source": "node_1", "target": "node_2"}
        ],
        is_published=True
    )

    with patch("app.repositories.outbox_repo.OutboxRepository.enqueue", return_value=MagicMock()) as mock_outbox, \
         patch.object(FlowRepository, "update_execution_step", return_value=True) as mock_update_step:

        mock_session.execute.side_effect = [
            MagicMock(scalars=lambda: MagicMock(first=lambda: execution)),
            MagicMock(scalars=lambda: MagicMock(first=lambda: version))
        ]

        result = await engine.execute_flow(tenant_id, exec_id)

        assert result["status"] == "completed"
        assert result["steps_executed"] == 2
        mock_outbox.assert_called_once()
        mock_update_step.assert_called_once()
        assert mock_update_step.call_args[1]["status"] == "completed"


@pytest.mark.asyncio
async def test_flow_engine_condition_branching():
    """
    Condition tuguni kontekstdagi o'zgaruvchiga qarab to'g'ri shoxchani (true/false) tanlaydi.
    """
    mock_session = AsyncMock()
    engine = FlowEngine(mock_session)

    tenant_id = uuid.uuid4()
    exec_id = uuid.uuid4()
    ver_id = uuid.uuid4()

    execution = FlowExecution(
        id=exec_id,
        tenant_id=tenant_id,
        flow_version_id=ver_id,
        flow_definition_id=uuid.uuid4(),
        instagram_account_id=uuid.uuid4(),
        conversation_id=uuid.uuid4(),
        recipient_id="user_123",
        status="running",
        step_count=0,
        context_data={"user_type": "vip"}  # VIP mijoz
    )

    version = FlowVersion(
        id=ver_id,
        tenant_id=tenant_id,
        flow_definition_id=execution.flow_definition_id,
        version_number=1,
        trigger_type="keyword_dm",
        trigger_config={},
        nodes=[
            {"id": "node_1", "type": "trigger", "data": {}},
            {"id": "node_cond", "type": "condition", "data": {"field": "user_type", "value": "vip"}},
            {"id": "node_vip", "type": "send_message", "data": {"text": "VIP chegirma siz uchun!"}},
            {"id": "node_standard", "type": "send_message", "data": {"text": "Standart narx."}}
        ],
        edges=[
            {"source": "node_1", "target": "node_cond"},
            {"source": "node_cond", "target": "node_vip", "sourceHandle": "true"},
            {"source": "node_cond", "target": "node_standard", "sourceHandle": "false"}
        ],
        is_published=True
    )

    with patch("app.repositories.outbox_repo.OutboxRepository.enqueue", return_value=MagicMock()) as mock_outbox, \
         patch.object(FlowRepository, "update_execution_step", return_value=True):

        mock_session.execute.side_effect = [
            MagicMock(scalars=lambda: MagicMock(first=lambda: execution)),
            MagicMock(scalars=lambda: MagicMock(first=lambda: version))
        ]

        result = await engine.execute_flow(tenant_id, exec_id)

        assert result["status"] == "completed"
        # VIP xabari yuborilganligini tasdiqlash
        mock_outbox.assert_called_once()
        assert "VIP" in mock_outbox.call_args[1]["payload"]["text"]


@pytest.mark.asyncio
async def test_flow_engine_handoff_node():
    """
    Handoff tuguniga yetganda suhbat rejimi human_takeover ga o'tadi va ijro yakunlanadi.
    """
    mock_session = AsyncMock()
    engine = FlowEngine(mock_session)

    tenant_id = uuid.uuid4()
    exec_id = uuid.uuid4()
    ver_id = uuid.uuid4()
    conv_id = uuid.uuid4()

    execution = FlowExecution(
        id=exec_id,
        tenant_id=tenant_id,
        flow_version_id=ver_id,
        flow_definition_id=uuid.uuid4(),
        instagram_account_id=uuid.uuid4(),
        conversation_id=conv_id,
        recipient_id="user_123",
        status="running",
        step_count=0
    )

    version = FlowVersion(
        id=ver_id,
        tenant_id=tenant_id,
        flow_definition_id=execution.flow_definition_id,
        version_number=1,
        trigger_type="keyword_dm",
        trigger_config={},
        nodes=[
            {"id": "node_1", "type": "trigger", "data": {}},
            {"id": "node_handoff", "type": "handoff", "data": {"message": "Operatorga ulandik."}}
        ],
        edges=[
            {"source": "node_1", "target": "node_handoff"}
        ],
        is_published=True
    )

    with patch.object(ConversationRepository, "set_mode", return_value=True) as mock_set_mode, \
         patch("app.repositories.outbox_repo.OutboxRepository.enqueue", return_value=MagicMock()) as mock_outbox, \
         patch.object(FlowRepository, "update_execution_step", return_value=True):

        mock_session.execute.side_effect = [
            MagicMock(scalars=lambda: MagicMock(first=lambda: execution)),
            MagicMock(scalars=lambda: MagicMock(first=lambda: version))
        ]

        result = await engine.execute_flow(tenant_id, exec_id)

        assert result["status"] == "completed"
        assert result["action"] == "handoff"
        mock_set_mode.assert_called_once_with(tenant_id, conv_id, "human_takeover")
        mock_outbox.assert_called_once()
