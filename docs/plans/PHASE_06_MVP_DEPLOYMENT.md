# PHASE 06 — MVP DEPLOYMENT
> **COGNARC Engineering Governance | Phase 6 of 10**
> Agents: `gsd-planner` · `gsd-roadmapper` · `gsd-verifier` · `performance-monitor`
> Skills: `senior-architect` · `gepetto` · `subagent-driven-development`

---

## Phase Goal

Successfully deploy the complete MVP to Railway (FastAPI) and Vercel (Next.js) on Day 10, pass all E2E validation gates on a public production URL, and confirm the full user journey — register → quests → complete → XP updates — completes in under 5 minutes for a new user.

---

## Architectural Rules Addressed

| Rule (CLAUDE.md) | Constraint |
|---|---|
| §03 MVP Architecture | ONE Railway service, ONE FastAPI process, ONE port (8000). |
| §13 Phase 1 Day 10 | E2E test + Railway + Vercel deploy is the Day 10 deliverable. |
| §13 Non-Negotiable MVP | No microservices on Railway. No Go gateway. Single deployment unit. |
| §22 CI/CD Rules | GitHub Actions: test → lint → build → deploy pipeline on push to `main`. |
| §22 Deployment Rules | NEVER deploy without staging validation. Smoke test after every deploy. |
| §28 Failure Recovery | Railway one-click rollback plan documented before go-live. |
| §29 Scaling Strategy | Free tier constraints managed: Railway $5 credit, Vercel Hobby, Atlas M0. |

---

## Task Breakdown (Checklist)

### Production Dockerfile (FastAPI MVP)

- [ ] **T1.1** Finalize `infrastructure/docker/api/Dockerfile.prod`:
  ```dockerfile
  FROM python:3.11-slim AS builder
  WORKDIR /app
  COPY apps/api/requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt

  FROM python:3.11-slim
  WORKDIR /app
  COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
  COPY apps/api/app ./app
  COPY ai-services ./ai-services
  ENV PYTHONPATH=/app
  CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", \
       "--workers", "2", "--log-level", "info"]
  ```

- [ ] **T1.2** Verify Docker image builds < 500MB (use `docker images` after build)
- [ ] **T1.3** Validate `docker run` locally with all required env vars → `/health` → 200

### Railway Deployment

- [ ] **T2.1** Create Railway project: service `cognarc-api`
- [ ] **T2.2** Connect Railway service to GitHub repo, set root directory to monorepo root
- [ ] **T2.3** Configure Railway build settings: `Dockerfile` path = `infrastructure/docker/api/Dockerfile.prod`
- [ ] **T2.4** Set all required environment variables in Railway service dashboard:
  - `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`
  - `MONGODB_URL`, `MONGODB_DB_NAME`
  - `GROQ_API_KEY`
  - `UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN`
  - `SENTRY_DSN`
  - `ENVIRONMENT=production`
- [ ] **T2.5** Configure Railway health check probe: `GET /health/ready` — fail after 30s
- [ ] **T2.6** Configure Railway auto-restart policy on crash (enabled)
- [ ] **T2.7** Set Railway resource limits: 0.5 vCPU, 512MB RAM (MVP monolith fits comfortably)
- [ ] **T2.8** Test deployment: `railway up --service cognarc-api`
- [ ] **T2.9** Validate: `curl https://<railway-url>/health` → `{"status": "ok"}`
- [ ] **T2.10** Validate: `curl https://<railway-url>/health/ready` → `{"database": "connected", "cache": "connected"}`

### Vercel Deployment (Next.js)

- [ ] **T3.1** Connect Vercel project to GitHub repo
- [ ] **T3.2** Configure Vercel project: root directory = `apps/web/`, framework = Next.js
- [ ] **T3.3** Set Vercel environment variables:
  - `NEXT_PUBLIC_API_URL=https://<railway-url>`
  - `NEXT_PUBLIC_SUPABASE_URL`
  - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
  - `SENTRY_DSN`
- [ ] **T3.4** Configure Vercel `vercel.json`:
  ```json
  {
    "buildCommand": "cd apps/web && npm run build",
    "outputDirectory": "apps/web/.next",
    "installCommand": "pnpm install"
  }
  ```
- [ ] **T3.5** Validate Vercel preview deploy on PR (automatic)
- [ ] **T3.6** Validate production deploy on push to `main`
- [ ] **T3.7** Check Vercel analytics: FCP < 1.5s, TTI < 3s

### GitHub Actions CI/CD Pipeline

- [ ] **T4.1** Finalize `.github/workflows/ci.yml`:
  ```yaml
  name: CI
  on: [push, pull_request]
  jobs:
    test-backend:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - uses: actions/setup-python@v5
          with: { python-version: '3.11' }
        - run: pip install -r apps/api/requirements.txt
        - run: cd apps/api && pytest tests/ -v --cov=app --cov-report=xml
        - run: cd apps/api && ruff check app/
        - run: cd apps/api && mypy app/

    test-frontend:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - uses: actions/setup-node@v4
          with: { node-version: '20' }
        - run: npm install -g pnpm && pnpm install
        - run: cd apps/web && npx tsc --noEmit
        - run: cd apps/web && npm run lint
        - run: cd apps/web && npm run test
  ```

- [ ] **T4.2** Finalize `.github/workflows/deploy.yml`:
  ```yaml
  name: Deploy
  on:
    push:
      branches: [main]
  jobs:
    deploy:
      needs: [test-backend, test-frontend]
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - name: Deploy to Railway
          run: |
            npm install -g @railway/cli
            railway up --service cognarc-api
          env:
            RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
        - name: Smoke test Railway
          run: |
            sleep 30
            curl -f https://$RAILWAY_URL/health || exit 1
          env:
            RAILWAY_URL: ${{ secrets.RAILWAY_URL }}
  ```

- [ ] **T4.3** Store all secrets in GitHub repository secrets (never in workflow YAML)

### End-to-End Test Suite (Day 10 Gate)

- [ ] **T5.1** Write `apps/web/tests/e2e/mvp_flow.spec.ts` (Playwright):
  ```typescript
  import { test, expect } from '@playwright/test'

  test('MVP full loop: register → quests → complete → XP updates', async ({ page }) => {
    // Step 1: Navigate to app
    await page.goto(process.env.APP_URL!)
    await expect(page).toHaveTitle(/COGNARC/)

    // Step 2: Login page visible
    await expect(page.locator('[data-testid="email-input"]')).toBeVisible()

    // Step 3: (Using test user with pre-seeded JWT)
    await page.evaluate((token) => {
      localStorage.setItem('supabase.auth.token', token)
    }, process.env.TEST_JWT!)
    await page.reload()

    // Step 4: Dashboard with 3 quests
    await expect(page.locator('[data-testid="quest-card"]')).toHaveCount(3)

    // Step 5: Mark first quest complete
    await page.locator('[data-testid="quest-card"]').first()
         .locator('[data-testid="mark-complete-btn"]').click()

    // Step 6: XP updates without reload
    await expect(page.locator('[data-testid="xp-value"]')).not.toHaveText('0 XP')
  })
  ```

- [ ] **T5.2** Configure Playwright: `playwright.config.ts` with `baseURL` from env
- [ ] **T5.3** Add E2E test to CI: run after successful deploy (staging URL)

### Monitoring & Alerts Setup

- [ ] **T6.1** Configure Sentry projects for `cognarc-api` (Python) and `cognarc-web` (Next.js)
- [ ] **T6.2** Create Sentry alerts:
  - Error rate > 5% for 5 minutes → email alert
  - P1 unhandled exception → immediate email
- [ ] **T6.3** Add Railway deployment webhook to Slack (optional but recommended)
- [ ] **T6.4** Document rollback procedure in `docs/deployment/ROLLBACK.md`:
  ```markdown
  # Railway Rollback
  1. Railway Dashboard → service → Deployments tab
  2. Click previous deployment → "Rollback" button
  3. Verify /health/ready returns 200 after rollback
  4. Post incident report
  ```

### MongoDB Atlas Production Hardening

- [ ] **T7.1** Enable MongoDB Atlas network access IP allowlist for Railway egress IPs
- [ ] **T7.2** Create read-only Atlas user for monitoring access
- [ ] **T7.3** Enable Atlas alerts: connection spike > 50, storage > 400MB
- [ ] **T7.4** Set Atlas backup: M0 does not support automated backups — document manual export schedule

### Free Tier Monitoring

- [ ] **T8.1** Create `scripts/monitor_free_tiers.sh`:
  ```bash
  #!/bin/bash
  echo "=== COGNARC Free Tier Status ==="
  echo "Railway: Check dashboard.railway.app for credit usage"
  echo "MongoDB Atlas: ${MONGODB_STORAGE_PCT}% of 512MB used"
  echo "Groq: $(curl -s https://api.groq.com/usage)  req/day used"
  echo "Redis: $(redis-cli info stats | grep total_commands_processed)"
  ```
- [ ] **T8.2** Document scaling trigger points per §29 in `docs/deployment/SCALING.md`

---

## Data Flow & Dependencies

```
GitHub push to main
  │
  ├── GitHub Actions CI
  │     ├── pytest apps/api/tests/      → PASS
  │     ├── ruff + mypy apps/api/       → PASS
  │     ├── tsc + eslint apps/web/      → PASS
  │     └── vitest apps/web/            → PASS
  │
  ├── GitHub Actions Deploy
  │     ├── railway up → [Railway: cognarc-api container]
  │     │     └── uvicorn :8000
  │     │           ├── → [MongoDB Atlas M0]
  │     │           ├── → [Supabase Auth]
  │     │           ├── → [Groq API]
  │     │           └── → [Upstash Redis]
  │     │
  │     └── vercel → [Vercel CDN: cognarc.vercel.app]
  │           └── Next.js App
  │                 ├── NEXT_PUBLIC_API_URL → Railway
  │                 └── NEXT_PUBLIC_SUPABASE_URL → Supabase
  │
  └── Smoke test: curl /health/ready → 200 (or rollback)
```

---

## Testing & Observability

### Day 10 Gate Tests (All Required)

| Test | Method | Expected |
|---|---|---|
| Railway /health | curl | 200 `{"status":"ok"}` |
| Railway /health/ready | curl | 200 `{"database":"connected","cache":"connected"}` |
| Auth: register new user | Browser manual | Magic link email received |
| Auth: login with magic link | Browser manual | JWT set, redirect to /dashboard |
| Quest generation | Browser | 3 quest cards visible < 1500ms |
| Quest completion | Browser | XP bar updates, toast shown |
| Streak increment | Browser | Streak count +1 in dashboard |
| E2E Playwright | Automated | All assertions pass |
| Vercel FCP | Lighthouse | < 1.5s |
| No console errors | Browser DevTools | 0 errors in network + console |

### SLO Verification (Day 10)

| Metric | Target | Measured via |
|---|---|---|
| Quest generation latency (cold) | < 1500ms p95 | Browser DevTools network tab |
| Dashboard load | < 800ms | Vercel Analytics |
| API uptime | 100% for 24h post-deploy | Railway metrics |

---

## Validation Gate

**Phase 6 (Day 10 MVP Gate) — DONE when ALL pass:**

```bash
# 1. Production health
curl https://<railway-url>/health        # 200
curl https://<railway-url>/health/ready  # 200 {"database":"connected"}

# 2. GitHub Actions CI green (check GitHub Actions tab)

# 3. Manual browser test on production URL:
# Open https://cognarc.vercel.app (or Railway preview URL)
# → Register with real email
# → Receive magic link, click it
# → See dashboard with 3 quests
# → Mark one quest complete
# → XP updates on page
# → Streak shows 1
# Total time for new user: < 5 minutes

# 4. E2E tests pass
cd apps/web && npx playwright test tests/e2e/mvp_flow.spec.ts --reporter=line
# All pass

# 5. No critical Sentry errors in first 1 hour
```

**The Day 10 gate is BINARY: either it passes completely or MVP has not shipped.**

---

## Absolute 'Do-Not-Do' List for Phase 6

| Forbidden | Reason |
|---|---|
| ❌ Deploy multiple Railway services | ONE service in MVP §03 |
| ❌ Deploy Go gateway | Phase 2+ (COGNARC Phase 7) |
| ❌ `git push --force` to `main` | CI/CD safety §22, §27 |
| ❌ Merge PR with failing tests | CI must be green §22 |
| ❌ Deploy without staging validation | §22 deployment rules |
| ❌ `docker compose down -v` in production | Data loss §27 |
| ❌ Commit env files to repo | §20 secrets rules |
| ❌ Scale horizontally before Day 10 gate | Resolve MVP first, scale after §29 |
| ❌ Enable Phase 2 features on main branch | `feat/phase-2` branch only §14 |
| ❌ Disable Railway health check probe | Required for auto-restart on crash |

---

*Phase 6 Target: Day 10 (final MVP gate)*
*Owner: `gsd-planner` (coordination) · `backend-developer` (Railway) · `frontend-developer` (Vercel)*
*Next: [PHASE_07_MICROSERVICES.md](./PHASE_07_MICROSERVICES.md)*
