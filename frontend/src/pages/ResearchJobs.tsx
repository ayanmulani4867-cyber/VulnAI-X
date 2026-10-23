import React, { useEffect, useState } from 'react';
import { PlayCircle, StopCircle, RefreshCw, Plus, Terminal, AlertCircle } from 'lucide-react';
import { ResearchJob, JobAttempt } from '../types';
import { JobStatusBadge } from '../components/Badges';
import { api } from '../services/api';

export const ResearchJobs: React.FC<{ onOpenNewJob: () => void }> = ({ onOpenNewJob }) => {
  const [jobs, setJobs] = useState<ResearchJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedJob, setSelectedJob] = useState<ResearchJob | null>(null);
  const [attempts, setAttempts] = useState<JobAttempt[]>([]);
  const [showLogsModal, setShowLogsModal] = useState(false);
  const [runningJobId, setRunningJobId] = useState<string | null>(null);

  const fetchJobs = async () => {
    try {
      setLoading(true);
      const data = await api.getJobs();
      setJobs(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 8000); // 8s auto refresh
    return () => clearInterval(interval);
  }, []);

  const handleRunNow = async (jobId: string) => {
    try {
      setRunningJobId(jobId);
      const res = await api.runJobNow(jobId);
      alert(`Job executed successfully! Findings discovered: ${res.findings_count ?? 0}`);
      fetchJobs();
    } catch (err: any) {
      alert(`Execution Error: ${err.message}`);
    } finally {
      setRunningJobId(null);
    }
  };

  const handleCancel = async (jobId: string) => {
    try {
      await api.cancelJob(jobId);
      fetchJobs();
    } catch (err: any) {
      alert(`Failed to cancel: ${err.message}`);
    }
  };

  const handleViewLogs = async (job: ResearchJob) => {
    setSelectedJob(job);
    try {
      const atts = await api.getJobAttempts(job.id);
      setAttempts(atts);
      setShowLogsModal(true);
    } catch (err) {
      alert('Failed to load job attempt logs');
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#FFFFFF' }}>Research Jobs Queue</h2>
          <p style={{ fontSize: '0.82rem', color: '#94A3B8' }}>
            Persistent background jobs, multi-agent orchestration, retry handling & recovery.
          </p>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn btn-secondary btn-sm" onClick={fetchJobs}>
            <RefreshCw size={14} />
            <span>Refresh</span>
          </button>
          <button className="btn btn-primary" onClick={onOpenNewJob}>
            <Plus size={16} />
            <span>New Research Job</span>
          </button>
        </div>
      </div>

      <div className="card">
        <div className="table-responsive">
          <table className="cyber-table">
            <thead>
              <tr>
                <th>Job Title & Target</th>
                <th>Module</th>
                <th>Status</th>
                <th>Retries</th>
                <th>Created At</th>
                <th>Findings</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((job) => (
                <tr key={job.id}>
                  <td>
                    <div style={{ fontWeight: 600, color: '#FFFFFF' }}>{job.title}</div>
                    <div style={{ fontSize: '0.78rem', color: '#38BDF8', fontFamily: 'monospace' }}>
                      {job.target}
                    </div>
                    {job.error_message && (
                      <div style={{ fontSize: '0.72rem', color: 'var(--cyber-crimson)', display: 'flex', alignItems: 'center', gap: 4, marginTop: 4 }}>
                        <AlertCircle size={12} />
                        <span>{job.error_message}</span>
                      </div>
                    )}
                  </td>
                  <td>
                    <span className="badge badge-info" style={{ textTransform: 'uppercase' }}>
                      {job.module_type}
                    </span>
                  </td>
                  <td>
                    <JobStatusBadge status={job.status} />
                  </td>
                  <td style={{ fontSize: '0.8rem', color: '#94A3B8' }}>
                    {job.retry_count} / {job.max_retries}
                  </td>
                  <td style={{ fontSize: '0.78rem', color: '#64748B' }}>
                    {new Date(job.created_at).toLocaleString()}
                  </td>
                  <td>
                    <span style={{ fontWeight: 700, color: (job.findings_count ?? 0) > 0 ? 'var(--cyber-cyan)' : '#64748B' }}>
                      {job.findings_count ?? 0}
                    </span>
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <div style={{ display: 'inline-flex', gap: 8 }}>
                      {job.status === 'queued' && (
                        <button
                          className="btn btn-primary btn-sm"
                          onClick={() => handleRunNow(job.id)}
                          disabled={runningJobId === job.id}
                        >
                          <PlayCircle size={13} />
                          <span>{runningJobId === job.id ? 'Running...' : 'Run Now'}</span>
                        </button>
                      )}
                      {(job.status === 'queued' || job.status === 'running') && (
                        <button
                          className="btn btn-danger btn-sm"
                          onClick={() => handleCancel(job.id)}
                        >
                          <StopCircle size={13} />
                          <span>Cancel</span>
                        </button>
                      )}
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => handleViewLogs(job)}
                      >
                        <Terminal size={13} />
                        <span>Logs</span>
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {jobs.length === 0 && (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: 30, color: '#64748B' }}>
                    No research jobs found. Launch one above.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Logs Modal */}
      {showLogsModal && selectedJob && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ maxWidth: 750 }}>
            <div className="modal-header">
              <div>
                <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#FFFFFF' }}>
                  Execution Logs: {selectedJob.title}
                </h3>
                <span style={{ fontSize: '0.75rem', color: 'var(--cyber-cyan)' }}>Target: {selectedJob.target}</span>
              </div>
              <button onClick={() => setShowLogsModal(false)} style={{ background: 'none', border: 'none', color: '#94A3B8', cursor: 'pointer' }}>✕</button>
            </div>
            <div className="modal-body">
              {attempts.length > 0 ? (
                attempts.map((att) => (
                  <div key={att.id} style={{ marginBottom: 16 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4, fontSize: '0.8rem', color: '#94A3B8' }}>
                      <span>Attempt #{att.attempt_number} (Status: <b>{att.status}</b>)</span>
                      <span>Started: {new Date(att.started_at).toLocaleTimeString()}</span>
                    </div>
                    <pre className="code-box" style={{ maxHeight: 220 }}>
                      {att.logs || 'No output recorded.'}
                    </pre>
                  </div>
                ))
              ) : (
                <div style={{ padding: 20, textAlign: 'center', color: '#64748B' }}>
                  No execution attempts recorded for this job.
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowLogsModal(false)}>Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
