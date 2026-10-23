import React from 'react';
import { 
  Cpu, Compass, Globe, Code, Smartphone, Cloud, Bot, 
  Layers, CheckCircle, FileText, ShieldAlert 
} from 'lucide-react';

export const AgentActivity: React.FC = () => {
  const agents = [
    {
      role: 'Planning Agent',
      icon: Compass,
      color: 'var(--cyber-cyan)',
      desc: 'Inspects scope registry, selects authorized security checks, enforces rate limits and fail-closed policies.',
      guardrail: 'Cannot expand target scope or override policy prohibitions.'
    },
    {
      role: 'Web Analysis Agent',
      icon: Globe,
      color: 'var(--cyber-blue)',
      desc: 'Executes non-destructive HTTP requests with strict SSRF and redirect validation, checks headers, TLS, and cookies.',
      guardrail: 'Blocks private IPs, link-local, and cloud metadata (169.254.169.254).'
    },
    {
      role: 'Code Analysis Agent',
      icon: Code,
      color: 'var(--cyber-emerald)',
      desc: 'Executes Bandit Python security AST, Semgrep rules, and OSV dependency vulnerability audits.',
      guardrail: 'Treats code text as untrusted. Never executes untrusted repository scripts.'
    },
    {
      role: 'Mobile Analysis Agent',
      icon: Smartphone,
      color: 'var(--cyber-purple)',
      desc: 'Performs static analysis of APK archives and AndroidManifest.xml (exported components, debuggable flags).',
      guardrail: 'Static extraction only. Never installs or launches third-party APKs.'
    },
    {
      role: 'Cloud Analysis Agent',
      icon: Cloud,
      color: 'var(--cyber-amber)',
      desc: 'Reviews Terraform, CloudFormation, Kubernetes, and Dockerfile IaC configurations for public exposure.',
      guardrail: 'Static inspection only. Never modifies live cloud resources.'
    },
    {
      role: 'AI Security Agent',
      icon: Bot,
      color: 'var(--cyber-cyan)',
      desc: 'Analyzes prompt injection boundaries, unsanitized LLM output passing to eval/exec, and hardcoded API tokens.',
      guardrail: 'Uses synthetic test vectors only. No data extraction or model subversion.'
    },
    {
      role: 'Correlation Agent',
      icon: Layers,
      color: '#38BDF8',
      desc: 'Groups related observations across multiple tools, merges duplicate findings sharing common root causes.',
      guardrail: 'Deterministic deduplication across target assets.'
    },
    {
      role: 'Verification Agent',
      icon: CheckCircle,
      color: 'var(--cyber-emerald)',
      desc: 'Inspects repeatable evidence before updating status from Detected to Verified in Authorized Environment.',
      guardrail: 'Never marks verified solely based on AI prediction.'
    },
    {
      role: 'Reporting Agent',
      icon: FileText,
      color: '#CBD5E1',
      desc: 'Generates structured JSON exports and ReportLab PDF documents for human review and notification alerts.',
      guardrail: 'Drafts for human review only; no automatic submissions.'
    }
  ];

  return (
    <div>
      <div style={{ marginBottom: 20 }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#FFFFFF' }}>Multi-Agent Orchestration Architecture</h2>
        <p style={{ fontSize: '0.82rem', color: '#94A3B8' }}>
          Autonomous, bounded agent logical roles with evidence validation and hard guardrails.
        </p>
      </div>

      <div style={{
        padding: 14,
        borderRadius: 8,
        backgroundColor: 'rgba(0, 240, 255, 0.05)',
        border: '1px solid var(--border-active)',
        marginBottom: 24,
        display: 'flex',
        alignItems: 'center',
        gap: 12
      }}>
        <ShieldAlert size={22} color="var(--cyber-cyan)" />
        <div style={{ fontSize: '0.85rem', color: '#E2E8F0' }}>
          <b>Security Architecture Principles:</b> Bounded task iterations &bull; Per-job timeouts (900s) &bull; Maximum retry counts (3) &bull; No unrestricted command execution &bull; No autonomous changes to target systems.
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 16 }}>
        {agents.map((ag) => {
          const Icon = ag.icon;
          return (
            <div key={ag.role} className="card" style={{ marginBottom: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
                <div style={{
                  width: 36,
                  height: 36,
                  borderRadius: 8,
                  backgroundColor: 'rgba(255, 255, 255, 0.04)',
                  border: `1px solid ${ag.color}`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: ag.color
                }}>
                  <Icon size={20} />
                </div>
                <div>
                  <div style={{ fontWeight: 700, fontSize: '0.95rem', color: '#FFFFFF' }}>{ag.role}</div>
                  <span className="badge badge-info" style={{ fontSize: '0.68rem' }}>AUTONOMOUS AGENT</span>
                </div>
              </div>

              <p style={{ fontSize: '0.82rem', color: '#CBD5E1', marginBottom: 12, lineHeight: 1.4 }}>
                {ag.desc}
              </p>

              <div style={{
                padding: '6px 10px',
                borderRadius: 4,
                backgroundColor: 'rgba(0, 0, 0, 0.3)',
                borderLeft: `2px solid ${ag.color}`,
                fontSize: '0.74rem',
                color: '#94A3B8'
              }}>
                <b>Guardrail:</b> {ag.guardrail}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
