import React from 'react';
import { Severity, FindingStatus, JobStatus } from '../types';

export const SeverityBadge: React.FC<{ severity: Severity }> = ({ severity }) => {
  const map: Record<Severity, string> = {
    Critical: 'badge-critical',
    High: 'badge-high',
    Medium: 'badge-medium',
    Low: 'badge-low',
    Informational: 'badge-info'
  };

  return (
    <span className={`badge ${map[severity] || 'badge-info'}`}>
      {severity}
    </span>
  );
};

export const StatusBadge: React.FC<{ status: FindingStatus }> = ({ status }) => {
  if (status === 'Verified in Authorized Environment') {
    return <span className="badge badge-verified">Verified</span>;
  }
  if (status === 'False Positive') {
    return <span className="badge badge-false-positive">False Positive</span>;
  }
  if (status === 'Needs Investigation') {
    return <span className="badge badge-high">Investigation</span>;
  }
  return <span className="badge badge-detected">{status}</span>;
};

export const JobStatusBadge: React.FC<{ status: JobStatus }> = ({ status }) => {
  const map: Record<JobStatus, { class: string; label: string }> = {
    queued: { class: 'badge-info', label: 'Queued' },
    running: { class: 'badge-detected', label: 'Running...' },
    completed: { class: 'badge-verified', label: 'Completed' },
    failed: { class: 'badge-critical', label: 'Failed' },
    cancelled: { class: 'badge-false-positive', label: 'Cancelled' },
    timeout: { class: 'badge-high', label: 'Timeout' }
  };

  const item = map[status] || { class: 'badge-info', label: status };

  return (
    <span className={`badge ${item.class}`}>
      {item.label}
    </span>
  );
};
