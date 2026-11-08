import React from 'react';
import {
  Instagram,
  GitFork,
  MessageSquare,
  Users,
  CheckCircle2,
  Clock,
  ArrowUpRight,
  ShieldCheck,
  Zap
} from 'lucide-react';

interface DashboardProps {
  onNavigate: (tab: string) => void;
}

export const DashboardOverviewPage: React.FC<DashboardProps> = ({ onNavigate }) => {
  const stats = [
    { title: 'Ulangan Instagram', value: '2 ta', change: '+1 yangi', icon: Instagram, color: 'text-pink-400', bg: 'bg-pink-950/40' },
    { title: 'Faol Oqimlar (DAG)', value: '6 ta', change: '100% sog\'lom', icon: GitFork, color: 'text-purple-400', bg: 'bg-purple-950/40' },
    { title: 'Ochiq Suhbatlar', value: '48 ta', change: '12 ta yangi', icon: MessageSquare, color: 'text-blue-400', bg: 'bg-blue-950/40' },
    { title: 'Yig\'ilgan Leadlar', value: '142 ta', change: '+18% bu hafta', icon: Users, color: 'text-emerald-400', bg: 'bg-emerald-950/40' },
  ];

  return (
    <div className="space-y-8">
      {/* Welcome banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-purple-900/50 via-indigo-900/40 to-slate-900 border border-purple-800/40 p-8 shadow-xl">
        <div className="relative z-10 max-w-2xl">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-purple-500/20 text-purple-300 border border-purple-500/30 mb-3">
            <Zap className="w-3.5 h-3.5 text-purple-400" />
            Instagram AI SaaS Engine v2.5 Faol
          </span>
          <h2 className="text-2xl font-bold text-white mb-2">
            Instagram Savdo va Mijozlarga Xizmat Ko'rsatishni Avtomatlashtiring
          </h2>
          <p className="text-sm text-slate-300 leading-relaxed mb-6">
            Meta Graph API v21.0 orqali izohlarga avtomatik Private Reply yuboring, Direct xabarlarni 24 soatlik qoidaga rioya qilgan holda qabul qiling va OpenRouter AI orqali mijozlarni saralang.
          </p>
          <div className="flex items-center gap-3">
            <button
              onClick={() => onNavigate('flows')}
              className="px-4 py-2.5 bg-purple-600 hover:bg-purple-500 text-white font-medium text-sm rounded-xl flex items-center gap-2 shadow-lg shadow-purple-600/30 transition"
            >
              Yangi Oqim (DAG) Yaratish
              <ArrowUpRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => onNavigate('accounts')}
              className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-sm rounded-xl border border-slate-700 transition"
            >
              Instagram Akkaunt Ulash
            </button>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((s, idx) => {
          const Icon = s.icon;
          return (
            <div key={idx} className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-medium text-slate-400">{s.title}</span>
                <div className={`p-2 rounded-xl ${s.bg}`}>
                  <Icon className={`w-4 h-4 ${s.color}`} />
                </div>
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-slate-100">{s.value}</span>
                <span className="text-xs font-medium text-emerald-400">{s.change}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Architecture Health Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Meta 24-Hour Window Health */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <Clock className="w-4 h-4 text-purple-400" />
              Meta 24-Soatlik Oyna Holati
            </h3>
            <span className="text-xs bg-emerald-950 text-emerald-400 px-2 py-0.5 rounded-full border border-emerald-800">
              Faol
            </span>
          </div>
          <p className="text-xs text-slate-400 mb-4">
            Mijoz so'nggi xabar yozgan vaqtdan boshlab 24 soatlik bepul Direct javob oynasi hisoblanadi.
          </p>
          <div className="space-y-3">
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-400">Oyna ichidagi ochiq suhbatlar:</span>
              <span className="font-bold text-emerald-400">42 ta</span>
            </div>
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-400">24 soati tugagan (muzlatilgan):</span>
              <span className="font-bold text-amber-400">6 ta</span>
            </div>
            <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
              <div className="bg-emerald-500 h-full rounded-full" style={{ width: '87%' }}></div>
            </div>
          </div>
        </div>

        {/* Private Reply 7-Day Window Health */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-pink-400" />
              Izoh Private Reply (7 Kunlik)
            </h3>
            <span className="text-xs bg-purple-950 text-purple-400 px-2 py-0.5 rounded-full border border-purple-800">
              Himoyalangan
            </span>
          </div>
          <p className="text-xs text-slate-400 mb-4">
            Architecture v2.5: Asl Instagram izohi vaqti (ig_comment_created_at) bo'yicha 7 kunlik cheklov va 5-holatli atomik lease nazorati.
          </p>
          <div className="space-y-3 text-xs">
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Yuborilgan Private Reply:</span>
              <span className="font-bold text-slate-200">184 ta</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Muddati o'tib rad etilgan (&gt;7 kun):</span>
              <span className="font-bold text-slate-400">3 ta</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Dublikat yuborish holati:</span>
              <span className="font-bold text-emerald-400">0 ta (100% himoya)</span>
            </div>
          </div>
        </div>

        {/* OpenRouter AI Status */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-indigo-400" />
              AI Agent & Lead Capture
            </h3>
            <span className="text-xs bg-indigo-950 text-indigo-400 px-2 py-0.5 rounded-full border border-indigo-800">
              Llama 3.3 70B
            </span>
          </div>
          <p className="text-xs text-slate-400 mb-4">
            OpenRouter orqali mijozlar bilan muloqot va telefon/email ma'lumotlarini CRM ga avtomatik yozish.
          </p>
          <div className="space-y-3 text-xs">
            <div className="flex justify-between items-center">
              <span className="text-slate-400">AI sarflagan tokenlar:</span>
              <span className="font-bold text-slate-200">34,120 / 100k</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Inson operatoriga uzatilgan:</span>
              <span className="font-bold text-blue-400">8 ta</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Muvaffaqiyatli Leadlar:</span>
              <span className="font-bold text-emerald-400">29 ta</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
