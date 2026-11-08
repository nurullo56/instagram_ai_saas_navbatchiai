export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
}

export interface Tenant {
  id: string;
  name: string;
  slug: string;
  is_active: boolean;
}

export interface InstagramAccount {
  id: string;
  ig_user_id: string;
  page_id: string;
  username: string;
  name?: string;
  profile_picture_url?: string;
  token_expires_at: string;
  webhook_subscribed: boolean;
  is_active: boolean;
}

export interface Conversation {
  id: string;
  instagram_account_id: string;
  ig_recipient_id: string;
  recipient_username?: string;
  status: 'open' | 'resolved' | 'pending';
  mode: 'bot' | 'human_takeover' | 'ai_assistant';
  last_message_at: string;
  messaging_window_expires_at: string;
  unread_count: number;
}

export interface Message {
  id: string;
  conversation_id: string;
  mid?: string;
  sender_type: 'contact' | 'bot' | 'human_agent' | 'ai';
  message_text?: string;
  media_url?: string;
  media_type?: string;
  status: string;
  created_at: string;
}

export interface Lead {
  id: string;
  instagram_account_id: string;
  ig_recipient_id: string;
  username?: string;
  full_name?: string;
  phone_number?: string;
  email?: string;
  stage: 'new' | 'contacted' | 'qualified' | 'won' | 'lost';
  custom_attributes: Record<string, any>;
  notes?: string;
  created_at: string;
}

export interface FlowNode {
  id: string;
  type: 'trigger' | 'send_message' | 'comment_reply' | 'condition' | 'wait_delay' | 'ai_generate' | 'lead_tag' | 'handoff';
  data: Record<string, any>;
  position?: { x: number; y: number };
}

export interface FlowEdge {
  source: string;
  target: string;
  sourceHandle?: string;
}

export interface FlowDefinition {
  id: string;
  instagram_account_id: string;
  name: string;
  description?: string;
  is_active: boolean;
  active_version_id?: string;
  created_at: string;
}

export interface AIAgentConfig {
  id?: string;
  instagram_account_id: string;
  model_name: string;
  system_prompt: string;
  temperature: number;
  max_tokens: number;
  lead_capture_enabled: boolean;
  is_active: boolean;
}

export interface Plan {
  id: string;
  code: string;
  name: string;
  price_cents: number;
  currency: string;
  max_instagram_accounts: number;
  max_monthly_messages: number;
  max_ai_tokens: number;
  max_flows: number;
  ai_features_enabled: boolean;
}

export interface Subscription {
  id: string;
  plan_id: string;
  status: string;
  billing_cycle: string;
  currency: string;
  current_period_end: string;
}
