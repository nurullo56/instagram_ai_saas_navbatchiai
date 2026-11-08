"""001_initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-11-08

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')
    op.execute('CREATE EXTENSION IF NOT EXISTS "vector";')

    # 2. current_tenant_id function (STABLE, no SECURITY DEFINER, search_path=pg_catalog,pg_temp)
    op.execute("""
    CREATE OR REPLACE FUNCTION current_tenant_id() RETURNS UUID AS $$
    BEGIN
        RETURN NULLIF(current_setting('app.current_tenant_id', true), '')::UUID;
    END;
    $$ LANGUAGE plpgsql STABLE SET search_path = pg_catalog, pg_temp;
    """)

    # 3. Tenants & Users
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), unique=True, nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("settings", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False),
    )
    op.create_index("idx_tenants_slug", "tenants", ["slug"])

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("is_superadmin", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False),
    )
    op.create_index("idx_users_email", "users", ["email"])

    op.create_table(
        "tenant_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(50), server_default="member", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False),
        sa.UniqueConstraint("tenant_id", "user_id", name="uq_tenant_membership"),
    )

    # 4. Plans & Subscriptions
    op.create_table(
        "plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(50), unique=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("price_cents", sa.Integer(), server_default="0", nullable=False),
        sa.Column("currency", sa.String(10), server_default="USD", nullable=False),
        sa.Column("max_instagram_accounts", sa.Integer(), server_default="1", nullable=False),
        sa.Column("max_monthly_messages", sa.Integer(), server_default="1000", nullable=False),
        sa.Column("max_ai_tokens", sa.Integer(), server_default="100000", nullable=False),
        sa.Column("max_flows", sa.Integer(), server_default="3", nullable=False),
        sa.Column("ai_features_enabled", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False),
    )

    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("plans.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.String(50), server_default="active", nullable=False),
        sa.Column("billing_cycle", sa.String(20), server_default="monthly", nullable=False),
        sa.Column("currency", sa.String(10), server_default="USD", nullable=False),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cancel_at_period_end", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False),
        sa.UniqueConstraint("tenant_id", "id", name="uq_subscriptions_tenant_id_composite"),
    )
    op.execute("""
    CREATE UNIQUE INDEX uq_tenant_single_active_subscription ON subscriptions (tenant_id)
        WHERE status IN ('trialing', 'active', 'past_due');
    """)

    op.create_table(
        "payment_transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subscription_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("provider_transaction_id", sa.String(255), nullable=False),
        sa.Column("provider_action", sa.String(50), server_default="payment", nullable=False),
        sa.Column("amount_minor_units", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False),
        sa.Column("status", sa.String(50), server_default="pending", nullable=False),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column("raw_callback_payload", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id", "subscription_id"],
            ["subscriptions.tenant_id", "subscriptions.id"],
            ondelete="RESTRICT",
            name="fk_payment_subscription"
        ),
        sa.UniqueConstraint("provider", "provider_transaction_id", "provider_action", name="uq_payment_provider_tx_action"),
        sa.UniqueConstraint("provider", "idempotency_key", name="uq_payment_provider_idempotency"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_payment_transactions_composite"),
        sa.CheckConstraint("amount_minor_units > 0", name="chk_positive_amount"),
    )

    op.create_table(
        "subscription_usage_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metric", sa.String(50), nullable=False),
        sa.Column("quantity", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False),
        sa.UniqueConstraint("tenant_id", "metric", "period_start", name="uq_tenant_usage_metric_period"),
    )

    # 5. Webhook Events & Outbox Events
    op.create_table(
        "webhook_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True),
        sa.Column("source", sa.String(50), server_default="meta", nullable=False),
        sa.Column("event_id", sa.String(255), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("status", sa.String(50), server_default="received", nullable=False),
        sa.Column("retry_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("max_retries", sa.Integer(), server_default="5", nullable=False),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column("lease_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("locked_by", sa.String(100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("source", "event_id", name="uq_webhook_source_event"),
    )
    op.create_index("idx_webhook_events_queue", "webhook_events", ["source", "status", "next_retry_at"])

    op.create_table(
        "outbox_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("destination", sa.String(50), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("status", sa.String(50), server_default="pending", nullable=False),
        sa.Column("retry_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("max_retries", sa.Integer(), server_default="5", nullable=False),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("locked_by", sa.String(100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "idempotency_key", name="uq_outbox_tenant_idempotency"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_outbox_events_composite"),
    )

    # 6. Instagram Accounts, Conversations, Messages
    op.create_table(
        "instagram_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ig_user_id", sa.String(100), nullable=False),
        sa.Column("page_id", sa.String(100), nullable=False),
        sa.Column("username", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("profile_picture_url", sa.Text(), nullable=True),
        sa.Column("encrypted_access_token", sa.Text(), nullable=False),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("webhook_subscribed", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False),
        sa.UniqueConstraint("tenant_id", "ig_user_id", name="uq_tenant_ig_account"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_instagram_accounts_composite"),
    )

    op.create_table(
        "conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("instagram_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ig_recipient_id", sa.String(100), nullable=False),
        sa.Column("recipient_username", sa.String(255), nullable=True),
        sa.Column("status", sa.String(50), server_default="open", nullable=False),
        sa.Column("mode", sa.String(50), server_default="bot", nullable=False),
        sa.Column("last_message_at", sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column("messaging_window_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("unread_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id", "instagram_account_id"],
            ["instagram_accounts.tenant_id", "instagram_accounts.id"],
            ondelete="RESTRICT",
            name="fk_conversations_account"
        ),
        sa.UniqueConstraint("tenant_id", "instagram_account_id", "ig_recipient_id", name="uq_conversation_recipient"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_conversations_composite"),
    )

    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mid", sa.String(255), unique=True, nullable=True),
        sa.Column("sender_type", sa.String(50), nullable=False),
        sa.Column("message_text", sa.Text(), nullable=True),
        sa.Column("media_url", sa.Text(), nullable=True),
        sa.Column("media_type", sa.String(50), nullable=True),
        sa.Column("status", sa.String(50), server_default="sent", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("raw_payload", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id", "conversation_id"],
            ["conversations.tenant_id", "conversations.id"],
            ondelete="RESTRICT",
            name="fk_messages_conversation"
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_messages_composite"),
    )

    # 7. Comment Logs
    op.create_table(
        "comment_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("instagram_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ig_comment_id", sa.String(100), nullable=False),
        sa.Column("ig_media_id", sa.String(100), nullable=False),
        sa.Column("ig_user_id", sa.String(100), nullable=False),
        sa.Column("comment_text", sa.Text(), nullable=False),
        sa.Column("ig_comment_created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("private_reply_status", sa.String(50), server_default="none", nullable=False),
        sa.Column("private_reply_text", sa.Text(), nullable=True),
        sa.Column("private_reply_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("private_reply_lease_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("private_reply_locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("private_reply_locked_by", sa.String(100), nullable=True),
        sa.Column("private_reply_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id", "instagram_account_id"],
            ["instagram_accounts.tenant_id", "instagram_accounts.id"],
            ondelete="RESTRICT",
            name="fk_comment_logs_account"
        ),
        sa.UniqueConstraint("tenant_id", "ig_comment_id", name="uq_tenant_comment"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_comment_logs_composite"),
    )

    # 8. Leads & Tags
    op.create_table(
        "leads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("instagram_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ig_recipient_id", sa.String(100), nullable=False),
        sa.Column("username", sa.String(255), nullable=True),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("phone_number", sa.String(50), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("stage", sa.String(50), server_default="new", nullable=False),
        sa.Column("custom_attributes", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id", "instagram_account_id"],
            ["instagram_accounts.tenant_id", "instagram_accounts.id"],
            ondelete="RESTRICT",
            name="fk_leads_account"
        ),
        sa.UniqueConstraint("tenant_id", "instagram_account_id", "ig_recipient_id", name="uq_leads_recipient"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_leads_composite"),
    )

    op.create_table(
        "lead_tags",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("color", sa.String(20), server_default="#6366F1", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False),
        sa.UniqueConstraint("tenant_id", "name", name="uq_lead_tag_name"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_lead_tags_composite"),
    )

    op.create_table(
        "lead_tag_mappings",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tag_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id", "lead_id"],
            ["leads.tenant_id", "leads.id"],
            ondelete="CASCADE",
            name="fk_mapping_lead"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "tag_id"],
            ["lead_tags.tenant_id", "lead_tags.id"],
            ondelete="CASCADE",
            name="fk_mapping_tag"
        ),
    )

    # 9. Flow Builder (Definitions, Versions, Executions)
    op.create_table(
        "flow_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("instagram_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("active_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id", "instagram_account_id"],
            ["instagram_accounts.tenant_id", "instagram_accounts.id"],
            ondelete="RESTRICT",
            name="fk_flow_account"
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_flow_definitions_composite"),
    )

    op.create_table(
        "flow_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("flow_definition_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("trigger_type", sa.String(100), nullable=False),
        sa.Column("trigger_config", postgresql.JSONB(), nullable=False),
        sa.Column("nodes", postgresql.JSONB(), nullable=False),
        sa.Column("edges", postgresql.JSONB(), nullable=False),
        sa.Column("is_published", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id", "flow_definition_id"],
            ["flow_definitions.tenant_id", "flow_definitions.id"],
            ondelete="RESTRICT",
            name="fk_flow_version_def"
        ),
        sa.UniqueConstraint("tenant_id", "flow_definition_id", "version_number", name="uq_flow_version_num"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_flow_versions_composite"),
    )

    op.create_table(
        "flow_executions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("flow_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("flow_definition_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("instagram_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recipient_id", sa.String(100), nullable=False),
        sa.Column("trigger_source", sa.String(50), server_default="webhook", nullable=False),
        sa.Column("trigger_event_id", sa.String(255), nullable=True),
        sa.Column("current_node_id", sa.String(100), nullable=True),
        sa.Column("context_data", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("status", sa.String(50), server_default="running", nullable=False),
        sa.Column("step_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["tenant_id", "instagram_account_id"],
            ["instagram_accounts.tenant_id", "instagram_accounts.id"],
            ondelete="RESTRICT",
            name="fk_flow_exec_account"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "conversation_id"],
            ["conversations.tenant_id", "conversations.id"],
            ondelete="RESTRICT",
            name="fk_flow_exec_conversation"
        ),
        sa.CheckConstraint(
            "((trigger_source = 'webhook' AND trigger_event_id IS NOT NULL) OR (trigger_source <> 'webhook'))",
            name="chk_webhook_trigger_id"
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_flow_executions_composite"),
    )
    op.execute("""
    CREATE UNIQUE INDEX uq_flow_exec_webhook_dedup ON flow_executions (tenant_id, flow_definition_id, trigger_event_id)
        WHERE trigger_source = 'webhook';
    CREATE UNIQUE INDEX uq_active_waiting_input_flow ON flow_executions (tenant_id, conversation_id)
        WHERE status = 'waiting_input';
    """)

    # 10. AI Knowledge Base
    op.create_table(
        "ai_agent_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("instagram_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("model_name", sa.String(100), server_default="meta-llama/llama-3.3-70b-instruct", nullable=False),
        sa.Column("system_prompt", sa.Text(), nullable=False),
        sa.Column("temperature", sa.Numeric(2, 1), server_default="0.7", nullable=False),
        sa.Column("max_tokens", sa.Integer(), server_default="350", nullable=False),
        sa.Column("lead_capture_enabled", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id", "instagram_account_id"],
            ["instagram_accounts.tenant_id", "instagram_accounts.id"],
            ondelete="RESTRICT",
            name="fk_ai_config_account"
        ),
        sa.UniqueConstraint("tenant_id", "instagram_account_id", name="uq_ai_config_account"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_ai_agent_configs_composite"),
    )

    op.create_table(
        "knowledge_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("storage_provider", sa.String(50), server_default="s3", nullable=False),
        sa.Column("storage_bucket", sa.String(100), nullable=True),
        sa.Column("storage_key", sa.String(500), nullable=True),
        sa.Column("file_name", sa.String(255), nullable=True),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("sha256_hash", sa.String(64), nullable=True),
        sa.Column("processing_status", sa.String(50), server_default="pending", nullable=False),
        sa.Column("error_details", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False),
        sa.UniqueConstraint("tenant_id", "id", name="uq_knowledge_sources_composite"),
    )

    op.create_table(
        "knowledge_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("embedding_provider", sa.String(50), server_default="openai", nullable=False),
        sa.Column("embedding_model", sa.String(100), server_default="text-embedding-3-small", nullable=False),
        sa.Column("embedding_dimension", sa.Integer(), server_default="1536", nullable=False),
        sa.Column("embedding", Vector(1536), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id", "source_id"],
            ["knowledge_sources.tenant_id", "knowledge_sources.id"],
            ondelete="CASCADE",
            name="fk_chunks_source"
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_knowledge_chunks_composite"),
        sa.CheckConstraint("embedding_dimension = 1536", name="chk_embedding_dimension_match"),
    )

    # 11. Audit Logs
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", sa.String(100), nullable=True),
        sa.Column("changes", postgresql.JSONB(), nullable=True),
        sa.Column("ip_address", sa.String(50), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False),
    )

    # 12. PostgreSQL Row-Level Security (RLS) Enablement
    tenant_tables = [
        "subscriptions", "payment_transactions", "subscription_usage_records",
        "instagram_accounts", "conversations", "messages", "comment_logs",
        "leads", "lead_tags", "lead_tag_mappings", "flow_definitions",
        "flow_versions", "flow_executions", "ai_agent_configs", "knowledge_sources",
        "knowledge_chunks", "audit_logs", "outbox_events"
    ]
    for tbl in tenant_tables:
        op.execute(f"ALTER TABLE {tbl} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {tbl} FORCE ROW LEVEL SECURITY;")
        op.execute(f"""
        CREATE POLICY rls_{tbl}_tenant_isolation ON {tbl}
            FOR ALL
            USING (tenant_id = current_tenant_id())
            WITH CHECK (tenant_id = current_tenant_id());
        """)


def downgrade() -> None:
    # Downgrade drops in reverse order
    pass
