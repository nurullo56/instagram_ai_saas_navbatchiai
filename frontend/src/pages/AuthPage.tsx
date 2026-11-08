import React, { useState } from 'react';
import { Sparkles, ArrowRight, Lock, Mail, User as UserIcon, Building2 } from 'lucide-react';
import { apiClient } from '../api/client';

interface AuthPageProps {
  onAuthSuccess: () => void;
}

export const AuthPage: React.FC<AuthPageProps> = ({ onAuthSuccess }) => {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
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
          tenant_name: tenantName || 'Mening Biznesim',
        });
        localStorage.setItem('access_token', res.data.access_token);
        localStorage.setItem('refresh_token', res.data.refresh_token);
        if (res.data.tenant_id) {
          localStorage.setItem('active_tenant_id', res.data.tenant_id);
        }
      } else {
        // Tizimga kirish
        const res = await apiClient.post('/auth/login', {
          email,
          password,
        });
        localStorage.setItem('access_token', res.data.access_token);
        localStorage.setItem('refresh_token', res.data.refresh_token);
        if (res.data.tenant_id) {
          localStorage.setItem('active_tenant_id', res.data.tenant_id);
        }
      }
      onAuthSuccess();
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Xatolik yuz berdi. Qayta urinib ko\'ring.';
      setError(msg);
    } finally {
      setLoading(false);
    }
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
          <div className="mb-6 p-3 rounded-lg bg-red-950/40 border border-red-800/50 text-red-300 text-sm">
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
                placeholder="admin@kompaniya.uz"
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

        <div className="mt-6 text-center text-xs text-slate-400">
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
