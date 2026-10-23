import React, { useEffect, useState } from 'react';
import { ShieldCheck, Plus, CheckCircle, PauseCircle, Trash2, ExternalLink } from 'lucide-react';
import { AuthorizedProgram, ScopeEntry } from '../types';
import { api } from '../services/api';

export const ScopeManager: React.FC<{ onOpenCheck: () => void }> = ({ onOpenCheck }) => {
  const [programs, setPrograms] = useState<AuthorizedProgram[]>([]);
  const [scopes, setScopes] = useState<ScopeEntry[]>([]);
  const [selectedProgramId, setSelectedProgramId] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);

  // New scope form
  const [targetType, setTargetType] = useState<'domain' | 'wildcard_domain' | 'url_prefix' | 'repository' | 'android_package' | 'cloud_config'>('wildcard_domain');
  const [targetValue, setTargetValue] = useState('');
  const [permitted, setPermitted] = useState('passive,headers,tls,code_review');
  const [prohibited, setProhibited] = useState('dos,brute_force,credential_stuffing,data_exfiltration');
  const [rateLimit, setRateLimit] = useState(1.0);
  const [authRef, setAuthRef] = useState('');

  const loadData = async () => {
    try {
      setLoading(true);
      const [pData, sData] = await Promise.all([
        api.getPrograms(),
        api.getScopes(selectedProgramId || undefined)
      ]);
      setPrograms(pData);
      setScopes(sData);
      if (!selectedProgramId && pData.length > 0) {
        setSelectedProgramId(pData[0].id);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedProgramId]);

  const handleToggleStatus = async (scope: ScopeEntry) => {
    try {
      const newStatus = scope.status === 'active' ? 'paused' : 'active';
      await api.updateScope(scope.id, { status: newStatus });
      loadData();
    } catch (err) {
      alert('Failed to update scope status');
    }
  };

  const handleDelete = async (scopeId: string) => {
    if (!confirm('Are you sure you want to remove this scope entry?')) return;
    try {
      await api.deleteScope(scopeId);
      loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to delete scope');
    }
  };

  const handleCreateScope = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProgramId || !targetValue || !authRef) {
      alert('Please fill in all mandatory fields.');
      return;
    }

    try {
      await api.createScope({
        program_id: selectedProgramId,
        target_type: targetType,
        target_value: targetValue,
        permitted_methods: permitted,
        prohibited_methods: prohibited,
        rate_limit_rps: rateLimit,
        authorization_reference: authRef,
        status: 'active'
      });
      setShowAddModal(false);
      setTargetValue('');
      setAuthRef('');
      loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to create scope');
    }
  };

  return (
    <div>
      {/* Header Controls */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#FFFFFF' }}>Authorization & Scope Registry</h2>
          <p style={{ fontSize: '0.82rem', color: '#94A3B8' }}>
            Mandatory scope catalog. All research operations fail closed unless authorized here.
          </p>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn btn-secondary" onClick={onOpenCheck}>
            <ShieldCheck size={16} />
            <span>Pre-Flight Scope Test</span>
          </button>
          <button className="btn btn-primary" onClick={() => setShowAddModal(true)}>
            <Plus size={16} />
            <span>Register New Scope</span>
          </button>
        </div>
      </div>

      {/* Program Selector Tabs */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
        {programs.map((p) => (
          <button
            key={p.id}
            onClick={() => setSelectedProgramId(p.id)}
            style={{
              padding: '10px 18px',
              borderRadius: 8,
              border: `1px solid ${selectedProgramId === p.id ? 'var(--cyber-cyan)' : 'var(--border-subtle)'}`,
              backgroundColor: selectedProgramId === p.id ? 'rgba(0, 240, 255, 0.1)' : 'var(--bg-card)',
              color: selectedProgramId === p.id ? '#FFFFFF' : '#94A3B8',
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: '0.9rem',
              display: 'flex',
              alignItems: 'center',
              gap: 8
            }}
          >
            <ShieldCheck size={16} color={selectedProgramId === p.id ? 'var(--cyber-cyan)' : '#64748B'} />
            <span>{p.name}</span>
          </button>
        ))}
      </div>

      {/* Scope Table */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <span>Authorized Scope Entries</span>
            <span style={{ fontSize: '0.8rem', color: '#64748B', fontWeight: 400 }}>({scopes.length} targets)</span>
          </div>
        </div>

        <div className="table-responsive">
          <table className="cyber-table">
            <thead>
              <tr>
                <th>Target Asset</th>
                <th>Type</th>
                <th>Permitted Methods</th>
                <th>Rate Limit</th>
                <th>Authorization Policy Reference</th>
                <th>Status</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {scopes.map((s) => (
                <tr key={s.id}>
                  <td style={{ fontWeight: 600, color: '#38BDF8', fontFamily: 'monospace' }}>
                    {s.target_value}
                  </td>
                  <td>
                    <span className="badge badge-info">{s.target_type}</span>
                  </td>
                  <td style={{ fontSize: '0.78rem', color: '#CBD5E1', maxWidth: 200 }}>
                    {s.permitted_methods}
                  </td>
                  <td style={{ fontSize: '0.8rem', color: '#94A3B8' }}>
                    {s.rate_limit_rps} req/sec
                  </td>
                  <td style={{ fontSize: '0.8rem', color: '#E2E8F0', maxWidth: 220 }}>
                    {s.authorization_reference}
                  </td>
                  <td>
                    {s.status === 'active' ? (
                      <span className="badge badge-verified">Active</span>
                    ) : (
                      <span className="badge badge-high">{s.status}</span>
                    )}
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <div style={{ display: 'inline-flex', gap: 8 }}>
                      <button 
                        className="btn btn-secondary btn-sm"
                        onClick={() => handleToggleStatus(s)}
                        title={s.status === 'active' ? 'Pause Scope' : 'Activate Scope'}
                      >
                        {s.status === 'active' ? <PauseCircle size={14} /> : <CheckCircle size={14} />}
                        <span>{s.status === 'active' ? 'Pause' : 'Activate'}</span>
                      </button>
                      <button 
                        className="btn btn-danger btn-sm"
                        onClick={() => handleDelete(s.id)}
                        title="Delete Scope"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {scopes.length === 0 && (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: 30, color: '#64748B' }}>
                    No authorized scopes configured for this program. Add one to enable research testing.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Scope Modal */}
      {showAddModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#FFFFFF' }}>Register Authorized Target Scope</h3>
              <button onClick={() => setShowAddModal(false)} style={{ background: 'none', border: 'none', color: '#94A3B8', cursor: 'pointer' }}>✕</button>
            </div>
            <form onSubmit={handleCreateScope}>
              <div className="modal-body">
                <div className="form-group">
                  <label className="form-label">Program</label>
                  <select 
                    className="form-control"
                    value={selectedProgramId} 
                    onChange={(e) => setSelectedProgramId(e.target.value)}
                  >
                    {programs.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Asset Type</label>
                  <select 
                    className="form-control"
                    value={targetType} 
                    onChange={(e) => setTargetType(e.target.value as any)}
                  >
                    <option value="wildcard_domain">Wildcard Domain (*.example.com)</option>
                    <option value="domain">Exact Domain (example.com)</option>
                    <option value="url_prefix">URL Prefix (https://example.com/api/v1)</option>
                    <option value="repository">Source Repository / Local Path</option>
                    <option value="android_package">Android Package / APK File</option>
                    <option value="cloud_config">Cloud IaC Configuration File</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Target Pattern / Value</label>
                  <input
                    type="text"
                    className="form-control"
                    placeholder="e.g. *.google.com or https://meta.com"
                    value={targetValue}
                    onChange={(e) => setTargetValue(e.target.value)}
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Permitted Methods (Comma-separated)</label>
                  <input
                    type="text"
                    className="form-control"
                    value={permitted}
                    onChange={(e) => setPermitted(e.target.value)}
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Prohibited Methods (Strictly Enforced)</label>
                  <input
                    type="text"
                    className="form-control"
                    value={prohibited}
                    onChange={(e) => setProhibited(e.target.value)}
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Max Rate Limit (Requests per second)</label>
                  <input
                    type="number"
                    step="0.5"
                    className="form-control"
                    value={rateLimit}
                    onChange={(e) => setRateLimit(parseFloat(e.target.value))}
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Authorization / Bug Bounty Policy Reference</label>
                  <input
                    type="text"
                    className="form-control"
                    placeholder="e.g. Google Bughunters Rules Section 2.1"
                    value={authRef}
                    onChange={(e) => setAuthRef(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowAddModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Save to Registry</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
