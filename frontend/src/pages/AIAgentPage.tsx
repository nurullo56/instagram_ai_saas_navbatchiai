import React, { useState } from 'react';
import {
  Bot,
  Sparkles,
  Sliders,
  Database,
  Save,
  CheckCircle2,
  FileText,
  UploadCloud,
  ShieldAlert
} from 'lucide-react';

export const AIAgentPage: React.FC = () => {
  const [model, setModel] = useState('meta-llama/llama-3.3-70b-instruct');
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(350);
  const [leadCapture, setLeadCapture] = useState(true);
  const [isActive, setIsActive] = useState(true);
  const [systemPrompt, setSystemPrompt] = useState(
    "Siz IT Academy o'quv markazining do'stona va professional savdo bo'yicha AI yordamchisisiz.\n" +
    "Vazifangiz: Mijozlarga Python, AI va Web dasturlash kurslari haqida to'liq ma'lumot berish, narxlarni tushuntirish va ro'yxatdan o'tish uchun ularning ism-familiyasi hamda telefon raqamini olish.\n" +
    "Cheklovlar: Faqat o'quv markazi xizmatlari haqida gapiring. Instagram Direct uchun javoblaringiz ixcham va 300 belgidan oshmasin."
  );

  const [faqTitle, setFaqTitle] = useState('');
  const [faqContent, setFaqContent] = useState('');
  const [knowledgeList, setKnowledgeList] = useState([
    { id: '1', title: 'Kurslar Narxlari va Davomiyligi', type: 'FAQ Matni', date: 'Bugun' },
    { id: '2', title: 'Manzil va Filiallar', type: 'FAQ Matni', date: 'Kecha' }
  ]);
  const [saved, setSaved] = useState(false);

  const handleSaveConfig = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleAddKnowledge = (e: React.FormEvent) => {
    e.preventDefault();
    if (!faqTitle || !faqContent) return;
    setKnowledgeList([...knowledgeList, { id: `${Date.now()}`, title: faqTitle, type: 'FAQ Matni', date: 'Hozir' }]);
    setFaqTitle('');
    setFaqContent('');
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Bot className="w-5 h-5 text-purple-400" />
            OpenRouter AI Agent va RAG Bilimlar Bazasi
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Llama 3.3 70B, GPT-4o-mini yoki Claude 3.5 Haiku modellari orqali 24/7 aqlli mijozlar bilan muloqot
          </p>
        </div>
        <button
          onClick={handleSaveConfig}
          className="px-4 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white text-xs font-semibold rounded-xl flex items-center gap-2 shadow-lg shadow-purple-600/30 transition"
        >
          {saved ? <CheckCircle2 className="w-4 h-4 text-emerald-300" /> : <Save className="w-4 h-4" />}
          {saved ? 'Saqlandi!' : 'Sozlamalarni Saqlash'}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: AI Model & Prompt Settings */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-5">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2 border-b border-slate-800 pb-3">
              <Sliders className="w-4 h-4 text-purple-400" />
              AI Agent Asosiy Sozlamalari
            </h3>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Neyrotarmoq Modeli</label>
                <select
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  className="w-full px-3 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-purple-500"
                >
                  <option value="meta-llama/llama-3.3-70b-instruct">Meta Llama 3.3 70B Instruct (Tavsiya etiladi)</option>
                  <option value="openai/gpt-4o-mini">OpenAI GPT-4o Mini (Yuqori tezlik)</option>
                  <option value="anthropic/claude-3.5-haiku">Anthropic Claude 3.5 Haiku</option>
                </select>
              </div>

              <div className="flex items-center gap-4 pt-6">
                <label className="flex items-center gap-2 cursor-pointer text-xs text-slate-300 font-medium">
                  <input
                    type="checkbox"
                    checked={leadCapture}
                    onChange={(e) => setLeadCapture(e.target.checked)}
                    className="w-4 h-4 rounded text-purple-600 bg-slate-800 border-slate-700 focus:ring-purple-500"
                  />
                  Avtomatik Lead Capture (Telefon/Ism yig'ish)
                </label>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                AI Agent Tizimli Ko'rsatmasi (System Prompt)
              </label>
              <textarea
                rows={6}
                value={systemPrompt}
                onChange={(e) => setSystemPrompt(e.target.value)}
                className="w-full px-4 py-3 bg-slate-800/80 border border-slate-700 rounded-xl text-xs text-slate-200 leading-relaxed placeholder-slate-500 focus:outline-none focus:border-purple-500 font-mono"
              />
            </div>

            <div className="grid grid-cols-2 gap-6 pt-2">
              <div>
                <div className="flex justify-between text-xs text-slate-400 mb-1.5">
                  <span>Temperature (Ijodiylik):</span>
                  <span className="font-bold text-purple-400">{temperature}</span>
                </div>
                <input
                  type="range"
                  min="0.0"
                  max="1.0"
                  step="0.1"
                  value={temperature}
                  onChange={(e) => setTemperature(parseFloat(e.target.value))}
                  className="w-full accent-purple-600 cursor-pointer"
                />
              </div>

              <div>
                <div className="flex justify-between text-xs text-slate-400 mb-1.5">
                  <span>Maksimal Tokenlar (Uzunlik):</span>
                  <span className="font-bold text-purple-400">{maxTokens} ta</span>
                </div>
                <input
                  type="range"
                  min="100"
                  max="800"
                  step="50"
                  value={maxTokens}
                  onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                  className="w-full accent-purple-600 cursor-pointer"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Right: RAG Knowledge Base */}
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2 border-b border-slate-800 pb-3">
              <Database className="w-4 h-4 text-emerald-400" />
              RAG Bilimlar Bazasi
            </h3>
            <p className="text-xs text-slate-400">
              AI modeliga kompaniyangiz ma'lumotlarini o'rgating. U mijozlar savollariga ushbu bilimlar asosida aniq javob beradi.
            </p>

            <form onSubmit={handleAddKnowledge} className="space-y-3">
              <div>
                <input
                  type="text"
                  placeholder="Mavzu (masalan: Kurs narxi)"
                  value={faqTitle}
                  onChange={(e) => setFaqTitle(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-xl text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-purple-500"
                />
              </div>
              <div>
                <textarea
                  rows={3}
                  placeholder="Batafsil matn yoki savol-javob..."
                  value={faqContent}
                  onChange={(e) => setFaqContent(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-xl text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-purple-500"
                />
              </div>
              <button
                type="submit"
                className="w-full py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 rounded-xl text-xs font-semibold flex items-center justify-center gap-2 transition"
              >
                <UploadCloud className="w-4 h-4 text-emerald-400" />
                Bilimlar Bazasiga Qo'shish
              </button>
            </form>

            <div className="pt-2 border-t border-slate-800 space-y-2">
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
                Mavjud Bilimlar ({knowledgeList.length})
              </span>
              {knowledgeList.map((k) => (
                <div key={k.id} className="p-2.5 bg-slate-950/60 rounded-xl border border-slate-800/80 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2 truncate">
                    <FileText className="w-3.5 h-3.5 text-purple-400 shrink-0" />
                    <span className="text-slate-300 truncate font-medium">{k.title}</span>
                  </div>
                  <span className="text-[10px] text-slate-500 shrink-0">{k.date}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
