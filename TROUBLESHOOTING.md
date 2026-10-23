# VulnAI X — Troubleshooting & Operational Runbook

This guide covers common diagnostic scenarios, security error messages, and operational recovery procedures for **VulnAI X**.

---

## 1. Scope Authorization & Fail-Closed Errors

### Symptom: `Scope Authorization Check Failed: Target is NOT in the authorized scope`
- **Cause**: VulnAI X enforces strict **fail-closed** authorization. If a target domain, URL, or repository is not registered in the Scope Registry for that specific program, all testing is blocked immediately.
- **Resolution**:
  1. Open the **Scope Registry** tab in the dashboard.
  2. Select the relevant program (e.g., Google VRP or Meta Bug Bounty).
  3. Ensure the exact target pattern (e.g., `*.google.com` or `https://auth.meta.com`) is present and its status is marked **Active**.
  4. Use the **Pre-Flight Scope Test** button to simulate scope matching before launching the job.

### Symptom: `Requested method is expressly PROHIBITED by scope authorization policy`
- **Cause**: The scope entry explicitly lists methods that are forbidden by the bug bounty policy (e.g. `dos`, `brute_force`, `credential_stuffing`, `data_exfiltration`).
- **Resolution**: Do not run prohibited checks against external assets. VulnAI X will refuse to queue the job.

---

## 2. SSRF Guard & Network Block Messages

### Symptom: `Target resolves to restricted IP: 127.0.0.1 / 169.254.169.254. Blocked to prevent SSRF.`
- **Cause**: VulnAI X resolves all hostnames via DNS and validates every IP address before issuing any HTTP request. Access to loopback (`127.0.0.0/8`), private networks (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), link-local (`169.254.0.0/16`), and cloud metadata (`169.254.169.254`, `metadata.google.internal`) is blocked by default.
- **Resolution**:
  - In production / live bug bounty research: This is expected protective behavior.
  - In local isolated test labs: You can temporarily enable `ALLOW_PRIVATE_LAB_TARGETS=true` in your `.env` file to test local mock endpoints.

---

## 3. Worker Status & Crash Recovery

### Symptom: Worker status displays "Offline" in topbar
- **Cause**: The background worker process is not running, or its heartbeat has not been updated within the last 30 seconds.
- **Resolution**:
  1. Start the worker manually in a terminal:
     ```powershell
     .\scripts\run-worker.ps1
     ```
  2. The worker will output:
     ```
     [*] VulnAI X Background Worker started.
     ```
  3. The topbar status dot will turn green ("Worker: Active").

### Symptom: Job was interrupted due to a crash or PC reboot
- **Recovery Behavior**:
  - Upon starting up, `AutonomousWorker.recover_unfinished_jobs()` automatically identifies all jobs that were stuck in `running` state.
  - The worker checks if the authorization scope is still active. If valid, it increments the retry count and re-queues the job with backoff.
  - If the scope expired during the outage, the job is marked `failed` to prevent unauthorized execution.

---

## 4. Emergency Stop Activation

### Symptom: `EMERGENCY STOP PROTOCOL ACTIVE` banner is displayed
- **Effect**: All active and queued jobs are cancelled. No new jobs can be created.
- **Resolution**:
  1. Review the audit logs on the dashboard to inspect the reason for the emergency stop.
  2. Once the target issue is resolved, click the **Reset Circuit** button on the banner or in **System Health**.

---

## 5. Email Notification Diagnostics

### Symptom: Email alert not received
- **Check 1**: Check the **Notification Audit History** table in the Email Alerts page.
- **Check 2**: If the status is **Suppressed**, duplicate alert suppression prevented spamming the same notification within a 30-minute window.
- **Check 3**: If SMTP credentials are not yet configured in `.env`, VulnAI X operates in **Simulation / Log Mode**, recording notifications to the database without throwing runtime errors.
- **Check 4**: For Gmail SMTP, ensure you are using an **App Password** with 2-Factor Authentication enabled, not your main account password.

---

## 6. Backup & Restore Procedures

### SQLite Local Mode:
- **Backup**:
  ```powershell
  Copy-Item .\vulnai_x.db .\vulnai_x_backup.db
  ```
- **Restore**:
  ```powershell
  Copy-Item .\vulnai_x_backup.db .\vulnai_x.db -Force
  ```

### Cloud PostgreSQL Mode (Neon / Supabase):
- Neon provides automated point-in-time recovery and branch backups from the web console.
- Manual dump via `pg_dump`:
  ```bash
  pg_dump "$DATABASE_URL" > vulnaix_backup.sql
  ```

---

## 7. Authentication & Setup Troubleshooting

### Symptom: `Password change required before accessing system resources` (HTTP 403)
- **Cause**: The account has a temporary or default credential flag (`must_change_password=True`). To prevent unauthorized platform usage, all operations except password rotation and identity checks are blocked.
- **Resolution**: Use the password change dialog or call `POST /api/auth/change-password` with your current password and a new password meeting enterprise complexity requirements (>= 12 characters, uppercase, lowercase, number, and symbol).

### Symptom: First-time setup wizard is displayed on startup
- **Cause**: No administrative account currently exists in the database.
- **Resolution**: Fill in the administrator username, email, and password to establish the platform's initial identity enclave. Once completed, the setup endpoint automatically locks.
