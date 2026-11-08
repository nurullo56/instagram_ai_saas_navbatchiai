import React from 'react';
import {
  LayoutDashboard,
  Instagram,
  GitFork,
  MessageSquare,
  Users,
  Bot,
  CreditCard,
  LogOut,
  Building2,
  Sparkles
} from 'lucide-react';
import { Tenant, User } from '../types';

interface LayoutProps {
  currentTab: string;
  onSelectTab: (tab: string) => void;
  user: User | null;
  activeTenant: Tenant | null;
  onLogout: () => void;
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({
  currentTab,
  onSelectTab,
  user,
  activeTenant,
  onLogout,
  children
}) => {
  const navItems = [
    { id: 'dashboard', label: 'Boshqaruv paneli', icon: LayoutDashboard },
    { id: 'accounts', label: 'Instagram akkauntlar', icon: Instagram },
    { id: 'flows', label: 'Flow Builder (DAG)', icon: GitFork },
    { id: 'inbox', label: 'Live Inbox & Operator', icon: MessageSquare },
    { id: 'leads', label: 'Leads CRM', icon: Users },
    { id: 'ai', label: 'AI Yordamchi & RAG', icon: Bot },
    { id: 'billing', label: 'Tariflar & To\'lovlar', icon: CreditCard },
  ];

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col justify-between">
        <div>
          {/* Logo & Brand */}
          <div className="h-16 flex items-center px-6 border-b border-slate-800 gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-pink-500 via-purple-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-purple-500/20">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="font-bold text-base bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                InstaAI SaaS
              </span>
              <p className="text-xs text-slate-500">Avtomatizatsiya 2.5</p>
            </div>
          </div>

          {/* Active Tenant Badge */}
          {activeTenant && (
            <div className="px-4 py-3 mx-3 my-3 bg-slate-800/60 rounded-xl border border-slate-700/50 flex items-center gap-3">
              <Building2 className="w-4 h-4 text-purple-400 shrink-0" />
              <div className="truncate">
                <p className="text-xs text-slate-400 font-medium">Faol Kompaniya</p>
                <p className="text-sm font-semibold text-slate-200 truncate">{activeTenant.name}</p>
              </div>
            </div>
          )}

          {/* Navigation Links */}
          <nav className="px-3 space-y-1 mt-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = currentTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => onSelectTab(item.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-purple-600 text-white shadow-md shadow-purple-600/30 font-semibold'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                  {item.label}
                </button>
              );
            })}
          </nav>
        </div>

        {/* User profile & Logout */}
        <div className="p-4 border-t border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3 truncate">
            <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-xs text-purple-300">
              {user?.full_name ? user.full_name[0].toUpperCase() : 'U'}
            </div>
            <div className="truncate">
              <p className="text-xs font-semibold text-slate-200 truncate">{user?.full_name || 'Foydalanuvchi'}</p>
              <p className="text-[11px] text-slate-500 truncate">{user?.email || ''}</p>
            </div>
          </div>
          <button
            onClick={onLogout}
            title="Chiqish"
            className="p-1.5 text-slate-400 hover:text-red-400 hover:bg-red-950/30 rounded-lg transition"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Top Navbar */}
        <header className="h-16 bg-slate-900/60 backdrop-blur border-b border-slate-800 px-8 flex items-center justify-between shrink-0">
          <h1 className="text-lg font-semibold text-slate-100 capitalize">
            {navItems.find((n) => n.id === currentTab)?.label || 'Boshqaruv'}
          </h1>
          <div className="flex items-center gap-3">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-950/60 text-emerald-400 border border-emerald-800/50">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              Meta v21.0 Online
            </span>
          </div>
        </header>

        {/* Scrollable Page Body */}
        <div className="flex-1 overflow-y-auto p-8">
          {children}
        </div>
      </main>
    </div>
  );
};
