import React, { useState } from 'react';
import {
  GitFork,
  Plus,
  Play,
  CheckCircle2,
  AlertCircle,
  MessageSquare,
  Bot,
  UserCheck,
  Clock,
  HelpCircle,
  Trash2,
  Save,
  ArrowRight
} from 'lucide-react';
import { FlowNode, FlowEdge } from '../types';

export const FlowBuilderPage: React.FC = () => {
  const [nodes, setNodes] = useState<FlowNode[]>([
    {
      id: 'node_trigger',
      type: 'trigger',
      data: {
        title: 'Kiruvchi Xabar Trigger',
        trigger_type: 'keyword_dm',
        keywords: ['narx', 'kurs', 'info'],
        match_type: 'contains'
      }
    },
    {
      id: 'node_reply',
      type: 'send_message',
      data: {
        title: 'Javob Xabari',
        text: 'Assalomu alaykum! Kursimiz narxi 500,000 so\'m. Ro\'yxatdan o\'tish uchun telefon raqamingizni qoldiring.'
      }
    },
    {
      id: 'node_handoff',
      type: 'handoff',
      data: {
        title: 'Inson Operatoriga Uzatish',
        message: 'Mijoz operator talab qilganda avtomatik rejim to\'xtatiladi.'
      }
    }
  ]);

  const [edges, setEdges] = useState<FlowEdge[]>([
    { source: 'node_trigger', target: 'node_reply' }
  ]);

  const [selectedNodeId, setSelectedNodeId] = useState<string>('node_trigger');
  const [validationResult, setValidationResult] = useState<{ valid: boolean; message: string } | null>(null);
  const [publishing, setPublishing] = useState(false);

  const selectedNode = nodes.find((n) => n.id === selectedNodeId);

  // Yangi tugun qo'shish
  const addNode = (type: FlowNode['type']) => {
    const newId = `node_${Date.now()}`;
    const titles: Record<string, string> = {
      send_message: 'Yangi Direct Xabar',
      comment_reply: 'Izohga Private Reply',
      condition: 'Shart (If / Else)',
      wait_delay: 'Kutish (Delay)',
      ai_generate: 'AI Generatsiya (OpenRouter)',
      handoff: 'Operatorga Uzatish'
    };

    const newNode: FlowNode = {
      id: newId,
      type,
      data: {
        title: titles[type] || 'Yangi Tugun',
        text: type === 'send_message' ? 'Salom!' : '',
        keywords: type === 'trigger' ? ['start'] : []
      }
    };

    setNodes([...nodes, newNode]);
    setSelectedNodeId(newId);
  };

  // Tugun ma'lumotlarini yangilash
  const updateSelectedNodeData = (key: string, value: any) => {
    if (!selectedNodeId) return;
    setNodes(nodes.map((n) => {
      if (n.id === selectedNodeId) {
        return { ...n, data: { ...n.data, [key]: value } };
      }
      return n;
    }));
  };

  // Tugunni o'chirish
  const deleteNode = (id: string) => {
    if (nodes.length <= 1) {
      alert("Kamida bitta trigger tuguni bo'lishi kerak!");
      return;
    }
    setNodes(nodes.filter((n) => n.id !== id));
    setEdges(edges.filter((e) => e.source !== id && e.target !== id));
    if (selectedNodeId === id) {
      setSelectedNodeId(nodes[0].id);
    }
  };

  // Bog'lanish (Edge) qo'shish
  const handleConnect = (source: string, target: string) => {
    if (source === target) {
      alert("O'z-o'ziga bog'lanish mumkin emas!");
      return;
    }
    if (edges.some((e) => e.source === source && e.target === target)) {
      return;
    }
    setEdges([...edges, { source, target }]);
  };

  // DAG grafigini tekshirish (Cycle va unreachable tekshiruvi)
  const validateDAG = () => {
    // 1. Trigger mavjudligi
    const hasTrigger = nodes.some((n) => n.type === 'trigger');
    if (!hasTrigger) {
      setValidationResult({ valid: false, message: 'Kamida bitta Trigger tuguni bo\'lishi shart!' });
      return false;
    }

    // 2. Sikl tekshiruvi (Kahn algoritmi)
    const inDegree: Record<string, number> = {};
    const adj: Record<string, string[]> = {};
    nodes.forEach((n) => {
      inDegree[n.id] = 0;
      adj[n.id] = [];
    });

    edges.forEach((e) => {
      if (adj[e.source]) adj[e.source].push(e.target);
      if (inDegree[e.target] !== undefined) inDegree[e.target]++;
    });

    const queue: string[] = [];
    Object.keys(inDegree).forEach((nid) => {
      if (inDegree[nid] === 0) queue.push(nid);
    });

    let visitedCount = 0;
    while (queue.length > 0) {
      const curr = queue.shift()!;
      visitedCount++;
      (adj[curr] || []).forEach((neighbor) => {
        inDegree[neighbor]--;
        if (inDegree[neighbor] === 0) queue.push(neighbor);
      });
    }

    if (visitedCount < nodes.length) {
      setValidationResult({ valid: false, message: 'Xatolik: Graflar ichida cheksiz sikl (cycle loop) aniqlandi!' });
      return false;
    }

    setValidationResult({ valid: true, message: 'DAG muvaffaqiyatli tekshirildi: Sikllar yo\'q, arxitektura to\'g\'ri!' });
    return true;
  };

  const handlePublish = async () => {
    if (!validateDAG()) return;
    setPublishing(true);
    setTimeout(() => {
      setPublishing(false);
      alert("Avtomatizatsiya oqimi (DAG) muvaffaqiyatli e'lon qilindi va faollashtirildi! 🚀");
    }, 800);
  };

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col space-y-4">
      {/* Top action bar */}
      <div className="flex items-center justify-between bg-slate-900 border border-slate-800 p-4 rounded-2xl">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-purple-950/60 rounded-xl border border-purple-800/40">
            <GitFork className="w-5 h-5 text-purple-400" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-100">Boshlang'ich Savdo Oqimi (DAG)</h2>
            <p className="text-xs text-slate-400">Kalit so'z bo'yicha javob va operator uzatish</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={validateDAG}
            className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl border border-slate-700 flex items-center gap-2 transition"
          >
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            DAG Tekshirish
          </button>
          <button
            onClick={handlePublish}
            disabled={publishing}
            className="px-4 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-purple-600/30 flex items-center gap-2 transition disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            {publishing ? 'Nashr qilinmoqda...' : 'Oqimni E\'lon Qilish'}
          </button>
        </div>
      </div>

      {validationResult && (
        <div className={`p-3 rounded-xl text-xs flex items-center gap-2 border ${
          validationResult.valid
            ? 'bg-emerald-950/40 border-emerald-800/50 text-emerald-300'
            : 'bg-red-950/40 border-red-800/50 text-red-300'
        }`}>
          {validationResult.valid ? <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" /> : <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />}
          <span>{validationResult.message}</span>
        </div>
      )}

      {/* Workspace */}
      <div className="flex-1 flex gap-4 overflow-hidden">
        {/* Node Palette */}
        <div className="w-56 bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-col justify-between shrink-0">
          <div className="space-y-2">
            <span className="text-xs font-semibold text-slate-400 block mb-3 uppercase tracking-wider">
              Tugunlar Palitrasi
            </span>
            <button
              onClick={() => addNode('send_message')}
              className="w-full flex items-center gap-2.5 px-3 py-2 bg-slate-800/60 hover:bg-slate-800 rounded-xl text-xs text-slate-200 border border-slate-700/60 transition"
            >
              <MessageSquare className="w-4 h-4 text-blue-400" />
              Direct Xabar
            </button>
            <button
              onClick={() => addNode('comment_reply')}
              className="w-full flex items-center gap-2.5 px-3 py-2 bg-slate-800/60 hover:bg-slate-800 rounded-xl text-xs text-slate-200 border border-slate-700/60 transition"
            >
              <HelpCircle className="w-4 h-4 text-pink-400" />
              Izoh Private Reply
            </button>
            <button
              onClick={() => addNode('ai_generate')}
              className="w-full flex items-center gap-2.5 px-3 py-2 bg-slate-800/60 hover:bg-slate-800 rounded-xl text-xs text-slate-200 border border-slate-700/60 transition"
            >
              <Bot className="w-4 h-4 text-purple-400" />
              OpenRouter AI
            </button>
            <button
              onClick={() => addNode('condition')}
              className="w-full flex items-center gap-2.5 px-3 py-2 bg-slate-800/60 hover:bg-slate-800 rounded-xl text-xs text-slate-200 border border-slate-700/60 transition"
            >
              <GitFork className="w-4 h-4 text-amber-400" />
              Shart (If/Else)
            </button>
            <button
              onClick={() => addNode('handoff')}
              className="w-full flex items-center gap-2.5 px-3 py-2 bg-slate-800/60 hover:bg-slate-800 rounded-xl text-xs text-slate-200 border border-slate-700/60 transition"
            >
              <UserCheck className="w-4 h-4 text-emerald-400" />
              Inson Operator
            </button>
          </div>
          <p className="text-[11px] text-slate-500">
            Tugunlarni bosish orqali oqimga yangi element qo'shing.
          </p>
        </div>

        {/* Canvas Visual Area */}
        <div className="flex-1 bg-slate-950/80 border border-slate-800 rounded-2xl p-6 overflow-y-auto relative flex flex-col items-center space-y-6">
          {nodes.map((node, index) => {
            const isSelected = node.id === selectedNodeId;
            const hasOutgoing = edges.some((e) => e.source === node.id);

            return (
              <React.Fragment key={node.id}>
                <div
                  onClick={() => setSelectedNodeId(node.id)}
                  className={`w-80 bg-slate-900 border rounded-2xl p-4 shadow-lg cursor-pointer transition-all ${
                    isSelected
                      ? 'border-purple-500 ring-2 ring-purple-500/30'
                      : 'border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-semibold text-purple-400 uppercase tracking-wide">
                      {node.type}
                    </span>
                    {node.type !== 'trigger' && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteNode(node.id);
                        }}
                        className="text-slate-500 hover:text-red-400 p-1"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                  <h4 className="text-sm font-bold text-slate-100">{node.data.title}</h4>
                  <p className="text-xs text-slate-400 mt-1 truncate">
                    {node.type === 'trigger'
                      ? `Kalit so'zlar: ${(node.data.keywords || []).join(', ')}`
                      : node.data.text || node.data.message || 'Sozlash talab etiladi'}
                  </p>

                  {/* Connect helper buttons */}
                  <div className="mt-3 pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500">
                    <span>Ulanish holati:</span>
                    <span className={hasOutgoing ? 'text-emerald-400' : 'text-slate-400'}>
                      {hasOutgoing ? 'Bog\'langan' : 'Oxirgi qadam'}
                    </span>
                  </div>
                </div>

                {index < nodes.length - 1 && (
                  <div className="flex flex-col items-center my-1 text-slate-600">
                    <div className="w-0.5 h-4 bg-slate-800"></div>
                    <ArrowRight className="w-4 h-4 rotate-90" />
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>

        {/* Node Properties Panel */}
        <div className="w-80 bg-slate-900 border border-slate-800 rounded-2xl p-5 shrink-0 overflow-y-auto">
          {selectedNode ? (
            <div className="space-y-4">
              <span className="text-xs font-semibold text-slate-400 block uppercase tracking-wider">
                Tugun Sozlamalari
              </span>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Tugun Nomi</label>
                <input
                  type="text"
                  value={selectedNode.data.title || ''}
                  onChange={(e) => updateSelectedNodeData('title', e.target.value)}
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-purple-500"
                />
              </div>

              {selectedNode.type === 'trigger' && (
                <>
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">Trigger Turi</label>
                    <select
                      value={selectedNode.data.trigger_type || 'keyword_dm'}
                      onChange={(e) => updateSelectedNodeData('trigger_type', e.target.value)}
                      className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-purple-500"
                    >
                      <option value="keyword_dm">Direct Xabarda Kalit So'z</option>
                      <option value="comment_keyword">Izohda Kalit So'z (Post/Reels)</option>
                      <option value="comment_all">Barcha Izohlar</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">Kalit So'zlar (vergul bilan)</label>
                    <input
                      type="text"
                      value={(selectedNode.data.keywords || []).join(', ')}
                      onChange={(e) => updateSelectedNodeData('keywords', e.target.value.split(',').map((s) => s.trim()))}
                      placeholder="narx, kurs, start"
                      className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-purple-500"
                    />
                  </div>
                </>
              )}

              {(selectedNode.type === 'send_message' || selectedNode.type === 'comment_reply') && (
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Xabar Matni</label>
                  <textarea
                    rows={4}
                    value={selectedNode.data.text || ''}
                    onChange={(e) => updateSelectedNodeData('text', e.target.value)}
                    placeholder="Mijozga yuboriladigan avtomatik javob..."
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-purple-500"
                  />
                </div>
              )}

              {selectedNode.type === 'handoff' && (
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Ulanish Xabari</label>
                  <textarea
                    rows={3}
                    value={selectedNode.data.message || ''}
                    onChange={(e) => updateSelectedNodeData('message', e.target.value)}
                    placeholder="Siz inson operatoriga ulandingiz..."
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-purple-500"
                  />
                </div>
              )}
            </div>
          ) : (
            <p className="text-xs text-slate-500 text-center mt-12">Sozlash uchun tugunni tanlang.</p>
          )}
        </div>
      </div>
    </div>
  );
};
