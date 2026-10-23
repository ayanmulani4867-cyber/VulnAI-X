import { 
  User, AuthorizedProgram, ScopeEntry, ResearchJob, 
  Finding, DashboardStats, SystemHealth, NotificationLog, JobAttempt,
  SetupStatusResponse, InitialSetupRequest, ChangePasswordRequest
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ApiService {
  private getToken(): string | null {
    return localStorage.getItem('vulnai_token');
  }

  public setToken(token: string) {
    localStorage.setItem('vulnai_token', token);
  }

  public removeToken() {
    localStorage.removeItem('vulnai_token');
    localStorage.removeItem('vulnai_user');
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const token = this.getToken();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      this.removeToken();
      // If unauthorized on protected route, trigger window event
      window.dispatchEvent(new Event('auth:unauthorized'));
    }

    if (!response.ok) {
      let errorMessage = `HTTP Error ${response.status}`;
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorMessage;
      } catch {
        // fallback
      }
      throw new Error(errorMessage);
    }

    return response.json();
  }

  // Auth & Setup
  async getSetupStatus(): Promise<SetupStatusResponse> {
    return this.request<SetupStatusResponse>('/api/auth/setup-status');
  }

  async initialSetup(data: InitialSetupRequest): Promise<{ message: string; access_token: string; user: User }> {
    const res = await this.request<{ message: string; access_token: string; user: User }>('/api/auth/setup', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    this.setToken(res.access_token);
    localStorage.setItem('vulnai_user', JSON.stringify(res.user));
    return res;
  }

  async login(username: string, password: string): Promise<{ access_token: string; user: User }> {
    const data = await this.request<{ access_token: string; user: User }>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
    this.setToken(data.access_token);
    localStorage.setItem('vulnai_user', JSON.stringify(data.user));
    return data;
  }

  async changePassword(data: ChangePasswordRequest): Promise<{ message: string; user: User }> {
    const res = await this.request<{ message: string; user: User }>('/api/auth/change-password', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    localStorage.setItem('vulnai_user', JSON.stringify(res.user));
    return res;
  }

  async getCurrentUser(): Promise<User> {
    return this.request<User>('/api/auth/me');
  }

  // Dashboard
  async getDashboardStats(): Promise<DashboardStats> {
    return this.request<DashboardStats>('/api/dashboard/stats');
  }

  // Programs & Scopes
  async getPrograms(): Promise<AuthorizedProgram[]> {
    return this.request<AuthorizedProgram[]>('/api/programs');
  }

  async createProgram(program: Partial<AuthorizedProgram>): Promise<AuthorizedProgram> {
    return this.request<AuthorizedProgram>('/api/programs', {
      method: 'POST',
      body: JSON.stringify(program),
    });
  }

  async getScopes(programId?: string, statusFilter?: string): Promise<ScopeEntry[]> {
    let url = '/api/scopes';
    const params = new URLSearchParams();
    if (programId) params.append('program_id', programId);
    if (statusFilter) params.append('status_filter', statusFilter);
    const queryString = params.toString();
    if (queryString) url += `?${queryString}`;
    return this.request<ScopeEntry[]>(url);
  }

  async createScope(scope: Partial<ScopeEntry>): Promise<ScopeEntry> {
    return this.request<ScopeEntry>('/api/scopes', {
      method: 'POST',
      body: JSON.stringify(scope),
    });
  }

  async updateScope(scopeId: string, update: Partial<ScopeEntry>): Promise<ScopeEntry> {
    return this.request<ScopeEntry>(`/api/scopes/${scopeId}`, {
      method: 'PUT',
      body: JSON.stringify(update),
    });
  }

  async deleteScope(scopeId: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/api/scopes/${scopeId}`, {
      method: 'DELETE',
    });
  }

  async prevalidateTarget(programId: string, target: string, method: string = 'passive'): Promise<{ authorized: boolean; message: string; scope_id?: string; authorization_reference?: string }> {
    const params = new URLSearchParams({
      program_id: programId,
      target,
      method,
    });
    return this.request(`/api/scopes/validate-target?${params.toString()}`);
  }

  // Jobs
  async getJobs(statusFilter?: string, programId?: string): Promise<ResearchJob[]> {
    let url = '/api/jobs';
    const params = new URLSearchParams();
    if (statusFilter) params.append('status_filter', statusFilter);
    if (programId) params.append('program_id', programId);
    const qs = params.toString();
    if (qs) url += `?${qs}`;
    return this.request<ResearchJob[]>(url);
  }

  async createJob(job: { program_id: string; target: string; module_type: string; title?: string; is_scheduled?: boolean; cron_expression?: string }): Promise<ResearchJob> {
    return this.request<ResearchJob>('/api/jobs', {
      method: 'POST',
      body: JSON.stringify(job),
    });
  }

  async getJob(jobId: string): Promise<ResearchJob> {
    return this.request<ResearchJob>(`/api/jobs/${jobId}`);
  }

  async cancelJob(jobId: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/api/jobs/${jobId}/cancel`, {
      method: 'POST',
    });
  }

  async runJobNow(jobId: string): Promise<{ success: boolean; job_id: string; findings_count?: number; error?: string }> {
    return this.request(`/api/jobs/${jobId}/run-now`, {
      method: 'POST',
    });
  }

  async getJobAttempts(jobId: string): Promise<JobAttempt[]> {
    return this.request<JobAttempt[]>(`/api/jobs/${jobId}/attempts`);
  }

  // Findings
  async getFindings(filters: { severity?: string; confidence?: string; status_filter?: string; program_id?: string; job_id?: string } = {}): Promise<Finding[]> {
    const params = new URLSearchParams();
    if (filters.severity) params.append('severity', filters.severity);
    if (filters.confidence) params.append('confidence', filters.confidence);
    if (filters.status_filter) params.append('status_filter', filters.status_filter);
    if (filters.program_id) params.append('program_id', filters.program_id);
    if (filters.job_id) params.append('job_id', filters.job_id);
    const qs = params.toString();
    return this.request<Finding[]>(`/api/findings${qs ? `?${qs}` : ''}`);
  }

  async getFinding(findingId: string): Promise<Finding> {
    return this.request<Finding>(`/api/findings/${findingId}`);
  }

  async updateFinding(findingId: string, update: { status?: string; false_positive_reason?: string; remediation?: string }): Promise<Finding> {
    return this.request<Finding>(`/api/findings/${findingId}`, {
      method: 'PATCH',
      body: JSON.stringify(update),
    });
  }

  // Reports
  getPdfReportUrl(jobId: string): string {
    return `${API_BASE_URL}/api/reports/job/${jobId}/pdf`;
  }

  async getJsonReport(jobId: string): Promise<any> {
    return this.request(`/api/reports/job/${jobId}/json`);
  }

  // Settings & System
  async getConfig(): Promise<any> {
    return this.request('/api/settings/config');
  }

  async updateSmtp(config: any): Promise<{ message: string }> {
    return this.request('/api/settings/smtp', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async testEmail(recipient: string): Promise<{ success: boolean; message: string }> {
    return this.request('/api/settings/test-email', {
      method: 'POST',
      body: JSON.stringify({ recipient }),
    });
  }

  async getNotifications(): Promise<NotificationLog[]> {
    return this.request<NotificationLog[]>('/api/settings/notifications');
  }

  async triggerEmergencyStop(reason: string): Promise<any> {
    return this.request('/api/settings/emergency-stop', {
      method: 'POST',
      body: JSON.stringify({ reason }),
    });
  }

  async resetEmergencyStop(): Promise<any> {
    return this.request('/api/settings/emergency-stop/reset', {
      method: 'POST',
    });
  }

  async getHealth(): Promise<SystemHealth> {
    return this.request<SystemHealth>('/api/health');
  }
}

export const api = new ApiService();
