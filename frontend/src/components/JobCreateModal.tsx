import React, { useState } from 'react';
import { PlayCircle, X } from 'lucide-react';
import { AuthorizedProgram } from '../types';
import { api } from '../services/api';

interface JobCreateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  programs: AuthorizedProgram[];
}

export const JobCreateModal: React.FC<JobCreateModalProps> = ({ isOpen, onClose, onSuccess, programs }) => {
  const [programId, setProgramId] = useState(programs[0]?.id || '');
  const [target, setTarget] = useState('');
  const [moduleType, setModuleType] = useState('web');
  const [title, setTitle] = useState('');
  const [isScheduled, setIsScheduled] = useState(false);
  const [cron, setCron] = useState('0 0 * * *');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!programId || !target) {
      setError('Program and Target are required.');
      return;
    }

    try {
      setLoading(true);
      setError('');
      await api.createJob({
        program_id: programId,
        target,
        module_type: moduleType,
        title: title || undefined,
        is_scheduled: isScheduled,
        cron_expression: isScheduled ? cron : undefined
      });
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to create job');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: 'var(--cyber-cyan)' }}>
            <PlayCircle size={22} />
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Launch Authorized Research Job</h3>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#94A3B8', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            {error && (
              <div style={{
                padding: '10px 14px',
                borderRadius: 6,
                backgroundColor: 'rgba(239, 68, 68, 0.15)',
                border: '1px solid var(--cyber-crimson)',
                color: '#FCA5A5',
                fontSize: '0.85rem',
                marginBottom: 16
              }}>
                {error}
              </div>
            )}

            <div className="form-group">
              <label className="form-label">Authorized Bug Bounty Program</label>
              <select 
                className="form-control" 
                value={programId} 
                onChange={(e) => setProgramId(e.target.value)}
                required
              >
                {programs.map((p) => (
                  <option key={p.id} value={p.id}>{p.name} ({p.organization})</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Target Asset (Domain, URL, or Repository)</label>
              <input
                type="text"
                className="form-control"
                placeholder="e.g. https://bughunters.google.com or backend/app"
                value={target}
                onChange={(e) => setTarget(e.target.value)}
                required
              />
              <span style={{ fontSize: '0.72rem', color: '#64748B', marginTop: 4, display: 'block' }}>
                Target must be pre-authorized in the Scope Registry. Out-of-scope targets fail closed.
              </span>
            </div>

            <div className="form-group">
              <label className="form-label">Research Module</label>
              <select className="form-control" value={moduleType} onChange={(e) => setModuleType(e.target.value)}>
                <option value="web">Web Security Research (Passive Headers, Cookies, TLS, Sensitive Paths)</option>
                <option value="code">Source Code & Dependency Audit (Semgrep, Bandit, OSV-Scanner)</option>
                <option value="mobile">Android Application Static Analysis (APKs & Manifest)</option>
                <option value="cloud">Cloud Configuration & IaC Review (Terraform, Docker, K8s)</option>
                <option value="ai_sec">AI Application Security (Prompt Injection, Unsafe Tool Handling)</option>
                <option value="full_suite">Full Orchestrated Suite (All permitted agents)</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Job Title (Optional)</label>
              <input
                type="text"
                className="form-control"
                placeholder="Auto-generated if left blank"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />
            </div>

            <div className="form-group" style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <input
                type="checkbox"
                id="isScheduled"
                checked={isScheduled}
                onChange={(e) => setIsScheduled(e.target.checked)}
                style={{ width: 16, height: 16, cursor: 'pointer' }}
              />
              <label htmlFor="isScheduled" style={{ fontSize: '0.85rem', color: '#CBD5E1', cursor: 'pointer' }}>
                Schedule recurring job (Background Autonomous Execution)
              </label>
            </div>

            {isScheduled && (
              <div className="form-group">
                <label className="form-label">Cron Expression</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="0 0 * * * (daily at midnight)"
                  value={cron}
                  onChange={(e) => setCron(e.target.value)}
                />
              </div>
            )}
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose} disabled={loading}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Validating & Queuing...' : 'Queue Research Job'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
