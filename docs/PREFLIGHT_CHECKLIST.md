# COGNARC — Pre-Flight Checklist
> **Everything on this list requires YOU. Claude cannot do any of this.**
> Complete every item, collect the values, then paste them as instructed.
> Estimated time: ~45–60 minutes for a complete first-time setup.

---

## Current State (auto-detected 2026-05-06)

| Tool | Status |
|---|---|
| Node.js v25.9.0 | ✅ Installed |
| Python 3.14.4 | ✅ Installed |
| pip 26.1 | ✅ Installed |
| Docker 29.4.2 | ✅ Installed |
| Docker Compose v5.1.3 | ✅ Installed |
| git 2.54.0 | ✅ Installed |
| pnpm | ❌ **NOT installed** |
| Railway CLI | ❌ **NOT installed** |
| Vercel CLI | ❌ **NOT installed** |
| `.env` files | ❌ **None created yet** |
| GitHub repo | ❓ Unknown |

---

## SECTION A — Install Missing CLI Tools (Terminal — ~5 min)

These run locally. You can do them right now in your terminal.

### A1. Install pnpm (required — Turborepo uses it)
```bash
npm install -g pnpm
pnpm --version   # should print 9.x or 10.x
```

### A2. Install Railway CLI
```bash
npm install -g @railway/cli
railway --version
```

### A3. Install Vercel CLI
```bash
npm install -g vercel
vercel --version
```

### A4. Initialize git repo (the monorepo has no `.git` yet)
```bash
cd /home/agentrogue/cognarc
git init
git add .
git commit -m "chore: initial cognarc monorepo scaffold"
```

### A5. Install Python virtualenv for the API
```bash
cd /home/agentrogue/cognarc/apps/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # (once Claude fills this in)
```

> ✅ Mark **A1–A5 done** before proceeding. Claude can handle everything else after this.

---

## SECTION B — Create External Service Accounts (Browser — ~30 min)

These require sign-up. All have **free tiers** that cover the full MVP.

---

### B1. Supabase (Auth + PostgreSQL leaderboard)
> **URL:** https://supabase.com → "Start your project" → sign up with GitHub

**Steps:**
1. Create a **new organization** (e.g., "cognarc-dev")
2. Create a **new project** named `cognarc`
3. Choose the **free tier**
4. Choose region closest to you (e.g., `ap-south-1` for India)
5. Set a strong **database password** — save it somewhere safe
6. Wait ~2 min for project to initialize
7. Go to **Settings → API**

**Collect these values:**

| Variable | Where to find it | Your value |
|---|---|---|
| `SUPABASE_URL` | Settings → API → "Project URL" | `https://xxxx.supabase.co` |
| `SUPABASE_ANON_KEY` | Settings → API → "anon public" | `eyJ...` |
| `SUPABASE_SERVICE_ROLE_KEY` | Settings → API → "service_role" (**secret!**) | `eyJ...` |
| `SUPABASE_JWT_SECRET` | Settings → API → "JWT Settings" → "JWT Secret" | `your-jwt-secret` |

8. Go to **Authentication → Settings → Auth Providers**
9. Enable **Email (Magic Link)** — toggle it on, save
 
---

### B2. MongoDB Atlas (primary database)
> **URL:** https://cloud.mongodb.com → sign up (free)

**Steps:**
1. Create a **free M0 cluster** (512MB, shared)
2. Choose provider: **AWS**, region: **ap-south-1** (or closest to you)
3. Name the cluster: `cognarc-cluster`
4. Go to **Database Access → Add New Database User**
   - Username: `cognarc-app`
   - Password: generate a strong one — **save it**
   - Role: `readWriteAnyDatabase`
5. Go to **Network Access → Add IP Address**
   - Click "Allow Access from Anywhere" for now (0.0.0.0/0)
   - *(You'll restrict to Railway IPs later)*
6. Go to **Database → Connect → Drivers**
   - Select: Python 3.12+
   - Copy the connection string

**Collect these values:**

| Variable | Value |
|---|---|
| `MONGODB_URL` | `mongodb+srv://cognarc-app:<password>@cognarc-cluster.xxxx.mongodb.net/?retryWrites=true&w=majority` |
| `MONGODB_DB_NAME` | `cognarc` |

> Replace `<password>` in the connection string with the password you set in step 4.

---

### B3. Groq API (AI quest generation)
> **URL:** https://console.groq.com → sign up (free)

**Steps:**
1. Sign up / log in
2. Go to **API Keys → Create API Key**
3. Name it: `cognarc-dev`
4. Copy the key immediately (shown only once)

**Collect:**

| Variable | Value |
|---|---|
| `GROQ_API_KEY` | `gsk_...` |

> **Free limits:** 14,400 requests/day, 30 req/min. More than enough for MVP.
> Optional: create a second key named `cognarc-backup` and note it as `GROQ_API_KEYS`.

---

### B4. Upstash Redis (streak counters + quest cache)
> **URL:** https://upstash.com → sign up with GitHub (free)

**Steps:**
1. Click **Create Database**
2. Name: `cognarc-redis`
3. Type: **Regional** (pick closest region)
4. Plan: **Free** (10,000 req/day)
5. After creation → go to database details → **REST API** tab

**Collect:**

| Variable | Value |
|---|---|
| `UPSTASH_REDIS_REST_URL` | `https://xxxx.upstash.io` |
| `UPSTASH_REDIS_REST_TOKEN` | `AXxx...` |

---

### B5. GitHub Repository (version control + CI/CD)
> **URL:** https://github.com → New repository

**Steps:**
1. Create repo named `cognarc` (or `cognarc-platform`)
2. Set to **Private**
3. **Do NOT** initialize with README (the local repo already has content)
4. Copy the remote URL: `https://github.com/YOUR_USERNAME/cognarc.git`

**Then in your terminal:**
```bash
cd /home/agentrogue/cognarc
git remote add origin https://github.com/YOUR_USERNAME/cognarc.git
git branch -M main
git push -u origin main
```

5. Go to **Settings → Secrets and variables → Actions → New repository secret**

Add these secrets (you'll fill them in as you collect values above):

| Secret Name | Value |
|---|---|
| `SUPABASE_URL` | from B1 |
| `SUPABASE_ANON_KEY` | from B1 |
| `SUPABASE_SERVICE_ROLE_KEY` | from B1 |
| `SUPABASE_JWT_SECRET` | from B1 |
| `MONGODB_URL` | from B2 |
| `MONGODB_DB_NAME` | `cognarc` |
| `GROQ_API_KEY` | from B3 |
| `UPSTASH_REDIS_REST_URL` | from B4 |
| `UPSTASH_REDIS_REST_TOKEN` | from B4 |
| `SENTRY_DSN` | from B6 (below) |
| `RAILWAY_TOKEN` | from B7 (below) |
| `RAILWAY_URL` | from B7 (below) |

---

### B6. Sentry (error tracking — optional for MVP but recommended)
> **URL:** https://sentry.io → sign up (free — 5,000 errors/month)

**Steps:**
1. Create organization: `cognarc`
2. Create **two projects**:
   - Project 1: Platform `Python` → name `cognarc-api`
   - Project 2: Platform `Next.js` → name `cognarc-web`
3. Copy the DSN from each project's **Settings → Client Keys**

**Collect:**

| Variable | Value |
|---|---|
| `SENTRY_DSN` (API) | `https://xxx@oxx.ingest.sentry.io/yyy` |
| `NEXT_PUBLIC_SENTRY_DSN` (Web) | `https://xxx@oxx.ingest.sentry.io/zzz` |

---

### B7. Railway (FastAPI hosting)
> **URL:** https://railway.app → sign up with GitHub (free — $5 credit/month)

**Steps:**
1. Sign up with your GitHub account
2. Click **New Project → Empty Project**
3. Name it `cognarc`
4. Go to **Account Settings → API Tokens → Create Token**
5. Name: `github-actions-deploy`

**Collect:**

| Variable | Value |
|---|---|
| `RAILWAY_TOKEN` | `xxxx...` |

> The `RAILWAY_URL` will be generated when you deploy. Add it to GitHub secrets after first deploy.

---

### B8. Vercel (Next.js hosting)
> **URL:** https://vercel.com → sign up with GitHub (free — Hobby tier)

**Steps:**
1. Sign up with GitHub
2. Click **Add New → Project**
3. Import your GitHub repo `cognarc`
4. Configure:
   - **Root Directory:** `apps/web`
   - **Framework Preset:** Next.js (auto-detected)
   - **Build Command:** `npm run build`
5. Add Environment Variables in Vercel dashboard (from values above):
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `NEXT_PUBLIC_API_URL` → will be your Railway URL

6. Go to **Account Settings → Tokens → Create Token**
   - Name: `github-actions`

**Collect:**

| Variable | Value |
|---|---|
| `VERCEL_TOKEN` | `xxxx...` |
| `VERCEL_ORG_ID` | Settings → General → "Your ID" |
| `VERCEL_PROJECT_ID` | Project Settings → General → "Project ID" |

> Add these 3 to GitHub Secrets too.

---

## SECTION C — Langfuse (AI observability — needed before Phase 3)
> **URL:** https://cloud.langfuse.com → sign up (free)

Can be deferred until Day 4 (Phase 3), but set up now while you're doing accounts.

**Steps:**
1. Create org: `cognarc`
2. Create project: `cognarc-quests`
3. Go to **Settings → API Keys**
4. Create a key pair

**Collect:**

| Variable | Value |
|---|---|
| `LANGFUSE_PUBLIC_KEY` | `pk-lf-...` |
| `LANGFUSE_SECRET_KEY` | `sk-lf-...` |
| `LANGFUSE_HOST` | `https://cloud.langfuse.com` |

---

## SECTION D — Create Your `.env` Files (Terminal — ~10 min)

Once you have all values above, run this in your terminal to create the env files:

```bash
cd /home/agentrogue/cognarc

# ── Root .env (shared values read by docker-compose)
cat > .env << 'EOF'
# ── Supabase ──────────────────────────────────────────────────
SUPABASE_URL=https://YOUR_PROJECT_ID.supabase.co
SUPABASE_ANON_KEY=eyJ...your-anon-key...
SUPABASE_SERVICE_ROLE_KEY=eyJ...your-service-role-key...
SUPABASE_JWT_SECRET=your-jwt-secret

# ── MongoDB Atlas ──────────────────────────────────────────────
MONGODB_URL=mongodb+srv://cognarc-app:YOUR_PASSWORD@cognarc-cluster.xxxx.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB_NAME=cognarc

# ── Groq AI ───────────────────────────────────────────────────
GROQ_API_KEY=gsk_your-groq-key
GROQ_API_KEYS=gsk_primary,gsk_backup   # optional rotation

# ── Upstash Redis ──────────────────────────────────────────────
UPSTASH_REDIS_REST_URL=https://your-db.upstash.io
UPSTASH_REDIS_REST_TOKEN=AXxx...

# ── Sentry (optional but recommended) ─────────────────────────
SENTRY_DSN=https://xxx@oxx.ingest.sentry.io/yyy

# ── Langfuse (needed for Phase 3+) ────────────────────────────
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com

# ── App ───────────────────────────────────────────────────────
ENVIRONMENT=development
EOF

# ── API-specific .env (same values, consumed by FastAPI directly)
cp .env apps/api/.env

# ── Web .env.local (Next.js public vars)
cat > apps/web/.env.local << 'EOF'
NEXT_PUBLIC_SUPABASE_URL=https://YOUR_PROJECT_ID.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...your-anon-key...
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SENTRY_DSN=https://xxx@oxx.ingest.sentry.io/zzz
EOF
```

> ⚠️ `.env` files are already in `.gitignore`. Never commit them.

---

## SECTION E — Final Verification Checklist

Run this after completing all sections above:

```bash
cd /home/agentrogue/cognarc

# 1. CLI tools
pnpm --version       # should print a version
railway --version    # should print a version
vercel --version     # should print a version
git remote -v        # should show your GitHub repo URL

# 2. Env files exist
ls -la .env apps/api/.env apps/web/.env.local
# All 3 should show file sizes > 0

# 3. Docker works
docker compose config   # should parse docker-compose.yml without errors

# 4. Tell Claude you're ready
echo "Pre-flight complete. Ready to build."
```

---

## SECTION F — What Claude Will Do Next (You Don't Touch This)

Once you confirm pre-flight is done, Claude will:

1. **Install pnpm dependencies** → `pnpm install` (Turborepo workspace)
2. **Fill all empty source files** → `apps/api/app/main.py`, `apps/api/app/config.py`, etc.
3. **Write all `requirements.txt`** entries based on what's actually needed
4. **Configure Supabase** → apply the SQL migrations for leaderboard/achievements tables
5. **Apply MongoDB indexes** → run the index creation script
6. **Start local dev environment** → `docker compose up -d`
7. **Verify GATE 1A** → `curl localhost:8000/health` → 200

---

## Summary Table

| # | What | Where | Time | Blocker? |
|---|---|---|---|---|
| A1 | Install pnpm | Terminal | 1 min | ✅ YES — needed immediately |
| A2 | Install Railway CLI | Terminal | 1 min | ✅ Needed for deploy (Day 10) |
| A3 | Install Vercel CLI | Terminal | 1 min | ✅ Needed for deploy (Day 10) |
| A4 | Init git + push to GitHub | Terminal | 5 min | ✅ YES — needed for CI/CD |
| B1 | Create Supabase project | Browser | 5 min | ✅ YES — blocks auth on Day 2 |
| B2 | Create MongoDB Atlas cluster | Browser | 5 min | ✅ YES — blocks data on Day 3 |
| B3 | Get Groq API key | Browser | 2 min | ✅ YES — blocks AI on Day 4 |
| B4 | Create Upstash Redis | Browser | 3 min | ✅ YES — blocks streaks on Day 9 |
| B5 | Create GitHub repo + secrets | Browser | 10 min | ✅ YES — blocks CI/CD |
| B6 | Create Sentry projects | Browser | 5 min | 🟡 Recommended but deferrable |
| B7 | Create Railway project + token | Browser | 5 min | ✅ Needed for Day 10 deploy |
| B8 | Connect Vercel project + token | Browser | 5 min | ✅ Needed for Day 10 deploy |
| C | Create Langfuse project | Browser | 3 min | 🟡 Needed before Phase 3 (Day 4) |
| D | Create `.env` files | Terminal | 10 min | ✅ YES — needed before `docker compose up` |

**Critical blockers (do these first):** A1 → B1 → B2 → B3 → B4 → D

*Once you have `.env` files with real values, tell Claude and the build begins.*
