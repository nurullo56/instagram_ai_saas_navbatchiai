import React, { useState } from 'react';
import {
  MessageSquare,
  Clock,
  User,
  Send,
  AlertTriangle,
  Bot,
  UserCheck,
  Search,
  CheckCheck
} from 'lucide-react';
import { Conversation, Message } from '../types';

export const LiveInboxPage: React.FC = () => {
  const [conversations, setConversations] = useState<Conversation[]>([
    {
      id: 'conv-1',
      instagram_account_id: 'acc-1',
      ig_recipient_id: 'user_1001',
      recipient_username: 'anvar_dev',
      status: 'open',
      mode: 'bot',
      last_message_at: new Date(Date.now() - 25 * 60 * 1000).toISOString(),
      messaging_window_expires_at: new Date(Date.now() + 23 * 3600 * 1000).toISOString(),
      unread_count: 1
    },
    {
      id: 'conv-2',
      instagram_account_id: 'acc-1',
      ig_recipient_id: 'user_1002',
      recipient_username: 'dilshod_marketing',
      status: 'open',
      mode: 'human_takeover',
      last_message_at: new Date(Date.now() - 2 * 3600 * 1000).toISOString(),
      messaging_window_expires_at: new Date(Date.now() + 21 * 3600 * 1000).toISOString(),
      unread_count: 0
    },
    {
      id: 'conv-3',
      instagram_account_id: 'acc-1',
      ig_recipient_id: 'user_1003',
      recipient_username: 'malika_designer',
      status: 'open',
      mode: 'bot',
      last_message_at: new Date(Date.now() - 26 * 3600 * 1000).toISOString(),
      messaging_window_expires_at: new Date(Date.now() - 2 * 3600 * 1000).toISOString(), // 24h tugagan
      unread_count: 0
    }
  ]);

  const [selectedConvId, setSelectedConvId] = useState<string>('conv-1');
  const [replyText, setReplyText] = useState('');
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'msg-1',
      conversation_id: 'conv-1',
      sender_type: 'contact',
      message_text: 'Assalomu alaykum, kursingiz narxi qancha?',
      status: 'delivered',
      created_at: new Date(Date.now() - 25 * 60 * 1000).toISOString()
    },
    {
      id: 'msg-2',
      conversation_id: 'conv-1',
      sender_type: 'bot',
      message_text: 'Va alaykum assalom! Python va AI kursimiz 500,000 so\'m.',
      status: 'sent',
      created_at: new Date(Date.now() - 24 * 60 * 1000).toISOString()
    },
    {
      id: 'msg-3',
      conversation_id: 'conv-1',
      sender_type: 'contact',
      message_text: 'Operator bilan gaplashsam bo\'ladimi?',
      status: 'delivered',
      created_at: new Date(Date.now() - 5 * 60 * 1000).toISOString()
    }
  ]);

  const selectedConv = conversations.find((c) => c.id === selectedConvId);

  // 24 soatlik oynani hisoblash
  const isWindowActive = selectedConv
    ? new Date(selectedConv.messaging_window_expires_at).getTime() > Date.now()
    : false;

  // Inson operatoriga olish (Human Takeover) almashtirish
  const toggleTakeover = () => {
    if (!selectedConv) return;
    const newMode = selectedConv.mode === 'human_takeover' ? 'bot' : 'human_takeover';
    setConversations(conversations.map((c) => c.id === selectedConv.id ? { ...c, mode: newMode } : c));
  };

  const handleSendMessage = () => {
    if (!replyText.trim() || !selectedConv) return;
    const newMsg: Message = {
      id: `msg-${Date.now()}`,
      conversation_id: selectedConv.id,
      sender_type: selectedConv.mode === 'human_takeover' ? 'human_agent' : 'bot',
      message_text: replyText,
      status: 'sent',
      created_at: new Date().toISOString()
    };
    setMessages([...messages, newMsg]);
    setReplyText('');
  };

  return (
    <div className="h-[calc(100vh-8rem)] flex gap-4 overflow-hidden">
      {/* Conversations List (Left) */}
      <div className="w-80 bg-slate-900 border border-slate-800 rounded-2xl flex flex-col shrink-0 overflow-hidden">
        <div className="p-4 border-b border-slate-800">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
            <input
              type="text"
              placeholder="Suhbatlarni qidirish..."
              className="w-full pl-9 pr-3 py-1.5 bg-slate-800 border border-slate-700 rounded-xl text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-purple-500"
            />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto divide-y divide-slate-800/60">
          {conversations.map((conv) => {
            const isSelected = conv.id === selectedConvId;
            const windowOpen = new Date(conv.messaging_window_expires_at).getTime() > Date.now();

            return (
              <div
                key={conv.id}
                onClick={() => setSelectedConvId(conv.id)}
                className={`p-4 cursor-pointer transition ${
                  isSelected ? 'bg-purple-950/30 border-l-4 border-purple-500' : 'hover:bg-slate-800/40'
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-2">
                    <div className="w-7 h-7 rounded-full bg-slate-800 flex items-center justify-center font-bold text-xs text-purple-400">
                      @{conv.recipient_username?.[0].toUpperCase()}
                    </div>
                    <span className="text-xs font-semibold text-slate-200">
                      @{conv.recipient_username}
                    </span>
                  </div>
                  {conv.unread_count > 0 && (
                    <span className="w-5 h-5 bg-purple-600 rounded-full text-[10px] font-bold text-white flex items-center justify-center">
                      {conv.unread_count}
                    </span>
                  )}
                </div>

                <div className="flex items-center justify-between mt-2 text-[11px]">
                  <span className={`inline-flex items-center gap-1 ${
                    windowOpen ? 'text-emerald-400 font-medium' : 'text-red-400 font-medium'
                  }`}>
                    <Clock className="w-3 h-3" />
                    {windowOpen ? '24h Ochiq' : '24h Tugagan'}
                  </span>
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium border ${
                    conv.mode === 'human_takeover'
                      ? 'bg-emerald-950/60 text-emerald-300 border-emerald-800'
                      : 'bg-purple-950/60 text-purple-300 border-purple-800'
                  }`}>
                    {conv.mode === 'human_takeover' ? 'Operator' : 'Bot'}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Chat Thread Panel (Right) */}
      <div className="flex-1 bg-slate-900 border border-slate-800 rounded-2xl flex flex-col overflow-hidden">
        {selectedConv ? (
          <>
            {/* Thread Header */}
            <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/40">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-pink-500 to-purple-600 flex items-center justify-center font-bold text-white text-sm">
                  @{selectedConv.recipient_username?.[0].toUpperCase()}
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                    @{selectedConv.recipient_username}
                    <span className="text-[11px] font-mono text-slate-500">ID: {selectedConv.ig_recipient_id}</span>
                  </h3>
                  <div className="flex items-center gap-2 text-xs">
                    <span className={`flex items-center gap-1 ${isWindowActive ? 'text-emerald-400' : 'text-red-400'}`}>
                      <Clock className="w-3.5 h-3.5" />
                      {isWindowActive ? 'Meta 24-soatlik bepul oyna faol' : '24-soatlik oyna yopilgan'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Takeover button */}
              <button
                onClick={toggleTakeover}
                className={`px-3.5 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 border transition ${
                  selectedConv.mode === 'human_takeover'
                    ? 'bg-emerald-950/60 text-emerald-300 border-emerald-800 hover:bg-emerald-900/60'
                    : 'bg-slate-800 text-slate-200 border-slate-700 hover:bg-slate-700'
                }`}
              >
                {selectedConv.mode === 'human_takeover' ? (
                  <>
                    <UserCheck className="w-4 h-4 text-emerald-400" />
                    Operator Boshqaruvida (Bot o'chiq)
                  </>
                ) : (
                  <>
                    <Bot className="w-4 h-4 text-purple-400" />
                    Suhbatni Operatorga Olish
                  </>
                )}
              </button>
            </div>

            {/* Message Thread Body */}
            <div className="flex-1 p-6 overflow-y-auto space-y-4">
              {messages.map((m) => {
                const isContact = m.sender_type === 'contact';
                return (
                  <div
                    key={m.id}
                    className={`flex flex-col ${isContact ? 'items-start' : 'items-end'}`}
                  >
                    <div className="flex items-center gap-1.5 mb-1 text-[11px] text-slate-500">
                      <span>{isContact ? `@${selectedConv.recipient_username}` : m.sender_type === 'human_agent' ? 'Operator' : 'Bot'}</span>
                      <span>•</span>
                      <span>{new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    </div>
                    <div
                      className={`max-w-md p-3.5 rounded-2xl text-xs leading-relaxed ${
                        isContact
                          ? 'bg-slate-800 text-slate-200 border border-slate-700/80 rounded-tl-sm'
                          : m.sender_type === 'human_agent'
                          ? 'bg-emerald-600 text-white rounded-tr-sm shadow-md'
                          : 'bg-purple-600 text-white rounded-tr-sm shadow-md'
                      }`}
                    >
                      {m.message_text}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Reply Input Box */}
            <div className="p-4 border-t border-slate-800 bg-slate-950/60">
              {!isWindowActive && (
                <div className="mb-3 p-2 bg-amber-950/40 border border-amber-800/50 rounded-xl text-amber-300 text-xs flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
                  <span>Meta qoidasi: 24 soatdan oshgan suhbatlarga standart Direct xabar yuborish rad etiladi.</span>
                </div>
              )}
              <div className="flex items-center gap-3">
                <input
                  type="text"
                  value={replyText}
                  onChange={(e) => setReplyText(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                  placeholder={selectedConv.mode === 'human_takeover' ? 'Operator sifatida javob yozing...' : 'Bot rejimida qo\'lda xabar yuborish...'}
                  className="flex-1 px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-purple-500"
                />
                <button
                  onClick={handleSendMessage}
                  disabled={!replyText.trim()}
                  className="px-4 py-2.5 bg-purple-600 hover:bg-purple-500 text-white rounded-xl text-xs font-semibold flex items-center gap-2 shadow-lg shadow-purple-600/30 transition disabled:opacity-40"
                >
                  <Send className="w-4 h-4" />
                  Yuborish
                </button>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-slate-500 text-xs">
            Suhbatni tanlang
          </div>
        )}
      </div>
    </div>
  );
};
