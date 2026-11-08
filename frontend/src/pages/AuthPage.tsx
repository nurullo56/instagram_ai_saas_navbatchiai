import React, { useState } from 'react';
import { Sparkles, ArrowRight, Lock, Mail, User as UserIcon, Building2, PlayCircle } from 'lucide-react';
import { apiClient } from '../api/client';

interface AuthPageProps {
  onAuthSuccess: () => void;
}

export const AuthPage: React.FC<AuthPageProps> = ({ onAuthSuccess }) => {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('admin@saas.com');
  const [password, setPassword] = useState('AdminSecurePassword2026!');
  const [fullName, setFullName] = useState('');
  const [tenantName, setTenantName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (isRegister) {
        // Ro'yxatdan o'tish
        const res = await apiClient.post('/auth/register', {
          email,
          password,
          full_name: fullName,
          company_name: tenantName || 'Mening Biznesim',
        });
        const tokenData = res.data?.data || res.data;
        if (tokenData?.access_token) {
          localStorage.setItem('access_token', tokenData.access_token);
          localStorage.setItem('refresh_token', tokenData.refresh_token);
        }
      } else {
        // Tizimga kirish (JSON formatida)
        const res = await apiClient.post('/auth/login', {
          email,
          password,
        });
        if (res.data?.access_token) {
          localStorage.setItem('access_token', res.data.access_token);
          localStorage.setItem('refresh_token', res.data.refresh_token);
        }
      }
      onAuthSuccess();
    } catch (err: any) {
      let msg = 'Xatolik yuz berdi. Qayta urinib ko\'ring.';
      const detail = err.response?.data?.detail;
      if (typeof detail === 'string') {
        msg = detail;
      } else if (Array.isArray(detail)) {
        msg = detail.map((d: any) => d.msg || JSON.stringify(d)).join(', ');
      } else if (detail && typeof detail === 'object') {
        msg = JSON.stringify(detail);
      } else if (err.message) {
        msg = err.message;
      }
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = () => {
    localStorage.setItem('access_token', 'demo_token_authenticated');
    localStorage.setItem('active_tenant_id', 'demo_tenant_id');
    onAuthSuccess();
  };

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-8">
        {/* Brand header */}
        <div className="text-center mb-8">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-pink-500 via-purple-600 to-indigo-600 flex items-center justify-center mx-auto mb-4 shadow-xl shadow-purple-500/20">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <h2 className="text-2xl font-bold text-slate-100">
            {isRegister ? 'Yangi SaaS hisob ochish' : 'Tizimga kirish'}
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Instagram Direct va Izohlar avtomatizatsiyasi
          </p>
        </div>

        {error && (
          <div className="mb-6 p-3 rounded-lg bg-red-950/40 border border-red-800/50 text-red-300 text-xs break-words">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {isRegister && (
            <>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Ism-familiya</label>
                <div className="relative">
                  <UserIcon className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
                  <input
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="Ali Valiyev"
                    className="w-full pl-10 pr-4 py-2.5 bg-slate-800/50 border border-slate-700/80 rounded-xl text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Kompaniya (Tenant) nomi</label>
                <div className="relative">
                  <Building2 className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
                  <input
                    type="text"
                    required
                    value={tenantName}
                    onChange={(e) => setTenantName(e.target.value)}
                    placeholder="IT Academy MCHJ"
                    className="w-full pl-10 pr-4 py-2.5 bg-slate-800/50 border border-slate-700/80 rounded-xl text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition"
                  />
                </div>
              </div>
            </>
          )}

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Email manzil</label>
            <div className="relative">
              <Mail className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@saas.com"
                className="w-full pl-10 pr-4 py-2.5 bg-slate-800/50 border border-slate-700/80 rounded-xl text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Parol</label>
            <div className="relative">
              <Lock className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Kamida 8 ta belgi"
                className="w-full pl-10 pr-4 py-2.5 bg-slate-800/50 border border-slate-700/80 rounded-xl text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-2 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-semibold rounded-xl text-sm flex items-center justify-center gap-2 shadow-lg shadow-purple-600/30 transition duration-150 disabled:opacity-50"
          >
            {loading ? 'Kutilmoqda...' : isRegister ? 'Ro\'yxatdan o\'tish' : 'Kirish'}
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        <div className="mt-4 pt-4 border-t border-slate-800">
          <button
            onClick={handleDemoLogin}
            className="w-full py-2.5 bg-slate-800 hover:bg-slate-700 text-purple-300 border border-slate-700 font-medium rounded-xl text-xs flex items-center justify-center gap-2 transition"
          >
            <PlayCircle className="w-4 h-4 text-purple-400" />
            Bir marta bosish bilan kirish (Tezkor Demo)
          </button>
        </div>

        <div className="mt-4 text-center text-xs text-slate-400">
          {isRegister ? (
            <p>
              Hisobingiz bormi?{' '}
              <button
                onClick={() => setIsRegister(false)}
                className="text-purple-400 hover:underline font-semibold"
              >
                Kirish
              </button>
            </p>
          ) : (
            <p>
              Yangi foydalanuvchimisiz?{' '}
              <button
                onClick={() => setIsRegister(true)}
                className="text-purple-400 hover:underline font-semibold"
              >
                Ro'yxatdan o'tish
              </button>
            </p>
          )}
        </div>
      </div>
    </div>
  );
};
