# VulnAI X — Autonomous AI Security Research Platform

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.3+-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-6.0+-3178C6.svg)](https://www.typescriptlang.org/)
[![Vite](https://img.shields.io/badge/Vite-8.3+-646CFF.svg)](https://vitejs.dev/)
[![Tests](https://img.shields.io/badge/Tests-26%20Passed-success.svg)](https://pytest.org/)
[![License](https://img.shields.io/badge/Budget-%E2%82%B90%2Fmonth-brightgreen.svg)](#strict-budget--free-cloud-deployment)

**VulnAI X** is an enterprise-grade, safe, autonomous AI-assisted security research platform engineered for authorized bug bounty research (e.g., **Google Vulnerability Reward Program**, **Meta Bug Bounty Program**) and DevSecOps vulnerability management.

Built with a strict **fail-closed** authorization architecture, anti-DNS-rebinding SSRF defense guards, persistent multi-agent orchestration, and a modern cybersecurity React dashboard.

---

## 1. System Architecture

```
+-------------------------------------------------------------------+
|               REACT 19 + TYPESCRIPT + VITE DASHBOARD               |
|  - Real-time statistics from live DB (No hardcoded metrics)       |
|  - Initial Setup Wizard & Mandatory Password Rotation Screen       |
|  - Mandatory Scope Registry & Pre-Flight Target Scope Tester      |
|  - Persistent Research Jobs queue with Run Now & Cancel actions   |
|  - Findings & Evidence repository with Verification states        |
|  - ReportLab PDF and structured JSON exports                     |
|  - Multi-Agent Orchestration visualizer                           |
|  - SMTP Alert Configuration with duplicate suppression             |
|  - System Health telemetry & Instant Emergency Kill Switch        |
+---------------------------------+---------------------------------+
                                  | REST API + JWT Bearer Auth
                                  v
+-------------------------------------------------------------------+
|                     FASTAPI APPLICATION SERVER                    |
|  - Pydantic v2 validation & SQLAlchemy 2.0 ORM                   |
|  - Fail-Closed Scope Enforcement Guard                            |
|  - Anti-DNS-Rebinding Socket-Level SSRF Defense Engine            |
|  - Safe Subprocess Isolation (No shell interpolation)             |
|  - Audit Trail & Notification History logging                     |
+---------------------------------+---------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|               AUTONOMOUS BACKGROUND WORKER & SCHEDULER            |
|  - Heartbeat telemetry & Crash recovery for interrupted jobs      |
|  - Exponential backoff & Duplicate job prevention                 |
|  - Standalone worker process (Can run locally or in cloud)        |
+---------------------------------+---------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|                     MULTI-AGENT ORCHESTRATION                     |
|  1. Planning Agent     --> Scope policy verification & selection  |
|  2. Web Agent          --> Passive headers, TLS, cookies, paths   |
|  3. Code Agent         --> Bandit AST, Semgrep, OSV dependencies  |
|  4. Mobile Agent       --> APK & AndroidManifest static analysis  |
|  5. Cloud Agent        --> Terraform, Dockerfile, K8s IaC audit   |
|  6. AI Security Agent  --> Prompt injection & tool permission audit|
|  7. Correlation Agent  --> Cross-tool deduplication & merging     |
|  8. Verification Agent --> Repeatable proof validation            |
|  9. Reporting Agent    --> ReportLab PDF & JSON draft generation  |
+-------------------------------------------------------------------+
```

---

## 2. Hard Security Controls

- **Mandatory Scope Registry (Fail-Closed)**: No scan can execute against an asset unless it exactly matches an authorized domain, wildcard pattern, or repository configured in the scope registry.
- **Socket-Level Anti-Rebinding SSRF Protection**: In addition to URL scheme and IP range validation, HTTP connections are intercepted at TCP socket connect time (`AntiRebindingNetworkBackend`). This verifies and pins destination IPs directly before handshake, eliminating DNS-rebinding race condition bypasses.
- **Hop-by-Hop Redirect Scope Inspection**: Evaluates every redirect location against the active bug bounty scope boundary before the client follows it.
- **Secure Initial Setup & Password Rotation**: Default static credentials have been replaced with a first-run setup wizard. All administrative accounts require high-entropy passwords (minimum 12 characters, uppercase, lowercase, numbers, and symbols). Any pre-seeded account is flagged with `must_change_password=True`, blocking platform API access until updated.
- **Safe Subprocess Execution**: All external security tools (Bandit, Semgrep) are executed strictly via argument arrays (`["bandit", ...]`) with `shell=False`. Shell interpolation is prohibited.
- **Instant Emergency Stop**: A hardware-style kill switch that cancels all running and queued jobs and rejects new research tasks immediately.
- **No Automatic Bug Bounty Submissions**: All PDF and JSON reports are generated as drafts for human verification and submission.

---

## 3. Windows Quick Start (Developer Experience)

### Prerequisites
- Windows 10/11
- Python 3.11+
- Node.js 18+

### Step 1: Automated Windows Setup
Open PowerShell and run the setup script:
```powershell
.\scripts\setup-windows.ps1
```
This automatically configures the Python virtual environment (`.venv`), installs security packages, installs frontend dependencies, initializes the database, and seeds authorized programs (Google VRP & Meta Bug Bounty).

### Step 2: Start Application
Run the startup script:
```powershell
.\scripts\run-windows.ps1
```
- **Frontend Dashboard**: [http://localhost:5173](http://localhost:5173)
- **FastAPI Backend**: [http://localhost:8000](http://localhost:8000)
- **Interactive OpenAPI Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

### Initial Administrator Setup Flow:
- When you first visit the dashboard, VulnAI X automatically detects that no admin exists and opens the **First-Time Setup Screen**.
- Choose your administrator username, email, and a secure password satisfying enterprise complexity rules.
- Once created, the security enclave unlocks and directs you to the dashboard.

### Step 3: Run Standalone Background Worker
To run the background worker daemon independently:
```powershell
.\scripts\run-worker.ps1
```

---

## 4. Running Automated Tests

Run the complete test suite with `pytest`:
```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests -v
```
All 26 automated tests covering authentication, fail-closed scope enforcement, SSRF protections, worker crash recovery, finding deduplication, PDF generation, and duplicate email suppression execute in ~12 seconds.

---

## 5. Strict Budget & Free Cloud Deployment (₹0/Month)

For complete cloud deployment instructions and an honest evaluation of free-tier hosting limits, consult [CLOUD_DEPLOYMENT.md](file:///c:/VulnAI-X/CLOUD_DEPLOYMENT.md).

- **Frontend**: Deploy to Vercel or Cloudflare Pages for ₹0/month.
- **Backend**: Deploy to Render or Koyeb free tier.
- **Database**: Persistent Serverless PostgreSQL hosted on Neon.tech (₹0/month, SSL enabled, connection pooler supported).
- **Scheduled Autonomous Cloud Worker**: GitHub Actions cron workflow (`.github/workflows/scheduled_research.yml`). Executes scheduled research jobs autonomously in the cloud without keeping your local Windows PC switched on!

---

## 6. Directory Structure

```
VulnAI-X/
├── backend/
│   ├── app/
│   │   ├── api/            # REST API routers (auth, dashboard, scopes, jobs, findings, reports, settings, health)
│   │   ├── models/         # SQLAlchemy 2.0 database models
│   │   ├── schemas/        # Pydantic v2 schemas
│   │   ├── security/       # Scope guard, SSRF defense, JWT auth
│   │   ├── agents/         # Multi-agent orchestrator & logical agent roles
│   │   ├── tools/          # Security adapters (Semgrep, Bandit, OSV, Web passive, Android, Cloud IaC, AI sec)
│   │   ├── worker/         # Autonomous background worker, recovery, heartbeats
│   │   ├── reporting/      # ReportLab PDF & JSON generator
│   │   └── notifications/  # SMTP alert service with duplicate suppression
│   ├── tests/              # 23 automated pytest test cases
│   ├── requirements.txt    # Python dependencies
│   └── pytest.ini
├── frontend/
│   ├── src/
│   │   ├── components/     # Reusable cyber UI components (Sidebar, Header, Badges, Modals)
│   │   ├── pages/          # Full page modules (Dashboard, Scopes, Jobs, Findings, Reports, Agents, Email, Health, Login)
│   │   ├── services/       # Typed API client
│   │   ├── types/          # TypeScript interfaces
│   │   ├── index.css       # Cybersecurity theme design system
│   │   └── App.tsx         # Main app shell & router
│   ├── package.json
│   └── vite.config.ts
├── scripts/
│   ├── setup-windows.ps1   # One-click Windows setup script
│   ├── run-windows.ps1     # One-click Windows runner script
│   └── run-worker.ps1      # Standalone background worker runner
├── .github/workflows/
│   └── scheduled_research.yml # ₹0 autonomous cloud scheduled research worker
├── .env.example            # Environment variables template
├── .gitignore
├── CLOUD_DEPLOYMENT.md     # Honest ₹0 cloud analysis & step-by-step setup
├── TROUBLESHOOTING.md      # Operational troubleshooting runbook
└── README.md
```
