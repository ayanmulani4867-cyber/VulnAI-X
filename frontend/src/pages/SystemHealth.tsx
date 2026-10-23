import React, { useEffect, useState } from 'react';
import { Activity, Database, Cpu, AlertOctagon, CheckCircle2, ShieldCheck, RefreshCw } from 'lucide-react';
import { SystemHealth as SystemHealthType } from '../types';
import { api } from '../services/api';

export const SystemHealth: React.FC<{
  onTriggerEmergencyStop: () => void;
  onResetEmergencyStop: () => void;
}> = ({ onTriggerEmergencyStop, onResetEmergencyStop }) => {
  const [health, setHealth] = useState<SystemHealthType | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchHealth = async () => {
    try {
      setLoading(true);
      const data = await api.getHealth();
      setHealth(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 8000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#FFFFFF' }}>System Health & Cloud Infrastructure</h2>
          <p style={{ fontSize: '0.82rem', color: '#94A3B8' }}>
            Telemetry, worker heartbeats, database status, and ₹0 cloud deployment metrics.
          </p>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={fetchHealth}>
          <RefreshCw size={14} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Grid of Health Indicators */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-header">
            <span className="stat-label">System State</span>
            <div className="stat-icon" style={{ backgroundColor: 'rgba(16, 185, 129, 0.15)', color: 'var(--cyber-emerald)' }}>
              <Activity size={18} />
            </div>
          </div>
          <div className="stat-value" style={{ textTransform: 'capitalize' }}>
            {health?.status || 'Unknown'}
          </div>
          <div className="stat-footer">Version {health?.version || '1.0.0'}</div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span className="stat-label">Database Status</span>
            <div className="stat-icon" style={{ backgroundColor: 'rgba(0, 240, 255, 0.15)', color: 'var(--cyber-cyan)' }}>
              <Database size={18} />
            </div>
          </div>
          <div className="stat-value" style={{ color: '#6EE7B7' }}>
            {health?.database === 'healthy' ? 'Operational' : 'Degraded'}
          </div>
          <div className="stat-footer">
            {health?.database_engine === 'postgresql' ? 'Neon PostgreSQL (Cloud SSL)' : 'SQLite (Local Engine)'}
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span className="stat-label">Background Worker</span>
            <div className="stat-icon" style={{ backgroundColor: 'rgba(59, 130, 246, 0.15)', color: 'var(--cyber-blue)' }}>
              <Cpu size={18} />
            </div>
          </div>
          <div className="stat-value">
            {health?.worker_status === 'healthy' ? 'Active' : 'Offline'}
          </div>
          <div className="stat-footer">
            {health?.last_heartbeat ? `Heartbeat: ${new Date(health.last_heartbeat).toLocaleTimeString()}` : 'Awaiting worker start'}
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span className="stat-label">Emergency Circuit</span>
            <div className="stat-icon" style={{ backgroundColor: 'rgba(239, 68, 68, 0.15)', color: 'var(--cyber-crimson)' }}>
              <AlertOctagon size={18} />
            </div>
          </div>
          <div className="stat-value" style={{ color: health?.emergency_stop ? 'var(--cyber-crimson)' : 'var(--cyber-emerald)' }}>
            {health?.emergency_stop ? 'HALTED' : 'ARMED'}
          </div>
          <div className="stat-footer">Instant fail-safe switch</div>
        </div>
      </div>

      {/* Emergency Controls */}
      <div className="card" style={{ borderColor: health?.emergency_stop ? 'var(--cyber-crimson)' : 'var(--border-subtle)' }}>
        <div className="card-header">
          <div className="card-title">
            <AlertOctagon size={18} color="var(--cyber-crimson)" />
            <span>Emergency Kill Switch Controls</span>
          </div>
        </div>
        <p style={{ fontSize: '0.85rem', color: '#CBD5E1', marginBottom: 16 }}>
          In the event of an unexpected target response, scope ambiguity, or network anomaly, trigger the emergency stop to immediately cancel all active tasks.
        </p>
        <div style={{ display: 'flex', gap: 12 }}>
          <button 
            className="btn btn-danger"
            onClick={onTriggerEmergencyStop}
            disabled={health?.emergency_stop}
          >
            <AlertOctagon size={16} />
            <span>Trigger Emergency Stop</span>
          </button>
          {health?.emergency_stop && (
            <button 
              className="btn btn-primary"
              onClick={onResetEmergencyStop}
            >
              <CheckCircle2 size={16} />
              <span>Reset & Restore Operations</span>
            </button>
          )}
        </div>
      </div>

      {/* Zero Cost Cloud Architecture Guide */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <ShieldCheck size={18} color="var(--cyber-cyan)" />
            <span>₹0/Month Cloud Deployment Architecture</span>
          </div>
        </div>
        <div style={{ fontSize: '0.85rem', color: '#CBD5E1', lineHeight: 1.6 }}>
          <p style={{ marginBottom: 10 }}>
            <b>Free Tier Realities & Autonomous Scheduling:</b>
          </p>
          <ul style={{ paddingLeft: 20, marginBottom: 14 }}>
            <li><b>Free Web Services (Render / Fly.io / Koyeb):</b> Free web instances sleep after 15 minutes of inactivity and do not support 24/7 background worker daemons for ₹0.</li>
            <li><b>Autonomous Cloud Scheduling (Best ₹0 Solution):</b> Use <b>GitHub Actions cron workflows</b> (`schedule: - cron: '0 2 * * *'`). GitHub Actions provides 2,000 free runner minutes/month for private repositories and unlimited runner minutes for public repositories. Scheduled jobs run headless in the cloud without requiring your Windows PC to remain powered on.</li>
            <li><b>Database Persistence:</b> Neon.tech or Supabase offer generous ₹0 PostgreSQL tiers with persistent storage.</li>
          </ul>
        </div>
      </div>
    </div>
  );
};
