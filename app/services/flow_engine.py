import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.logging import logger
from app.models.flow import FlowDefinition, FlowVersion, FlowExecution
from app.models.conversation import Conversation
from app.repositories.flow_repo import FlowRepository
from app.repositories.outbox_repo import OutboxRepository
from app.repositories.conversation_repo import ConversationRepository
from app.services.dag_validator import DAGValidator


class FlowEngine:
    """
    Visual Flow Builder DAG ijro dvigateli:
    - Tugunma-tugun graflar bo'yicha harakatlanish
    - Xabarlar (send_message), shartlar (condition), teglar (lead_tag), inson operatori (handoff)
    - Kontekst ma'lumotlarini (variables) saqlash va uzatish
    - Cheksiz aylanmalardan himoya (Max steps limit)
    """

    MAX_STEPS = 50

    def __init__(self, session: AsyncSession):
        self.session = session

    async def execute_flow(
        self,
        tenant_id: uuid.UUID,
        execution_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Flow ijrosini davom ettirish yoki yakunlash.
        """
        flow_repo = FlowRepository(self.session, tenant_id=tenant_id)
        outbox_repo = OutboxRepository(self.session, tenant_id=tenant_id)
        conv_repo = ConversationRepository(self.session, tenant_id=tenant_id)

        # 1. Execution yozuvini olish
        stmt_exec = select(FlowExecution).where(
            FlowExecution.tenant_id == tenant_id,
            FlowExecution.id == execution_id
        )
        execution = (await self.session.execute(stmt_exec)).scalars().first()
        if not execution or execution.status not in ("running", "waiting_input"):
            return {"status": "skipped", "reason": "Execution not found or not active"}

        # 2. Versiyani olish
        stmt_ver = select(FlowVersion).where(
            FlowVersion.tenant_id == tenant_id,
            FlowVersion.id == execution.flow_version_id
        )
        version = (await self.session.execute(stmt_ver)).scalars().first()
        if not version:
            await flow_repo.update_execution_step(
                tenant_id, execution_id, execution.current_node_id, "failed", execution.step_count,
                error_message="Flow version not found"
            )
            await self.session.commit()
            return {"status": "failed", "reason": "Flow version not found"}

        nodes_map = {node["id"]: node for node in version.nodes}
        edges = version.edges
        context = dict(execution.context_data or {})
        current_node_id = execution.current_node_id
        step_count = execution.step_count

        # Agar boshlang'ich node belgilanmagan bo'lsa, trigger nodedan boshlaymiz
        if not current_node_id:
            for node in version.nodes:
                if node.get("type") == "trigger":
                    current_node_id = node["id"]
                    break

        # 3. Qadamlar bo'yicha ijro qilish
        while current_node_id and step_count < self.MAX_STEPS:
            current_node = nodes_map.get(current_node_id)
            if not current_node:
                break

            step_count += 1
            node_type = current_node.get("type")
            node_data = current_node.get("data", {})

            logger.info("Flow node ijro qilinmoqda", node_id=current_node_id, type=node_type, step=step_count)

            # Tugun mantig'i
            if node_type == "send_message":
                text = node_data.get("text")
                if text:
                    await outbox_repo.enqueue(
                        tenant_id=tenant_id,
                        destination="meta_api",
                        event_type="direct_message",
                        idempotency_key=f"flow:{tenant_id}:{execution.id}:{current_node_id}:{step_count}",
                        payload={
                            "instagram_account_id": str(execution.instagram_account_id),
                            "recipient_id": execution.recipient_id,
                            "text": text,
                            "conversation_id": str(execution.conversation_id)
                        }
                    )

            elif node_type == "handoff":
                await conv_repo.set_mode(tenant_id, execution.conversation_id, "human_takeover")
                msg = node_data.get("message") or "Siz inson operatoriga ulandingiz. 👨‍💼"
                await outbox_repo.enqueue(
                    tenant_id=tenant_id,
                    destination="meta_api",
                    event_type="direct_message",
                    idempotency_key=f"flow_handoff:{tenant_id}:{execution.id}:{current_node_id}",
                    payload={
                        "instagram_account_id": str(execution.instagram_account_id),
                        "recipient_id": execution.recipient_id,
                        "text": msg,
                        "conversation_id": str(execution.conversation_id)
                    }
                )
                await flow_repo.update_execution_step(
                    tenant_id, execution_id, current_node_id, "completed", step_count, context
                )
                await self.session.commit()
                return {"status": "completed", "action": "handoff"}

            # Keyingi nodedi topish
            next_node_id = self._get_next_node_id(current_node_id, node_type, node_data, edges, context)
            current_node_id = next_node_id

        # 4. Yakunlash
        final_status = "completed" if not current_node_id else "failed"
        err = "Max steps limit reached" if step_count >= self.MAX_STEPS else None

        await flow_repo.update_execution_step(
            tenant_id=tenant_id,
            execution_id=execution_id,
            current_node_id=current_node_id,
            status=final_status,
            step_count=step_count,
            context_data=context,
            error_message=err
        )
        await self.session.commit()
        return {
            "status": final_status,
            "steps_executed": step_count,
            "error": err
        }

    def _get_next_node_id(
        self,
        current_node_id: str,
        node_type: str,
        node_data: Dict[str, Any],
        edges: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> Optional[str]:
        """Edge va shartlar bo'yicha keyingi tugunni aniqlash"""
        outgoing_edges = [e for e in edges if e.get("source") == current_node_id]
        if not outgoing_edges:
            return None

        # Agar condition bo'lsa, shartni baholaymiz
        if node_type == "condition":
            field = node_data.get("field")
            expected_val = node_data.get("value")
            actual_val = context.get(field)
            condition_met = str(actual_val).lower() == str(expected_val).lower()

            target_handle = "true" if condition_met else "false"
            for edge in outgoing_edges:
                if edge.get("sourceHandle") == target_handle:
                    return edge.get("target")

        # Standart ketma-ketlik
        return outgoing_edges[0].get("target")
