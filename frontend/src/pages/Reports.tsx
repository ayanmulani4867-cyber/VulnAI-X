import React, { useEffect, useState } from 'react';
import { FileText, Download, Code, ShieldAlert, CheckCircle2 } from 'lucide-react';
import { ResearchJob } from '../types';
import { api } from '../services/api';

export const Reports: React.FC = () => {
  const [jobs, setJobs] = useState<ResearchJob[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        const data = await api.getJobs();
        // Show jobs that are completed or have findings
        setJobs(data.filter(j => j.status === 'completed' || (j.findings_count ?? 0) > 0));
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const handleDownloadPdf = (jobId: string) => {
    const url = api.getPdfReportUrl(jobId);
    window.open(url, '_blank');
  };

  const handleDownloadJson = async (jobId: string) => {
    try {
      const data = await api.getJsonReport(jobId);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `vulnai_report_${jobId.slice(0, 8)}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err: any) {
      alert(`Export failed: ${err.message}`);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: 20 }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#FFFFFF' }}>Security Reports & Exports</h2>
        <p style={{ fontSize: '0.82rem', color: '#94A3B8' }}>
          Generate professional PDF vulnerability reports and structured JSON exports for human review.
        </p>
      </div>

      <div style={{
        padding: 16,
        borderRadius: 8,
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        border: '1px solid var(--border-subtle)',
        marginBottom: 20,
        display: 'flex',
        alignItems: 'center',
        gap: 12
      }}>
        <ShieldAlert size={24} color="var(--cyber-cyan)" />
        <div style={{ fontSize: '0.85rem', color: '#CBD5E1' }}>
          <b>Responsible Disclosure Notice:</b> Reports are generated as structured drafts for researcher verification. VulnAI X never submits reports to Google VRP, Meta Bug Bounty, or other programs automatically.
        </div>
      </div>

      <div className="card">
        <div className="table-responsive">
          <table className="cyber-table">
            <thead>
              <tr>
                <th>Job Title & Target</th>
                <th>Module</th>
                <th>Findings Count</th>
                <th>Completed At</th>
                <th style={{ textAlign: 'right' }}>Report Exports</th>
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
                  </td>
                  <td>
                    <span className="badge badge-info" style={{ textTransform: 'uppercase' }}>{job.module_type}</span>
                  </td>
                  <td>
                    <span style={{ fontWeight: 700, color: (job.findings_count ?? 0) > 0 ? 'var(--cyber-cyan)' : '#64748B' }}>
                      {job.findings_count ?? 0} findings
                    </span>
                  </td>
                  <td style={{ fontSize: '0.8rem', color: '#94A3B8' }}>
                    {job.completed_at ? new Date(job.completed_at).toLocaleString() : 'Recent'}
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <div style={{ display: 'inline-flex', gap: 8 }}>
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => handleDownloadJson(job.id)}
                      >
                        <Code size={13} />
                        <span>JSON</span>
                      </button>
                      <button
                        className="btn btn-primary btn-sm"
                        onClick={() => handleDownloadPdf(job.id)}
                      >
                        <Download size={13} />
                        <span>PDF Report</span>
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {jobs.length === 0 && (
                <tr>
                  <td colSpan={5} style={{ textAlign: 'center', padding: 30, color: '#64748B' }}>
                    No completed research jobs available for report generation.
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
