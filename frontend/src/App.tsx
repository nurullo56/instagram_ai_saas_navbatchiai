import React, { useState, useEffect } from 'react';
import { Layout } from './components/Layout';
import { AuthPage } from './pages/AuthPage';
import { DashboardOverviewPage } from './pages/DashboardOverviewPage';
import { InstagramAccountsPage } from './pages/InstagramAccountsPage';
import { FlowBuilderPage } from './pages/FlowBuilderPage';
import { LiveInboxPage } from './pages/LiveInboxPage';
import { LeadsCRMPage } from './pages/LeadsCRMPage';
import { AIAgentPage } from './pages/AIAgentPage';
import { BillingPage } from './pages/BillingPage';
import { User, Tenant } from './types';

export const App: React.FC = () => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(
    Boolean(localStorage.getItem('access_token'))
  );
  const [currentTab, setCurrentTab] = useState<string>('dashboard');
  const [user, setUser] = useState<User | null>({
    id: 'usr-1',
    email: 'admin@itacademy.uz',
    full_name: 'Super Admin',
    is_active: true,
    is_superuser: true
  });
  const [activeTenant, setActiveTenant] = useState<Tenant | null>({
    id: 'tnt-1',
    name: 'IT Academy MCHJ',
    slug: 'it-academy',
    is_active: true
  });

  useEffect(() => {
    const handleUnauthorized = () => {
      setIsAuthenticated(false);
      localStorage.removeItem('access_token');
    };
    window.addEventListener('auth_unauthorized', handleUnauthorized);
    return () => window.removeEventListener('auth_unauthorized', handleUnauthorized);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('active_tenant_id');
    setIsAuthenticated(false);
  };

  if (!isAuthenticated) {
    return <AuthPage onAuthSuccess={() => setIsAuthenticated(true)} />;
  }

  const renderContent = () => {
    switch (currentTab) {
      case 'dashboard':
        return <DashboardOverviewPage onNavigate={(tab) => setCurrentTab(tab)} />;
      case 'accounts':
        return <InstagramAccountsPage />;
      case 'flows':
        return <FlowBuilderPage />;
      case 'inbox':
        return <LiveInboxPage />;
      case 'leads':
        return <LeadsCRMPage />;
      case 'ai':
        return <AIAgentPage />;
      case 'billing':
        return <BillingPage />;
      default:
        return <DashboardOverviewPage onNavigate={(tab) => setCurrentTab(tab)} />;
    }
  };

  return (
    <Layout
      currentTab={currentTab}
      onSelectTab={setCurrentTab}
      user={user}
      activeTenant={activeTenant}
      onLogout={handleLogout}
    >
      {renderContent()}
    </Layout>
  );
};

export default App;
