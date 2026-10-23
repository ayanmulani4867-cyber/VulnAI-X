import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { EmergencyModal } from './components/EmergencyModal';
import { TargetCheckModal } from './components/TargetCheckModal';
import { JobCreateModal } from './components/JobCreateModal';

import { Dashboard } from './pages/Dashboard';
import { ScopeManager } from './pages/ScopeManager';
import { ResearchJobs } from './pages/ResearchJobs';
import { Findings } from './pages/Findings';
import { Reports } from './pages/Reports';
import { AgentActivity } from './pages/AgentActivity';
import { EmailSettings } from './pages/EmailSettings';
import { SystemHealth } from './pages/SystemHealth';
import { Login } from './pages/Login';

import { User, AuthorizedProgram } from './types';
import { api } from './services/api';

export const App: React.FC = () => {
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('vulnai_user');
    return saved ? JSON.parse(saved) : null;
  });

  const [currentTab, setCurrentTab] = useState<string>('dashboard');
  const [emergencyActive, setEmergencyActive] = useState(false);
  const [workerOnline, setWorkerOnline] = useState(false);
  const [programs, setPrograms] = useState<AuthorizedProgram[]>([]);

  // Modals
  const [isEmergencyModalOpen, setIsEmergencyModalOpen] = useState(false);
  const [isScopeCheckModalOpen, setIsScopeCheckModalOpen] = useState(false);
  const [isJobCreateModalOpen, setIsJobCreateModalOpen] = useState(false);

  // Re-verify session on mount
  useEffect(() => {
    if (user) {
      api.getCurrentUser()
        .then(u => setUser(u))
        .catch(() => {
          api.removeToken();
          setUser(null);
        });
    }

    const handleUnauthorized = () => setUser(null);
    window.addEventListener('auth:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('auth:unauthorized', handleUnauthorized);
  }, []);

  // Poll system health & load programs
  useEffect(() => {
    if (!user || user.must_change_password) return;

    const checkSystem = async () => {
      try {
        const [health, progs] = await Promise.all([
          api.getHealth(),
          api.getPrograms()
        ]);
        setEmergencyActive(health.emergency_stop);
        setWorkerOnline(health.worker_status === 'healthy');
        setPrograms(progs);
      } catch (err) {
        // silent fail
      }
    };

    checkSystem();
    const interval = setInterval(checkSystem, 8000);
    return () => clearInterval(interval);
  }, [user]);

  const handleLogout = () => {
    api.removeToken();
    setUser(null);
  };

  const handleEmergencyReset = async () => {
    try {
      await api.resetEmergencyStop();
      setEmergencyActive(false);
    } catch (err: any) {
      alert(`Reset failed: ${err.message}`);
    }
  };

  if (!user || user.must_change_password) {
    return <Login initialUser={user} onLoginSuccess={(loggedInUser) => setUser(loggedInUser)} />;
  }

  const titles: Record<string, string> = {
    dashboard: 'Security Overview Dashboard',
    scopes: 'Authorization & Scope Registry',
    jobs: 'Research Jobs & Orchestration',
    findings: 'Vulnerability Findings & Evidence',
    reports: 'Security Reports & Exports',
    agents: 'Multi-Agent Architecture',
    email: 'Email Alerts & Notifications',
    health: 'System Health & Cloud Infrastructure'
  };

  return (
    <div className="app-layout">
      {/* Fixed Sidebar */}
      <Sidebar
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
        onEmergencyStop={() => setIsEmergencyModalOpen(true)}
        emergencyActive={emergencyActive}
      />

      {/* Main Content Area */}
      <div className="main-wrapper">
        <Header
          title={titles[currentTab] || 'VulnAI X'}
          workerOnline={workerOnline}
          user={user}
          onLogout={handleLogout}
        />

        <main className="page-container">
          {/* Emergency Stop Active Banner */}
          {emergencyActive && (
            <div className="emergency-banner">
              <div>
                <b style={{ color: '#FCA5A5' }}>EMERGENCY STOP PROTOCOL ACTIVE</b>
                <div style={{ fontSize: '0.8rem', color: '#CBD5E1', marginTop: 2 }}>
                  All research jobs are paused. New target execution is prohibited until reset.
                </div>
              </div>
              <button className="btn btn-primary btn-sm" onClick={handleEmergencyReset}>
                Reset Circuit
              </button>
            </div>
          )}

          {/* Active Tab View */}
          {currentTab === 'dashboard' && (
            <Dashboard
              onOpenNewJob={() => setIsJobCreateModalOpen(true)}
              onOpenScopeCheck={() => setIsScopeCheckModalOpen(true)}
              onNavigateTab={(tab) => setCurrentTab(tab)}
            />
          )}

          {currentTab === 'scopes' && (
            <ScopeManager onOpenCheck={() => setIsScopeCheckModalOpen(true)} />
          )}

          {currentTab === 'jobs' && (
            <ResearchJobs onOpenNewJob={() => setIsJobCreateModalOpen(true)} />
          )}

          {currentTab === 'findings' && <Findings />}

          {currentTab === 'reports' && <Reports />}

          {currentTab === 'agents' && <AgentActivity />}

          {currentTab === 'email' && <EmailSettings />}

          {currentTab === 'health' && (
            <SystemHealth
              onTriggerEmergencyStop={() => setIsEmergencyModalOpen(true)}
              onResetEmergencyStop={handleEmergencyReset}
            />
          )}
        </main>
      </div>

      {/* Global Modals */}
      <EmergencyModal
        isOpen={isEmergencyModalOpen}
        onClose={() => setIsEmergencyModalOpen(false)}
        onSuccess={() => setEmergencyActive(true)}
      />

      <TargetCheckModal
        isOpen={isScopeCheckModalOpen}
        onClose={() => setIsScopeCheckModalOpen(false)}
        programs={programs}
      />

      <JobCreateModal
        isOpen={isJobCreateModalOpen}
        onClose={() => setIsJobCreateModalOpen(false)}
        onSuccess={() => setCurrentTab('jobs')}
        programs={programs}
      />
    </div>
  );
};

export default App;
