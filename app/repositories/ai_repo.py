import uuid
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import select, update, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.ai_config import AIAgentConfig, KnowledgeSource, KnowledgeChunk
from app.repositories.base import BaseRepository


class AIRepository(BaseRepository[AIAgentConfig]):
    def __init__(self, session: AsyncSession, tenant_id: Optional[uuid.UUID] = None):
        super().__init__(AIAgentConfig, session, tenant_id=tenant_id)

    async def get_config_by_account(
        self,
        tenant_id: uuid.UUID,
        instagram_account_id: uuid.UUID
    ) -> Optional[AIAgentConfig]:
        """Instagram akkaunti uchun AI sozlamasini olish"""
        stmt = select(AIAgentConfig).where(
            AIAgentConfig.tenant_id == tenant_id,
            AIAgentConfig.instagram_account_id == instagram_account_id
        )
        res = await self.session.execute(stmt)
        return res.scalars().first()

    async def upsert_config(
        self,
        tenant_id: uuid.UUID,
        instagram_account_id: uuid.UUID,
        system_prompt: str,
        model_name: str = "meta-llama/llama-3.3-70b-instruct",
        temperature: float = 0.7,
        max_tokens: int = 350,
        lead_capture_enabled: bool = True,
        is_active: bool = True
    ) -> AIAgentConfig:
        """AI agent konfiguratsiyasini saqlash yoki yangilash"""
        config = await self.get_config_by_account(tenant_id, instagram_account_id)
        if config:
            config.system_prompt = system_prompt
            config.model_name = model_name
            config.temperature = temperature
            config.max_tokens = max_tokens
            config.lead_capture_enabled = lead_capture_enabled
            config.is_active = is_active
            await self.session.flush()
            return config

        config = AIAgentConfig(
            tenant_id=tenant_id,
            instagram_account_id=instagram_account_id,
            system_prompt=system_prompt,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            lead_capture_enabled=lead_capture_enabled,
            is_active=is_active
        )
        self.session.add(config)
        await self.session.flush()
        return config

    async def create_knowledge_source(
        self,
        tenant_id: uuid.UUID,
        title: str,
        source_type: str = "raw_text",
        file_name: Optional[str] = None,
        mime_type: Optional[str] = None
    ) -> KnowledgeSource:
        """Yangi bilim manbai (fayl yoki matn) yozuvini yaratish"""
        source = KnowledgeSource(
            tenant_id=tenant_id,
            title=title,
            source_type=source_type,
            file_name=file_name,
            mime_type=mime_type,
            processing_status="completed"
        )
        self.session.add(source)
        await self.session.flush()
        return source

    async def add_knowledge_chunk(
        self,
        tenant_id: uuid.UUID,
        source_id: uuid.UUID,
        chunk_index: int,
        content: str,
        embedding: List[float],
        token_count: int = 0
    ) -> KnowledgeChunk:
        """Vektor embedding bilan bilim bo'lagini (chunk) saqlash"""
        chunk = KnowledgeChunk(
            tenant_id=tenant_id,
            source_id=source_id,
            chunk_index=chunk_index,
            content=content,
            token_count=token_count or max(1, len(content) // 4),
            embedding_model="text-embedding-3-small",
            embedding_dimension=1536,
            embedding=embedding
        )
        self.session.add(chunk)
        await self.session.flush()
        return chunk

    async def search_similar_chunks(
        self,
        tenant_id: uuid.UUID,
        query_embedding: List[float],
        limit: int = 4
    ) -> List[Tuple[KnowledgeChunk, float]]:
        """
        pgvector orqali kosinus o'xshashlik bo'yicha eng mos bo'laklarni qidirish (RAG).
        Tenant izolyatsiyasi qat'iy ta'minlanadi.
        """
        stmt = (
            select(
                KnowledgeChunk,
                (1 - KnowledgeChunk.embedding.cosine_distance(query_embedding)).label("similarity")
            )
            .where(KnowledgeChunk.tenant_id == tenant_id)
            .order_by(KnowledgeChunk.embedding.cosine_distance(query_embedding).asc())
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        return [(row[0], float(row[1])) for row in res.all()]
