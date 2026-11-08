import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.flow import FlowDefinition, FlowVersion, FlowExecution
from app.repositories.base import BaseRepository


class FlowRepository(BaseRepository[FlowDefinition]):
    def __init__(self, session: AsyncSession, tenant_id: Optional[uuid.UUID] = None):
        super().__init__(FlowDefinition, session, tenant_id=tenant_id)

    async def create_flow(
        self,
        tenant_id: uuid.UUID,
        instagram_account_id: uuid.UUID,
        name: str,
        description: Optional[str] = None
    ) -> FlowDefinition:
        """Yangi oqim (flow) yaratish"""
        flow = FlowDefinition(
            tenant_id=tenant_id,
            instagram_account_id=instagram_account_id,
            name=name,
            description=description,
            is_active=False
        )
        self.session.add(flow)
        await self.session.flush()
        return flow

    async def create_version(
        self,
        tenant_id: uuid.UUID,
        flow_definition_id: uuid.UUID,
        version_number: int,
        trigger_type: str,
        trigger_config: Dict[str, Any],
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]]
    ) -> FlowVersion:
        """Flow versiyasini saqlash"""
        version = FlowVersion(
            tenant_id=tenant_id,
            flow_definition_id=flow_definition_id,
            version_number=version_number,
            trigger_type=trigger_type,
            trigger_config=trigger_config,
            nodes=nodes,
            edges=edges,
            is_published=False
        )
        self.session.add(version)
        await self.session.flush()
        return version

    async def publish_version(
        self,
        tenant_id: uuid.UUID,
        flow_definition_id: uuid.UUID,
        version_id: uuid.UUID
    ) -> bool:
        """
        Versiyani nashr qilish (publish):
        - Ushbu versiyani published qilish
        - Flow ta'rifidagi active_version_id ni ushbu versiyaga yo'naltirish
        - Flow ni faollashtirish (is_active = True)
        """
        # Versiyani nashr qilish
        stmt_ver = (
            update(FlowVersion)
            .where(
                FlowVersion.tenant_id == tenant_id,
                FlowVersion.id == version_id,
                FlowVersion.flow_definition_id == flow_definition_id
            )
            .values(is_published=True)
        )
        await self.session.execute(stmt_ver)

        # Asosiy ta'rifni yangilash
        stmt_flow = (
            update(FlowDefinition)
            .where(
                FlowDefinition.tenant_id == tenant_id,
                FlowDefinition.id == flow_definition_id
            )
            .values(active_version_id=version_id, is_active=True)
        )
        res = await self.session.execute(stmt_flow)
        return res.rowcount > 0

    async def get_published_version(
        self,
        tenant_id: uuid.UUID,
        flow_definition_id: uuid.UUID
    ) -> Optional[FlowVersion]:
        """Flow ning faol va nashr etilgan versiyasini olish"""
        stmt = (
            select(FlowVersion)
            .join(FlowDefinition, FlowDefinition.active_version_id == FlowVersion.id)
            .where(
                FlowDefinition.tenant_id == tenant_id,
                FlowDefinition.id == flow_definition_id,
                FlowDefinition.is_active.is_(True),
                FlowVersion.is_published.is_(True)
            )
        )
        res = await self.session.execute(stmt)
        return res.scalars().first()

    async def create_execution(
        self,
        tenant_id: uuid.UUID,
        flow_version_id: uuid.UUID,
        flow_definition_id: uuid.UUID,
        instagram_account_id: uuid.UUID,
        conversation_id: uuid.UUID,
        recipient_id: str,
        trigger_source: str = "webhook",
        trigger_event_id: Optional[str] = None,
        initial_node_id: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None
    ) -> Optional[FlowExecution]:
        """
        Flow ijrosini (Execution) boshlash.
        Webhook trigger deduplication indeksiga asosan bitta event qayta ijro qilinmaydi.
        """
        stmt = (
            insert(FlowExecution)
            .values(
                tenant_id=tenant_id,
                flow_version_id=flow_version_id,
                flow_definition_id=flow_definition_id,
                instagram_account_id=instagram_account_id,
                conversation_id=conversation_id,
                recipient_id=recipient_id,
                trigger_source=trigger_source,
                trigger_event_id=trigger_event_id,
                current_node_id=initial_node_id,
                context_data=context_data or {},
                status="running",
                step_count=0
            )
            .on_conflict_do_nothing(
                index_elements=["tenant_id", "flow_definition_id", "trigger_event_id"]
            )
            .returning(FlowExecution)
        )
        res = await self.session.execute(stmt)
        return res.scalars().first()

    async def update_execution_step(
        self,
        tenant_id: uuid.UUID,
        execution_id: uuid.UUID,
        current_node_id: Optional[str],
        status: str,
        step_count: int,
        context_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """Ijro qadamini va holatini yangilash"""
        values: Dict[str, Any] = {
            "current_node_id": current_node_id,
            "status": status,
            "step_count": step_count,
            "error_message": error_message
        }
        if status in ("completed", "failed"):
            values["completed_at"] = datetime.now(timezone.utc)
        if context_data is not None:
            values["context_data"] = context_data

        stmt = (
            update(FlowExecution)
            .where(
                FlowExecution.tenant_id == tenant_id,
                FlowExecution.id == execution_id
            )
            .values(**values)
        )
        res = await self.session.execute(stmt)
        return res.rowcount > 0
