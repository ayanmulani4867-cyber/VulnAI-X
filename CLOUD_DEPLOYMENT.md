# VulnAI X — ₹0/Month Cloud Deployment Guide & Free-Tier Evaluation

This document provides a realistic, technically rigorous guide to deploying **VulnAI X** in the cloud at **₹0 per month**, without requiring your local Windows PC to remain switched on.

---

## 1. Cloud Provider Free-Tier Reality Analysis (₹0 Budget)

Many cloud platforms market "free tiers", but have critical technical limitations that prevent continuous background workers or risk surprise billing. Here is an honest breakdown of current free-tier options:

| Hosting Provider | Free Tier Limits | Always-On Background Workers? | Database Persistence | Recommendation & Risk Level |
| :--- | :--- | :--- | :--- | :--- |
| **Render** | 750 free instance hours/month. Web services sleep after 15 mins of inactivity. | ❌ No free background worker or cron services. | Free Postgres expires in 30 days. | **Suitable for API & Frontend only**. Will sleep if idle. |
| **Fly.io** | 3 shared-cpu-1x VMs (256MB RAM). | ⚠️ Requires credit card entry for verification. | Ephemeral unless volume attached. | **Medium Risk**: Payment card required; accidental charges possible if limits exceeded. |
| **Koyeb** | 1 free Eco instance (512MB RAM, always-on). | ⚠️ Only 1 service allowed on free plan. | Ephemeral filesystem. | **Good for combined API + worker container**, but tight memory limit (512MB). |
| **Vercel / Cloudflare Pages** | Unlimited static hosting & CDN. | ❌ Serverless functions timeout after 10-15 seconds. | None (stateless). | **Recommended for React Frontend** (100% free, fast, zero maintenance). |
| **Neon.tech / Supabase** | Free managed PostgreSQL (0.5GB - 1GB). | N/A (Database only). | ✅ Persistent cloud storage. | **Recommended for Database** (No expiration, always accessible). |
| **GitHub Actions (Cron Workflows)** | 2,000 free minutes/month for private repos; unlimited for public. | ✅ **Yes! Autonomous cron execution without keeping PC on.** | Syncs state to cloud PostgreSQL. | **WINNER FOR ₹0 AUTONOMOUS SCHEDULED RESEARCH.** |

---

## 2. Recommended ₹0 Cloud Architecture

To achieve true autonomous scheduling in the cloud without keeping your PC powered on and with **zero risk of unexpected charges**:

```
+-------------------------------------------------------------+
|             REACT FRONTEND (Vercel / Cloudflare Pages)      |
|             - Cost: ₹0 / month                              |
|             - Global CDN, auto-build on git push            |
+------------------------------+------------------------------+
                               | HTTPS API Calls
                               v
+-------------------------------------------------------------+
|             BACKEND API (Render / Koyeb / Docker)           |
|             - Cost: ₹0 / month                              |
|             - FastAPI + Pydantic validation                 |
|             - Health check & scope management               |
+------------------------------+------------------------------+
                               |
                               +------------------------------+
                               |                              |
                               v                              v
+------------------------------------+  +-------------------------------------+
| PERSISTENT DATABASE (Neon.tech)   |  | AUTONOMOUS WORKER (GitHub Actions)  |
| - Cost: ₹0 / month                 |  | - Cost: ₹0 / month (2,000 mins/mo)  |
| - Managed PostgreSQL 16            |  | - Runs on schedule (e.g. daily cron)|
| - SSL connection pooling           |  | - Windows PC does NOT need to be on |
| - Automated backups                |  | - Dispatches SMTP email alerts      |
+------------------------------------+  +-------------------------------------+
```

---

## 3. Step-by-Step Cloud Deployment Instructions

### Step 3.1: Persistent Database Setup (Neon.tech Serverless PostgreSQL - ₹0)
1. Sign up at [https://neon.tech](https://neon.tech) (no credit card required).
2. Create a free project named `vulnaix-db`.
3. In the Neon Console Dashboard:
   - Select the **Connection Details** widget.
   - Choose **Pooled connection** (uses the `-pooler` hostname for optimized connection pooling via PgBouncer).
   - Ensure **SSL Mode** is set to `require`.
   - Copy the connection URI:
     ```
     postgresql://[user]:[password]@[ep-id-pooler].[region].aws.neon.tech/neondb?sslmode=require&channel_binding=require
     ```
4. **Serverless Compute & Connection Pooling Architecture**:
   - Neon serverless compute automatically pauses when inactive to preserve resources, resuming within milliseconds on incoming queries.
   - VulnAI X's SQLAlchemy 2.x engine (`backend/app/database.py`) automatically enables:
     - `pool_pre_ping=True`: Verifies socket health before checkout, seamlessly recovering from serverless auto-suspension.
     - `pool_recycle=300`: Reconnects every 5 minutes to avoid stale sockets.
     - `pool_size=10` with `max_overflow=20`: Bounds connection concurrency to fit comfortably within Neon free tier limits.
5. **Where to store this secret**:
   - **Local Development**: In `C:\VulnAI-X\.env` (`DATABASE_URL=postgresql://...`). Note that `.env` is gitignored and never committed.
   - **Cloud Web Hosting (Render / Koyeb)**: In the provider's **Environment Variables** dashboard settings.
   - **Scheduled Cloud Worker (GitHub Actions)**: In repository **Settings -> Secrets and variables -> Actions** as `DATABASE_URL`.
6. **Automatic Schema Initialization & Non-Destructive Migrations**:
   - On application startup, VulnAI X executes `Base.metadata.create_all()` and safe column migrations (`IF NOT EXISTS`). Existing data and tables are never dropped.

### Step 3.2: React Frontend Deployment (Vercel - ₹0)
1. Push this repository to GitHub.
2. Sign in to [Vercel](https://vercel.com) using your GitHub account.
3. Import the repository and set:
   - **Root Directory**: `frontend`
   - **Framework Preset**: `Vite`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Environment Variable**: `VITE_API_URL` = Your backend URL (from Step 3.3).
4. Click **Deploy**. Your dashboard will be live at `https://vulnaix.vercel.app`.

### Step 3.3: Backend Deployment (Render - ₹0)
1. Sign up at [https://render.com](https://render.com).
2. Click **New +** -> **Web Service**.
3. Select your GitHub repository:
   - **Name**: `vulnaix-api`
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port 10000`
4. Set Environment Variables:
   - `APP_ENV`: `production`
   - `DATABASE_URL`: Your Neon PostgreSQL connection string.
   - `SECRET_KEY`: A random 64-character secret.
   - `CORS_ORIGINS`: `["https://vulnaix.vercel.app"]`
   - `SMTP_HOST`: `smtp.gmail.com`
   - `SMTP_PORT`: `587`
   - `SMTP_USER`: Your Gmail address.
   - `SMTP_PASSWORD`: Your Gmail App Password.
   - `NOTIFICATION_EMAIL_TO`: Your alert email.

*Note on Free Tier Sleep Behavior*: Render web services sleep after 15 minutes of inactivity. When you visit the dashboard, it takes ~45 seconds to wake up. This is standard behavior for ₹0 web hosting.

### Step 3.4: Autonomous Scheduled Research (GitHub Actions - ₹0)
To run scheduled research jobs without keeping your Windows PC on:
1. In your GitHub repository, go to **Settings** -> **Secrets and variables** -> **Actions**.
2. Add secrets:
   - `DATABASE_URL`: Your Neon connection string.
   - `SECRET_KEY`: Same JWT secret as backend.
   - `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`, `NOTIFICATION_EMAIL_TO`.
3. The workflow file `.github/workflows/scheduled_research.yml` is already included in this repository. It executes automatically on your configured schedule (e.g., daily at 02:00 UTC).

### Step 3.5: Containerized Deployment Option (Docker / Koyeb Eco - ₹0)
If deploying via container to Koyeb (Free Eco instance) or a self-hosted Docker server:
1. Build and run using the included `docker-compose.yml`:
   ```bash
   docker compose up -d
   ```
2. The compose stack initializes both the backend REST API (port 8000) and the background autonomous worker in separate isolated containers with persistent volume mounts.

---

## 4. Environment Variables Checklist

Ensure these variables are configured in your cloud environment:

- [ ] `DATABASE_URL` (PostgreSQL URI with SSL mode require)
- [ ] `SECRET_KEY` (Cryptographically random hex key)
- [ ] `APP_ENV` (`production`)
- [ ] `CORS_ORIGINS` (Exact URL of your deployed frontend)
- [ ] `SMTP_HOST` (e.g. `smtp.gmail.com` or SendGrid free)
- [ ] `SMTP_PORT` (`587`)
- [ ] `SMTP_USER` & `SMTP_PASSWORD`
- [ ] `NOTIFICATION_EMAIL_TO`

---

## 5. Health Check & Monitoring

Verify your cloud instance health:
- Health endpoint: `GET https://your-backend.onrender.com/api/health`
- Expected response:
  ```json
  {
    "status": "healthy",
    "database": "healthy",
    "worker_status": "healthy",
    "emergency_stop": false,
    "version": "1.0.0"
  }
  ```
