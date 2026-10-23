export type Severity = 'Critical' | 'High' | 'Medium' | 'Low' | 'Informational';
export type Confidence = 'Certain' | 'High' | 'Medium' | 'Low';
export type FindingStatus = 
  | 'Detected'
  | 'Needs Investigation'
  | 'Verification Pending'
  | 'Verified in Authorized Environment'
  | 'False Positive'
  | 'Fixed'
  | 'Retest Required';

export type JobStatus = 'queued' | 'running' | 'completed' | 'failed' | 'cancelled' | 'timeout';

export interface User {
  id: string;
  username: string;
  email: string;
  role: 'admin' | 'researcher' | 'viewer';
  is_active: boolean;
  must_change_password?: boolean;
  created_at: string;
  last_login?: string;
}

export interface SetupStatusResponse {
  setup_required: boolean;
  admin_count: number;
  message: string;
}

export interface InitialSetupRequest {
  username: string;
  email: string;
  password: string;
  confirm_password: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
  confirm_password: string;
}

export interface AuthorizedProgram {
  id: string;
  name: string;
  organization: string;
  policy_url?: string;
  contact_info?: string;
  notes?: string;
  is_active: boolean;
  created_at: string;
  scopes_count?: number;
}

export interface ScopeEntry {
  id: string;
  program_id: string;
  target_type: 'domain' | 'wildcard_domain' | 'url_prefix' | 'repository' | 'android_package' | 'cloud_config';
  target_value: string;
  permitted_methods: string;
  prohibited_methods: string;
  rate_limit_rps: number;
  authorization_reference: string;
  date_last_reviewed: string;
  status: 'active' | 'paused' | 'expired' | 'revoked';
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface ResearchJob {
  id: string;
  program_id: string;
  scope_id?: string;
  title: string;
  target: string;
  module_type: 'web' | 'api' | 'code' | 'mobile' | 'cloud' | 'ai_sec' | 'full_suite';
  status: JobStatus;
  priority: number;
  retry_count: number;
  max_retries: number;
  error_message?: string;
  cancellation_requested: boolean;
  is_scheduled: boolean;
  cron_expression?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
  findings_count?: number;
}

export interface JobAttempt {
  id: string;
  job_id: string;
  attempt_number: number;
  started_at: string;
  ended_at?: string;
  status: string;
  logs: string;
}

export interface Evidence {
  id: string;
  finding_id: string;
  evidence_type: string;
  content: string;
  headers_json?: string;
  request_url?: string;
  created_at: string;
}

export interface Finding {
  id: string;
  job_id?: string;
  program_id: string;
  scope_id?: string;
  title: string;
  category: string;
  severity: Severity;
  confidence: Confidence;
  status: FindingStatus;
  target: string;
  evidence_summary: string;
  reproduction_steps?: string;
  impact?: string;
  remediation?: string;
  tool_name?: string;
  rule_id?: string;
  false_positive_reason?: string;
  first_detected_at: string;
  last_observed_at: string;
  created_at: string;
  evidence_items?: Evidence[];
}

export interface DashboardStats {
  total_jobs: number;
  running_jobs: number;
  potential_vulnerabilities: number;
  verified_findings: number;
  false_positives: number;
  critical_and_high: number;
  worker_health: string;
  last_scheduled_run?: string;
  active_scopes_count: number;
  recent_activity: Array<{
    id: string;
    action: string;
    resource: string;
    details: string;
    timestamp: string;
  }>;
}

export interface SystemHealth {
  status: string;
  database: string;
  worker_status: string;
  last_heartbeat?: string;
  active_jobs: number;
  emergency_stop: boolean;
  version: string;
}

export interface NotificationLog {
  id: string;
  recipient: string;
  subject: string;
  event_type: string;
  status: 'sent' | 'failed' | 'suppressed';
  error_message?: string;
  sent_at: string;
}
