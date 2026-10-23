import React from 'react';
import { 
  LayoutDashboard, ShieldCheck, PlayCircle, AlertTriangle, 
  FileText, Cpu, Mail, Activity, AlertOctagon 
} from 'lucide-react';

interface SidebarProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
  onEmergencyStop: () => void;
  emergencyActive: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({ 
  currentTab, 
  setCurrentTab, 
  onEmergencyStop,
  emergencyActive 
}) => {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'scopes', label: 'Scope Registry', icon: ShieldCheck },
    { id: 'jobs', label: 'Research Jobs', icon: PlayCircle },
    { id: 'findings', label: 'Findings & Evidence', icon: AlertTriangle },
    { id: 'reports', label: 'Reports & Exports', icon: FileText },
    { id: 'agents', label: 'Agent Topology', icon: Cpu },
    { id: 'email', label: 'Email Alerts', icon: Mail },
    { id: 'health', label: 'System Health', icon: Activity },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="logo-badge">
          <ShieldCheck size={22} />
        </div>
        <div>
          <div className="logo-title">Vuln<span>AI</span> X</div>
          <div style={{ fontSize: '0.68rem', color: '#64748B', fontWeight: 600 }}>AUTONOMOUS RESEARCH</div>
        </div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              className={`nav-item ${isActive ? 'active' : ''}`}
              onClick={() => setCurrentTab(item.id)}
            >
              <Icon size={18} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <button 
          className="emergency-btn"
          onClick={onEmergencyStop}
          style={emergencyActive ? { backgroundColor: 'var(--cyber-crimson)', color: '#fff' } : {}}
        >
          <AlertOctagon size={16} />
          <span>{emergencyActive ? 'EMERGENCY ACTIVE' : 'EMERGENCY STOP'}</span>
        </button>
      </div>
    </aside>
  );
};
