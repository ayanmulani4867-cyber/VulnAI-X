import React, { useEffect, useState } from 'react';
import { 
  PlayCircle, AlertTriangle, ShieldCheck, CheckCircle2, 
  XCircle, Flame, Clock, RefreshCw 
} from 'lucide-react';
import { DashboardStats, AuthorizedProgram } from '../types';
import { api } from '../services/api';

interface DashboardProps {
  onOpenNewJob: () => void;
  onOpenScopeCheck: () => void;
  onNavigateTab: (tab: string) => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ 
  onOpenNewJob, 
  onOpenScopeCheck, 
  onNavigateTab 
}) => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [programs, setPrograms] = useState<AuthorizedProgram[]>([]);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const [statsData, progsData] = await Promise.all([
        api.getDashboardStats(),
        api.getPrograms()
      ]);
      setStats(statsData);
      setPrograms(progsData);
    } catch (err) {
      console.error('Failed to load dashboard stats', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 10000); // 10s auto-refresh
    return () => clearInterval(interval);
  }, []);

  return (
    <div>
      {/* Quick Actions Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#FFFFFF' }}>Research Command Center</h2>
          <p style={{ fontSize: '0.82rem', color: '#94A3B8' }}>Autonomous, Fail-Closed Security Auditing & Evidence Management</p>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn btn-secondary btn-sm" onClick={fetchStats} title="Refresh Live Data">
            <RefreshCw size={14} className={loading ? 'spin' : ''} />
            <span>Refresh</span>
          </button>
          <button className="btn btn-secondary" onClick={onOpenScopeCheck}>
            <ShieldCheck size={16} />
            <span>Scope Pre-Flight Test</span>
          </button>
          <button className="btn btn-primary" onClick={onOpenNewJob}>
            <PlayCircle size={16} />
            <span>Launch Research Job</span>
          </button>
        </div>
      </div>

      {/* Top Stats Grid */}
      <div className="stats-grid">
        <div className="stat-card" onClick={() => onNavigateTab('jobs')} style={{ cursor: 'pointer' }}>
          <div className="stat-header">
            <span className="stat-label">Total Jobs</span>
            <div className="stat-icon" style={{ backgroundColor: 'rgba(59, 130, 246, 0.15)', color: 'var(--cyber-blue)' }}>
              <PlayCircle size={18} />
            </div>
          </div>
          <div className="stat-value">{stats?.total_jobs ?? 0}</div>
          <div className="stat-footer">
            <span style={{ color: stats?.running_jobs ? 'var(--cyber-cyan)' : 'inherit' }}>
              {stats?.running_jobs ?? 0} active now
            </span>
          </div>
        </div>

        <div className="stat-card" onClick={() => onNavigateTab('findings')} style={{ cursor: 'pointer' }}>
          <div className="stat-header">
            <span className="stat-label">Potential Vulns</span>
            <div className="stat-icon" style={{ backgroundColor: 'rgba(0, 240, 255, 0.15)', color: 'var(--cyber-cyan)' }}>
              <AlertTriangle size={18} />
            </div>
          </div>
          <div className="stat-value">{stats?.potential_vulnerabilities ?? 0}</div>
          <div className="stat-footer">Awaiting verification</div>
        </div>

        <div className="stat-card" onClick={() => onNavigateTab('findings')} style={{ cursor: 'pointer' }}>
          <div className="stat-header">
            <span className="stat-label">Verified Findings</span>
            <div className="stat-icon" style={{ backgroundColor: 'rgba(16, 185, 129, 0.15)', color: 'var(--cyber-emerald)' }}>
              <CheckCircle2 size={18} />
            </div>
          </div>
          <div className="stat-value" style={{ color: '#6EE7B7' }}>{stats?.verified_findings ?? 0}</div>
          <div className="stat-footer">Confirmed repeatable evidence</div>
        </div>

        <div className="stat-card" onClick={() => onNavigateTab('findings')} style={{ cursor: 'pointer' }}>
          <div className="stat-header">
            <span className="stat-label">Critical & High</span>
            <div className="stat-icon" style={{ backgroundColor: 'rgba(239, 68, 68, 0.15)', color: 'var(--cyber-crimson)' }}>
              <Flame size={18} />
            </div>
          </div>
          <div className="stat-value" style={{ color: stats?.critical_and_high ? 'var(--cyber-crimson)' : 'inherit' }}>
            {stats?.critical_and_high ?? 0}
          </div>
          <div className="stat-footer">Requires immediate attention</div>
        </div>

        <div className="stat-card" onClick={() => onNavigateTab('findings')} style={{ cursor: 'pointer' }}>
          <div className="stat-header">
            <span className="stat-label">False Positives</span>
            <div className="stat-icon" style={{ backgroundColor: 'rgba(139, 92, 246, 0.15)', color: 'var(--cyber-purple)' }}>
              <XCircle size={18} />
            </div>
          </div>
          <div className="stat-value" style={{ color: '#C4B5FD' }}>{stats?.false_positives ?? 0}</div>
          <div className="stat-footer">Filtered & cataloged</div>
        </div>

        <div className="stat-card" onClick={() => onNavigateTab('scopes')} style={{ cursor: 'pointer' }}>
          <div className="stat-header">
            <span className="stat-label">Active Scopes</span>
            <div className="stat-icon" style={{ backgroundColor: 'rgba(16, 185, 129, 0.15)', color: 'var(--cyber-emerald)' }}>
              <ShieldCheck size={18} />
            </div>
          </div>
          <div className="stat-value">{stats?.active_scopes_count ?? 0}</div>
          <div className="stat-footer">Across {programs.length} authorized programs</div>
        </div>
      </div>

      {/* Two Column Layout: Programs Overview & Recent Activity */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))', gap: 20 }}>
        {/* Authorized Bug Bounty Programs */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <ShieldCheck size={18} color="var(--cyber-cyan)" />
              <span>Authorized Bug Bounty Programs</span>
            </div>
            <button className="btn btn-secondary btn-sm" onClick={() => onNavigateTab('scopes')}>
              Manage Scopes
            </button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {programs.map((p) => (
              <div 
                key={p.id}
                style={{
                  padding: 14,
                  borderRadius: 8,
                  backgroundColor: 'rgba(255, 255, 255, 0.02)',
                  border: '1px solid var(--border-subtle)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between'
                }}
              >
                <div>
                  <div style={{ fontWeight: 700, fontSize: '0.95rem', color: '#FFFFFF' }}>{p.name}</div>
                  <div style={{ fontSize: '0.78rem', color: '#94A3B8' }}>{p.organization}</div>
                  {p.policy_url && (
                    <a 
                      href={p.policy_url} 
                      target="_blank" 
                      rel="noopener noreferrer" 
                      style={{ fontSize: '0.74rem', color: 'var(--cyber-cyan)', textDecoration: 'none' }}
                    >
                      Official Policy Reference →
                    </a>
                  )}
                </div>
                <div style={{ textAlign: 'right' }}>
                  <span className="badge badge-verified">{p.scopes_count ?? 0} Scopes Active</span>
                  <div style={{ fontSize: '0.72rem', color: '#64748B', marginTop: 4 }}>Fail-Closed Enforcement</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Live Audit Activity */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <Clock size={18} color="var(--cyber-amber)" />
              <span>Security Audit Trail</span>
            </div>
            <span style={{ fontSize: '0.75rem', color: '#64748B' }}>Cryptographically Logged</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {stats?.recent_activity && stats.recent_activity.length > 0 ? (
              stats.recent_activity.map((act) => (
                <div 
                  key={act.id}
                  style={{
                    padding: '8px 12px',
                    borderRadius: 6,
                    backgroundColor: 'rgba(255, 255, 255, 0.02)',
                    borderLeft: '3px solid var(--cyber-cyan)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 2
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#E2E8F0' }}>{act.action}</span>
                    <span style={{ fontSize: '0.7rem', color: '#64748B' }}>
                      {new Date(act.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#94A3B8' }}>{act.details}</div>
                </div>
              ))
            ) : (
              <div style={{ padding: 20, textAlign: 'center', color: '#64748B', fontSize: '0.85rem' }}>
                No security audit events recorded yet.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
