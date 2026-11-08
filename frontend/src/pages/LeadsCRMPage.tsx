import React, { useState } from 'react';
import {
  Users,
  Search,
  Phone,
  Mail,
  Instagram,
  Filter,
  CheckCircle2,
  Calendar,
  Tag
} from 'lucide-react';
import { Lead } from '../types';

export const LeadsCRMPage: React.FC = () => {
  const [leads, setLeads] = useState<Lead[]>([
    {
      id: 'lead-1',
      instagram_account_id: 'acc-1',
      ig_recipient_id: 'user_1001',
      username: 'anvar_dev',
      full_name: 'Anvar Karimov',
      phone_number: '+998901234567',
      email: 'anvar@dev.uz',
      stage: 'qualified',
      custom_attributes: { course: 'Python & AI', budget: '500k' },
      created_at: new Date(Date.now() - 3 * 3600 * 1000).toISOString()
    },
    {
      id: 'lead-2',
      instagram_account_id: 'acc-1',
      ig_recipient_id: 'user_1002',
      username: 'dilshod_marketing',
      full_name: 'Dilshod Rahmatov',
      phone_number: '+998935557788',
      email: 'dilshod@marketing.uz',
      stage: 'contacted',
      custom_attributes: { interest: 'Instagram SMM' },
      created_at: new Date(Date.now() - 24 * 3600 * 1000).toISOString()
    },
    {
      id: 'lead-3',
      instagram_account_id: 'acc-1',
      ig_recipient_id: 'user_1003',
      username: 'malika_designer',
      full_name: 'Malika Karimova',
      phone_number: '+998971112233',
      stage: 'new',
      custom_attributes: {},
      created_at: new Date(Date.now() - 5 * 3600 * 1000).toISOString()
    }
  ]);

  const [search, setSearch] = useState('');
  const [stageFilter, setStageFilter] = useState<string>('all');

  const filteredLeads = leads.filter((l) => {
    const matchesSearch =
      (l.full_name || '').toLowerCase().includes(search.toLowerCase()) ||
      (l.phone_number || '').includes(search) ||
      (l.username || '').toLowerCase().includes(search.toLowerCase());
    const matchesStage = stageFilter === 'all' || l.stage === stageFilter;
    return matchesSearch && matchesStage;
  });

  const getStageBadge = (stage: Lead['stage']) => {
    const styles: Record<string, string> = {
      new: 'bg-blue-950/60 text-blue-300 border-blue-800',
      contacted: 'bg-purple-950/60 text-purple-300 border-purple-800',
      qualified: 'bg-emerald-950/60 text-emerald-300 border-emerald-800',
      won: 'bg-teal-950/60 text-teal-300 border-teal-800',
      lost: 'bg-red-950/60 text-red-300 border-red-800'
    };
    return (
      <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-semibold border ${styles[stage] || styles.new}`}>
        {stage.toUpperCase()}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-100">Instagram Leads CRM</h2>
          <p className="text-xs text-slate-400 mt-1">
            AI va bot orqali Direct xabarlardan avtomatik yig'ilgan mijozlar bazasi
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold px-3 py-1.5 bg-slate-900 border border-slate-800 rounded-xl text-slate-300">
            Jami Leadlar: <span className="text-purple-400 font-bold">{leads.length} ta</span>
          </span>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex items-center justify-between gap-4 bg-slate-900 border border-slate-800 p-4 rounded-2xl">
        <div className="relative w-80">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Ism, telefon yoki @username bo'yicha qidirish..."
            className="w-full pl-9 pr-3 py-1.5 bg-slate-800 border border-slate-700 rounded-xl text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-purple-500"
          />
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 font-medium">Bosqich:</span>
          {['all', 'new', 'contacted', 'qualified', 'won'].map((s) => (
            <button
              key={s}
              onClick={() => setStageFilter(s)}
              className={`px-3 py-1.5 rounded-xl text-xs font-medium transition ${
                stageFilter === s
                  ? 'bg-purple-600 text-white font-semibold'
                  : 'bg-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              {s === 'all' ? 'Barchasi' : s.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Leads Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-sm">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-slate-800 text-[11px] font-semibold text-slate-400 uppercase tracking-wider bg-slate-950/40">
              <th className="py-3.5 px-6">Mijoz / Username</th>
              <th className="py-3.5 px-6">Telefon Raqam</th>
              <th className="py-3.5 px-6">Email Manzil</th>
              <th className="py-3.5 px-6">Bosqich (Stage)</th>
              <th className="py-3.5 px-6">Yaratilgan Sana</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-xs">
            {filteredLeads.map((lead) => (
              <tr key={lead.id} className="hover:bg-slate-800/30 transition">
                <td className="py-4 px-6">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center font-bold text-purple-400">
                      @{lead.username?.[0].toUpperCase()}
                    </div>
                    <div>
                      <p className="font-semibold text-slate-200">{lead.full_name || 'Ismi kiritilmagan'}</p>
                      <p className="text-[11px] text-purple-400 font-mono">@{lead.username}</p>
                    </div>
                  </div>
                </td>
                <td className="py-4 px-6 font-mono text-slate-300">
                  {lead.phone_number ? (
                    <a
                      href={`tel:${lead.phone_number}`}
                      className="inline-flex items-center gap-1.5 text-emerald-400 hover:underline"
                    >
                      <Phone className="w-3.5 h-3.5" />
                      {lead.phone_number}
                    </a>
                  ) : (
                    <span className="text-slate-500">—</span>
                  )}
                </td>
                <td className="py-4 px-6 text-slate-300">
                  {lead.email ? (
                    <span className="inline-flex items-center gap-1.5">
                      <Mail className="w-3.5 h-3.5 text-slate-500" />
                      {lead.email}
                    </span>
                  ) : (
                    <span className="text-slate-500">—</span>
                  )}
                </td>
                <td className="py-4 px-6">{getStageBadge(lead.stage)}</td>
                <td className="py-4 px-6 text-slate-500 font-mono text-[11px]">
                  {new Date(lead.created_at).toLocaleDateString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
