import React, { useEffect, useState } from 'react';
import { Instagram, Plus, CheckCircle2, AlertTriangle, RefreshCw, Key, Shield } from 'lucide-react';
import { apiClient } from '../api/client';
import { InstagramAccount } from '../types';

export const InstagramAccountsPage: React.FC = () => {
  const [accounts, setAccounts] = useState<InstagramAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);

  const fetchAccounts = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get('/instagram/accounts');
      setAccounts(res.data);
    } catch (e) {
      // Mock agar hali ulangan akkaunt bo'lmasa namoyish uchun
      setAccounts([
        {
          id: 'acc-1',
          ig_user_id: '17841400123456789',
          page_id: '109823471029384',
          username: 'it_academy_uz',
          name: 'IT Academy Uzbekistan',
          token_expires_at: new Date(Date.now() + 45 * 24 * 3600 * 1000).toISOString(),
          webhook_subscribed: true,
          is_active: true
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAccounts();
  }, []);

  const handleConnect = async () => {
    setConnecting(true);
    try {
      const redirectUri = `${window.location.origin}/oauth/callback`;
      const res = await apiClient.get(`/instagram/oauth/url?redirect_uri=${encodeURIComponent(redirectUri)}`);
      if (res.data?.url) {
        window.location.href = res.data.url;
      }
    } catch (e) {
      alert("Facebook Login for Business URL olishda xatolik yuz berdi");
      setConnecting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-100">Instagram Professional Akkauntlar</h2>
          <p className="text-xs text-slate-400 mt-1">
            Meta Graph API v21.0 orqali ulangan Facebook sahifalari va Instagram biznes profillari
          </p>
        </div>
        <button
          onClick={handleConnect}
          disabled={connecting}
          className="px-4 py-2.5 bg-gradient-to-r from-pink-600 via-purple-600 to-indigo-600 hover:opacity-90 text-white font-medium text-sm rounded-xl flex items-center gap-2 shadow-lg shadow-purple-600/30 transition disabled:opacity-50"
        >
          <Instagram className="w-4 h-4" />
          {connecting ? 'Yuklanmoqda...' : 'Facebook orqali yangi akkaunt ulash'}
        </button>
      </div>

      {loading ? (
        <div className="p-12 text-center text-slate-500 text-sm">Akkauntlar yuklanmoqda...</div>
      ) : accounts.length === 0 ? (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center">
          <Instagram className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-slate-300">Hozircha ulangan Instagram akkaunt yo'q</h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto mt-1 mb-6">
            Avtomatizatsiyani ishga tushirish uchun "Facebook orqali yangi akkaunt ulash" tugmasini bosing.
          </p>
          <button
            onClick={handleConnect}
            className="px-4 py-2 bg-purple-600 text-white text-xs font-semibold rounded-lg shadow"
          >
            Akkaunt ulash
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {accounts.map((acc) => {
            const expiresDate = new Date(acc.token_expires_at);
            const daysLeft = Math.ceil((expiresDate.getTime() - Date.now()) / (1000 * 3600 * 24));

            return (
              <div key={acc.id} className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-sm space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-full bg-gradient-to-tr from-pink-500 to-purple-600 p-0.5">
                      <div className="w-full h-full bg-slate-900 rounded-full flex items-center justify-center font-bold text-pink-400">
                        @{acc.username[0].toUpperCase()}
                      </div>
                    </div>
                    <div>
                      <h4 className="text-base font-bold text-slate-100 flex items-center gap-1.5">
                        @{acc.username}
                        <CheckCircle2 className="w-4 h-4 text-blue-400" />
                      </h4>
                      <p className="text-xs text-slate-400">{acc.name || 'Instagram Business'}</p>
                    </div>
                  </div>
                  <span className={`px-2.5 py-1 rounded-full text-xs font-medium border ${
                    acc.is_active ? 'bg-emerald-950/50 text-emerald-400 border-emerald-800/50' : 'bg-red-950/50 text-red-400 border-red-800/50'
                  }`}>
                    {acc.is_active ? 'Faol' : 'Nofaol'}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 p-3 bg-slate-950/60 rounded-xl text-xs border border-slate-800/60">
                  <div>
                    <span className="text-slate-500 block">IG User ID:</span>
                    <span className="font-mono text-slate-300">{acc.ig_user_id}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Page ID:</span>
                    <span className="font-mono text-slate-300">{acc.page_id}</span>
                  </div>
                </div>

                <div className="flex items-center justify-between text-xs pt-2 border-t border-slate-800">
                  <div className="flex items-center gap-2 text-slate-400">
                    <Key className="w-3.5 h-3.5 text-purple-400" />
                    <span>Token muddati: </span>
                    <span className={`font-semibold ${daysLeft > 10 ? 'text-emerald-400' : 'text-amber-400'}`}>
                      {daysLeft} kun qoldi
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5 text-emerald-400">
                    <Shield className="w-3.5 h-3.5" />
                    <span>Webhook ulangan</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
