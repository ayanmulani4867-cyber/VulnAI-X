import React, { useEffect, useState } from 'react';
import { AlertTriangle, Eye, Filter, RefreshCw, CheckCircle, ShieldAlert } from 'lucide-react';
import { Finding, FindingStatus } from '../types';
import { SeverityBadge, StatusBadge } from '../components/Badges';
import { api } from '../services/api';

export const Findings: React.FC = () => {
  const [findings, setFindings] = useState<Finding[]>([]);
  const [loading, setLoading] = useState(true);
  const [severityFilter, setSeverityFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [newStatus, setNewStatus] = useState<FindingStatus>('Detected');
  const [fpReason, setFpReason] = useState('');

  const loadFindings = async () => {
    try {
      setLoading(true);
      const data = await api.getFindings({
        severity: severityFilter || undefined,
        status_filter: statusFilter || undefined
      });
      setFindings(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFindings();
  }, [severityFilter, statusFilter]);

  const handleOpenDetail = (f: Finding) => {
    setSelectedFinding(f);
    setNewStatus(f.status);
    setFpReason(f.false_positive_reason || '');
    setShowDetailModal(true);
  };

  const handleUpdateStatus = async () => {
    if (!selectedFinding) return;
    try {
      const updated = await api.updateFinding(selectedFinding.id, {
        status: newStatus,
        false_positive_reason: newStatus === 'False Positive' ? fpReason : undefined
      });
      setSelectedFinding(updated);
      setShowDetailModal(false);
      loadFindings();
    } catch (err: any) {
      alert(`Update failed: ${err.message}`);
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#FFFFFF' }}>Vulnerability Findings & Evidence</h2>
          <p style={{ fontSize: '0.82rem', color: '#94A3B8' }}>
            Correlated observations, verification statuses, and repeatable reproduction evidence.
          </p>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={loadFindings}>
          <RefreshCw size={14} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Filter Bar */}
      <div className="filter-bar">
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#94A3B8', fontSize: '0.85rem' }}>
          <Filter size={16} />
          <span>Filters:</span>
        </div>

        <select 
          className="form-control" 
          style={{ width: 'auto', padding: '6px 12px' }}
          value={severityFilter} 
          onChange={(e) => setSeverityFilter(e.target.value)}
        >
          <option value="">All Severities</option>
          <option value="Critical">Critical</option>
          <option value="High">High</option>
          <option value="Medium">Medium</option>
          <option value="Low">Low</option>
          <option value="Informational">Informational</option>
        </select>

        <select 
          className="form-control" 
          style={{ width: 'auto', padding: '6px 12px' }}
          value={statusFilter} 
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="">All Statuses</option>
          <option value="Detected">Detected</option>
          <option value="Needs Investigation">Needs Investigation</option>
          <option value="Verified in Authorized Environment">Verified</option>
          <option value="False Positive">False Positive</option>
          <option value="Fixed">Fixed</option>
          <option value="Retest Required">Retest Required</option>
        </select>
      </div>

      {/* Findings Table */}
      <div className="card">
        <div className="table-responsive">
          <table className="cyber-table">
            <thead>
              <tr>
                <th>Severity</th>
                <th>Title & Category</th>
                <th>Confidence</th>
                <th>Status</th>
                <th>Target Asset</th>
                <th>Tool / Rule</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {findings.map((f) => (
                <tr key={f.id}>
                  <td>
                    <SeverityBadge severity={f.severity} />
                  </td>
                  <td>
                    <div style={{ fontWeight: 600, color: '#FFFFFF' }}>{f.title}</div>
                    <div style={{ fontSize: '0.75rem', color: '#94A3B8' }}>{f.category}</div>
                  </td>
                  <td>
                    <span style={{ fontSize: '0.8rem', color: f.confidence === 'Certain' ? '#6EE7B7' : '#CBD5E1' }}>
                      {f.confidence}
                    </span>
                  </td>
                  <td>
                    <StatusBadge status={f.status} />
                  </td>
                  <td style={{ fontSize: '0.78rem', color: '#38BDF8', fontFamily: 'monospace' }}>
                    {f.target}
                  </td>
                  <td style={{ fontSize: '0.75rem', color: '#64748B' }}>
                    {f.tool_name} / {f.rule_id}
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <button className="btn btn-secondary btn-sm" onClick={() => handleOpenDetail(f)}>
                      <Eye size={13} />
                      <span>Inspect</span>
                    </button>
                  </td>
                </tr>
              ))}
              {findings.length === 0 && (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: 30, color: '#64748B' }}>
                    No security findings matching the criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Detailed Finding Modal */}
      {showDetailModal && selectedFinding && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ maxWidth: 750 }}>
            <div className="modal-header">
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <SeverityBadge severity={selectedFinding.severity} />
                  <StatusBadge status={selectedFinding.status} />
                  <span style={{ fontSize: '0.8rem', color: '#94A3B8' }}>Confidence: <b>{selectedFinding.confidence}</b></span>
                </div>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#FFFFFF', marginTop: 6 }}>
                  {selectedFinding.title}
                </h3>
              </div>
              <button onClick={() => setShowDetailModal(false)} style={{ background: 'none', border: 'none', color: '#94A3B8', cursor: 'pointer' }}>✕</button>
            </div>

            <div className="modal-body">
              <div style={{ marginBottom: 14 }}>
                <span style={{ fontSize: '0.78rem', color: '#64748B', textTransform: 'uppercase', fontWeight: 600 }}>Target Asset</span>
                <div style={{ color: '#38BDF8', fontFamily: 'monospace', fontSize: '0.9rem' }}>{selectedFinding.target}</div>
              </div>

              <div style={{ marginBottom: 14 }}>
                <span style={{ fontSize: '0.78rem', color: '#64748B', textTransform: 'uppercase', fontWeight: 600 }}>Repeatable Evidence</span>
                <pre className="code-box" style={{ marginTop: 4, maxHeight: 180 }}>
                  {selectedFinding.evidence_summary}
                </pre>
              </div>

              {selectedFinding.reproduction_steps && (
                <div style={{ marginBottom: 14 }}>
                  <span style={{ fontSize: '0.78rem', color: '#64748B', textTransform: 'uppercase', fontWeight: 600 }}>Reproduction Steps (Safe / Authorized)</span>
                  <div style={{ fontSize: '0.85rem', color: '#E2E8F0', marginTop: 4 }}>
                    {selectedFinding.reproduction_steps}
                  </div>
                </div>
              )}

              {selectedFinding.remediation && (
                <div style={{ marginBottom: 14 }}>
                  <span style={{ fontSize: '0.78rem', color: '#64748B', textTransform: 'uppercase', fontWeight: 600 }}>Remediation Guidance</span>
                  <div style={{ fontSize: '0.85rem', color: '#6EE7B7', marginTop: 4 }}>
                    {selectedFinding.remediation}
                  </div>
                </div>
              )}

              {/* Status Update Form */}
              <div style={{ padding: 14, borderRadius: 8, backgroundColor: 'rgba(255, 255, 255, 0.03)', border: '1px solid var(--border-subtle)', marginTop: 16 }}>
                <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#FFFFFF', display: 'block', marginBottom: 10 }}>
                  Review & Verification State
                </span>
                <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                  <select
                    className="form-control"
                    value={newStatus}
                    onChange={(e) => setNewStatus(e.target.value as any)}
                  >
                    <option value="Detected">Detected</option>
                    <option value="Needs Investigation">Needs Investigation</option>
                    <option value="Verification Pending">Verification Pending</option>
                    <option value="Verified in Authorized Environment">Verified in Authorized Environment</option>
                    <option value="False Positive">False Positive</option>
                    <option value="Fixed">Fixed</option>
                    <option value="Retest Required">Retest Required</option>
                  </select>

                  <button className="btn btn-primary btn-sm" onClick={handleUpdateStatus}>
                    Update Status
                  </button>
                </div>

                {newStatus === 'False Positive' && (
                  <div style={{ marginTop: 10 }}>
                    <input
                      type="text"
                      className="form-control"
                      placeholder="Reason for classifying as false positive..."
                      value={fpReason}
                      onChange={(e) => setFpReason(e.target.value)}
                    />
                  </div>
                )}
              </div>
            </div>

            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowDetailModal(false)}>Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
