import React, { useEffect, useState } from 'react';
import { Mail, Send, CheckCircle, RefreshCw, AlertCircle } from 'lucide-react';
import { NotificationLog } from '../types';
import { api } from '../services/api';

export const EmailSettings: React.FC = () => {
  const [config, setConfig] = useState<any>(null);
  const [logs, setLogs] = useState<NotificationLog[]>([]);
  const [testEmailAddress, setTestEmailAddress] = useState('');
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [loading, setLoading] = useState(false);
  const [smtpHost, setSmtpHost] = useState('');
  const [smtpPort, setSmtpPort] = useState(587);
  const [smtpUser, setSmtpUser] = useState('');
  const [smtpPass, setSmtpPass] = useState('');
  const [smtpFrom, setSmtpFrom] = useState('');
  const [notifyTo, setNotifyTo] = useState('');

  const loadData = async () => {
    try {
      const [cfg, lgs] = await Promise.all([
        api.getConfig(),
        api.getNotifications()
      ]);
      setConfig(cfg);
      setLogs(lgs);
      if (cfg) {
        setSmtpHost(cfg.smtp_host === 'Not configured' ? '' : cfg.smtp_host);
        setSmtpPort(cfg.smtp_port || 587);
        setSmtpFrom(cfg.smtp_from === 'Not configured' ? '' : cfg.smtp_from);
        setNotifyTo(cfg.notification_email_to === 'Not configured' ? '' : cfg.notification_email_to);
        if (cfg.notification_email_to && cfg.notification_email_to !== 'Not configured') {
          setTestEmailAddress(cfg.notification_email_to);
        }
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSaveSmtp = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.updateSmtp({
        smtp_host: smtpHost,
        smtp_port: smtpPort,
        smtp_user: smtpUser,
        smtp_password: smtpPass || undefined,
        smtp_from: smtpFrom,
        notification_email_to: notifyTo,
        smtp_tls: true
      });
      alert('SMTP settings updated successfully!');
      loadData();
    } catch (err: any) {
      alert(`Save failed: ${err.message}`);
    }
  };

  const handleTestEmail = async () => {
    if (!testEmailAddress) {
      alert('Please enter a recipient email for testing.');
      return;
    }
    try {
      setLoading(true);
      setTestResult(null);
      const res = await api.testEmail(testEmailAddress);
      setTestResult(res);
      loadData();
    } catch (err: any) {
      setTestResult({ success: false, message: err.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: 20 }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#FFFFFF' }}>Email Alerts & Notifications</h2>
        <p style={{ fontSize: '0.82rem', color: '#94A3B8' }}>
          Configurable SMTP dispatch with duplicate notification suppression and persistent audit logs.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: 20, marginBottom: 24 }}>
        {/* SMTP Config Form */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <Mail size={18} color="var(--cyber-cyan)" />
              <span>SMTP Server Settings</span>
            </div>
            <span className="badge badge-info">{config?.smtp_configured ? 'Configured' : 'Local Log Mode'}</span>
          </div>

          <form onSubmit={handleSaveSmtp}>
            <div className="form-group">
              <label className="form-label">SMTP Host (e.g. smtp.gmail.com)</label>
              <input
                type="text"
                className="form-control"
                placeholder="smtp.example.com"
                value={smtpHost}
                onChange={(e) => setSmtpHost(e.target.value)}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <div className="form-group">
                <label className="form-label">Port</label>
                <input
                  type="number"
                  className="form-control"
                  value={smtpPort}
                  onChange={(e) => setSmtpPort(parseInt(e.target.value))}
                />
              </div>
              <div className="form-group">
                <label className="form-label">TLS Security</label>
                <input type="text" className="form-control" value="STARTTLS Enabled" disabled />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">SMTP Username</label>
              <input
                type="text"
                className="form-control"
                placeholder="user@example.com"
                value={smtpUser}
                onChange={(e) => setSmtpUser(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">SMTP Password</label>
              <input
                type="password"
                className="form-control"
                placeholder="Leave blank to keep current password"
                value={smtpPass}
                onChange={(e) => setSmtpPass(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">From Address</label>
              <input
                type="email"
                className="form-control"
                placeholder="vulnai-alerts@example.com"
                value={smtpFrom}
                onChange={(e) => setSmtpFrom(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Default Alert Recipient</label>
              <input
                type="email"
                className="form-control"
                placeholder="security-lead@example.com"
                value={notifyTo}
                onChange={(e) => setNotifyTo(e.target.value)}
              />
            </div>

            <button type="submit" className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }}>
              Save Configuration
            </button>
          </form>
        </div>

        {/* Test Email & Status */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <Send size={18} color="var(--cyber-emerald)" />
              <span>Test Email Dispatch</span>
            </div>
          </div>

          <p style={{ fontSize: '0.85rem', color: '#94A3B8', marginBottom: 16 }}>
            Send a test notification to verify SMTP routing and template formatting without triggering a full research job.
          </p>

          <div className="form-group">
            <label className="form-label">Test Recipient Email</label>
            <input
              type="email"
              className="form-control"
              placeholder="your-email@example.com"
              value={testEmailAddress}
              onChange={(e) => setTestEmailAddress(e.target.value)}
            />
          </div>

          <button
            className="btn btn-secondary"
            onClick={handleTestEmail}
            disabled={loading || !testEmailAddress}
            style={{ width: '100%', justifyContent: 'center', marginBottom: 16 }}
          >
            <Send size={14} />
            <span>{loading ? 'Dispatching...' : 'Dispatch Test Alert'}</span>
          </button>

          {testResult && (
            <div style={{
              padding: 12,
              borderRadius: 6,
              border: `1px solid ${testResult.success ? 'var(--cyber-emerald)' : 'var(--cyber-crimson)'}`,
              backgroundColor: testResult.success ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
              fontSize: '0.82rem',
              color: '#FFFFFF'
            }}>
              <b>{testResult.success ? 'Success:' : 'Error:'}</b> {testResult.message}
            </div>
          )}

          <div style={{ marginTop: 24, padding: 14, borderRadius: 8, backgroundColor: 'rgba(255, 255, 255, 0.02)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontWeight: 600, fontSize: '0.82rem', color: '#FFFFFF', marginBottom: 6 }}>
              Notification Safeguards
            </div>
            <ul style={{ fontSize: '0.75rem', color: '#94A3B8', paddingLeft: 18, lineHeight: 1.5 }}>
              <li>Duplicate alerts for identical findings suppressed within 30 min window.</li>
              <li>Secrets and API credentials automatically redacted from email bodies.</li>
              <li>All dispatch attempts logged permanently in audit records.</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Notification Log History */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <span>Notification Audit History</span>
            <span style={{ fontSize: '0.75rem', color: '#64748B' }}>({logs.length} events)</span>
          </div>
        </div>

        <div className="table-responsive">
          <table className="cyber-table">
            <thead>
              <tr>
                <th>Recipient</th>
                <th>Subject</th>
                <th>Event Type</th>
                <th>Status</th>
                <th>Sent At</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id}>
                  <td style={{ color: '#38BDF8', fontFamily: 'monospace' }}>{log.recipient}</td>
                  <td style={{ fontWeight: 600, color: '#FFFFFF' }}>{log.subject}</td>
                  <td>
                    <span className="badge badge-info">{log.event_type}</span>
                  </td>
                  <td>
                    {log.status === 'sent' && <span className="badge badge-verified">Sent</span>}
                    {log.status === 'suppressed' && <span className="badge badge-high">Suppressed</span>}
                    {log.status === 'failed' && <span className="badge badge-critical">Failed</span>}
                  </td>
                  <td style={{ fontSize: '0.78rem', color: '#94A3B8' }}>
                    {new Date(log.sent_at).toLocaleString()}
                  </td>
                </tr>
              ))}
              {logs.length === 0 && (
                <tr>
                  <td colSpan={5} style={{ textAlign: 'center', padding: 24, color: '#64748B' }}>
                    No notification history recorded yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
