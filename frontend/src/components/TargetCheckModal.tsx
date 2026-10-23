import React, { useState } from 'react';
import { ShieldCheck, X, CheckCircle, AlertTriangle } from 'lucide-react';
import { AuthorizedProgram } from '../types';
import { api } from '../services/api';

interface TargetCheckModalProps {
  isOpen: boolean;
  onClose: () => void;
  programs: AuthorizedProgram[];
}

export const TargetCheckModal: React.FC<TargetCheckModalProps> = ({ isOpen, onClose, programs }) => {
  const [programId, setProgramId] = useState(programs[0]?.id || '');
  const [target, setTarget] = useState('');
  const [method, setMethod] = useState('passive');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ authorized: boolean; message: string; authorization_reference?: string } | null>(null);

  if (!isOpen) return null;

  const handleValidate = async () => {
    if (!programId || !target) return;
    try {
      setLoading(true);
      const res = await api.prevalidateTarget(programId, target, method);
      setResult(res);
    } catch (err: any) {
      setResult({ authorized: false, message: err.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: 'var(--cyber-cyan)' }}>
            <ShieldCheck size={22} />
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Pre-Flight Scope Verification</h3>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#94A3B8', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        <div className="modal-body">
          <p style={{ fontSize: '0.85rem', color: '#94A3B8', marginBottom: 16 }}>
            Verify whether a target URL or domain is explicitly authorized in the Scope Registry under an authorized bug bounty program policy (e.g. Google VRP, Meta Bug Bounty).
          </p>

          <div className="form-group">
            <label className="form-label">Authorized Program</label>
            <select className="form-control" value={programId} onChange={(e) => setProgramId(e.target.value)}>
              {programs.map((p) => (
                <option key={p.id} value={p.id}>{p.name} ({p.organization})</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Target Domain or URL</label>
            <input
              type="text"
              className="form-control"
              placeholder="e.g. https://bughunters.google.com or *.google.com"
              value={target}
              onChange={(e) => setTarget(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Requested Testing Method</label>
            <select className="form-control" value={method} onChange={(e) => setMethod(e.target.value)}>
              <option value="passive">Passive (Headers, TLS, Certificates, Robots)</option>
              <option value="code_review">Code Review / Static Analysis</option>
              <option value="dos">DoS / Load Testing (Strictly Prohibited)</option>
              <option value="brute_force">Brute Force (Strictly Prohibited)</option>
            </select>
          </div>

          {result && (
            <div style={{
              padding: 14,
              borderRadius: 8,
              border: `1px solid ${result.authorized ? 'var(--cyber-emerald)' : 'var(--cyber-crimson)'}`,
              backgroundColor: result.authorized ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
              marginTop: 16
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontWeight: 700, color: result.authorized ? '#6EE7B7' : '#FCA5A5' }}>
                {result.authorized ? <CheckCircle size={18} /> : <AlertTriangle size={18} />}
                <span>{result.authorized ? 'TARGET AUTHORIZED' : 'SCOPE ACCESS DENIED (FAIL-CLOSED)'}</span>
              </div>
              <div style={{ fontSize: '0.82rem', marginTop: 6, color: '#E2E8F0' }}>{result.message}</div>
              {result.authorization_reference && (
                <div style={{ fontSize: '0.75rem', marginTop: 4, color: '#94A3B8' }}>
                  Policy Reference: <b>{result.authorization_reference}</b>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>Close</button>
          <button className="btn btn-primary" onClick={handleValidate} disabled={loading || !target}>
            {loading ? 'Verifying...' : 'Check Scope Authorization'}
          </button>
        </div>
      </div>
    </div>
  );
};
