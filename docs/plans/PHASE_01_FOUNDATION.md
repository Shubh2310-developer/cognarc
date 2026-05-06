# PHASE 01 — FOUNDATION
> **COGNARC Engineering Governance | Phase 1 of 10**
> Agents: `gsd-planner` · `gsd-roadmapper` · `backend-architect` · `frontend-developer`
> Skills: `senior-architect` · `gepetto` · `subagent-driven-development`

---

## Phase Goal

Establish a fully operational monorepo with Next.js 14, FastAPI, Docker Compose, Supabase Auth, and MongoDB Atlas so that a new user can register, receive a JWT, and hit a protected health endpoint — all services green by Day 3.

---

## Architectural Rules Addressed

| Rule (CLAUDE.md) | Constraint |
|---|---|
| §03 MVP Architecture | ONE FastAPI app, ONE port (8000). No microservices. |
| §04 Monorepo Structure | Turborepo workspace; `apps/api/`, `apps/web/`, `packages/` scaffolded. |
| §13 Phase 1 Days 1–10 | MVP only. No Go gateway, no LangGraph, no agents. |
| §14 MVP Scope Rules | Phase 2 code on `feat/phase-2` branch only. Never on `main`. |
| §20 Security | Supabase Auth is the ONLY auth provider. JWT in `middleware/auth.py`. |
| §22 CI/CD | GitHub Actions: test → lint → build → deploy pipeline. |
| §27 Do-Not-Do List | No `exec()`/`eval()`, no secrets in source, no Go/Redis yet. |

---

## Task Breakdown (Checklist)

### Day 1 — Monorepo & Docker Scaffold

- [ ] **T1.1** Init Turborepo: `npx create-turbo@latest cognarc --package-manager pnpm`
- [ ] **T1.2** Configure `pnpm-workspace.yaml` for `apps/*` and `packages/*`
- [ ] **T1.3** Create `turbo.json` with pipelines: `build`, `dev`, `test`, `lint`
- [ ] **T1.4** Scaffold `apps/api/` FastAPI skeleton: `app/main.py`, `app/core/config.py`, `app/api/v1/health.py`
- [ ] **T1.5** Scaffold `apps/web/` Next.js 14: `npx create-next-app@14 apps/web --typescript --tailwind --app --src-dir`
- [ ] **T1.6** Create `packages/shared-types/` — empty TypeScript package, export `User`, `Quest`, `Progress` types
- [ ] **T1.7** Create `packages/design-tokens/` — CSS variables for §05 design system (purples, golds, dark surfaces)
- [ ] **T1.8** Create `packages/logger/` — structured JSON logger stub (Python + TS)
- [ ] **T1.9** Write root `Makefile`: `dev`, `test`, `lint`, `build`, `deploy` targets
- [ ] **T1.10** Write `docker-compose.yml`: services `api` (port 8000) and `web` (port 3000) on `cognarc-net`
- [ ] **T1.11** Write `docker-compose.dev.yml`: volume mounts for hot reload
- [ ] **T1.12** Write `infrastructure/docker/api/Dockerfile` (python:3.11-slim, uvicorn)
- [ ] **T1.13** Write `infrastructure/docker/web/Dockerfile` (multi-stage Next.js)
- [ ] **T1.14** Implement `GET /health`, `GET /health/ready`, `GET /health/live` in FastAPI
- [ ] **T1.15** **GATE:** `docker compose up -d` → `curl localhost:8000/health` → `{"status":"ok"}`

### Day 2 — Supabase Auth + JWT Middleware

- [ ] **T2.1** Create Supabase project; enable Magic Link auth provider
- [ ] **T2.2** Set env vars: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`
- [ ] **T2.3** Implement `apps/api/app/middleware/auth.py` — decode Supabase JWT via `python-jose`, inject `user_id`, return 401 on failure
- [ ] **T2.4** Implement `apps/api/app/core/dependencies.py` — `get_current_user()` and `require_admin()` FastAPI dependencies
- [ ] **T2.5** Implement `apps/api/app/adapters/supabase_adapter.py` — wraps Supabase client with retry/timeout
- [ ] **T2.6** Implement `apps/api/app/api/v1/auth.py`: `POST /auth/login`, `POST /auth/logout`, `POST /auth/refresh`
- [ ] **T2.7** Implement `packages/auth-client/` — Next.js Supabase client wrapper (magic link flow)
- [ ] **T2.8** Add `apps/web/src/middleware.ts` — Next.js route-level auth guard (redirect to login if no session)
- [ ] **T2.9** **GATE:** Register → JWT → `GET /users/me` with token → 200; without token → 401

### Day 3 — MongoDB Atlas Integration

- [ ] **T3.1** Create MongoDB Atlas M0 cluster; whitelist Railway CIDR + local IP
- [ ] **T3.2** Create DB user; copy `MONGODB_URL` and `MONGODB_DB_NAME` to env
- [ ] **T3.3** Implement `apps/api/app/db/mongodb.py` — Motor async client singleton with `connect_db()` / `close_db()` lifecycle hooks
- [ ] **T3.4** Implement `apps/api/app/models/user.py` — Pydantic model with all fields per §08 schema
- [ ] **T3.5** Implement `apps/api/app/repositories/mongo/user_repository.py`: `create_user()`, `get_user_by_auth_id()`, `update_user()`
- [ ] **T3.6** Implement `apps/api/app/services/user_service.py` — orchestrates user creation on first login
- [ ] **T3.7** Implement `apps/api/app/api/v1/users.py`: `GET /users/me`, `PATCH /users/me`, `GET /users/{id}/profile`
- [ ] **T3.8** Apply MongoDB indexes: `users.auth_id` (unique), `users.level` (regular)
- [ ] **T3.9** **GATE:** Login → `GET /users/me` → profile persists in Atlas → 200

### CI/CD Foundation

- [ ] **T4.1** Create `.github/workflows/ci.yml` — pytest + ruff + tsc + eslint on PR
- [ ] **T4.2** Create `.github/workflows/deploy.yml` — Railway + Vercel deploy on push to `main`
- [ ] **T4.3** Link Vercel project to GitHub repo (auto-deploy on PR for preview)
- [ ] **T4.4** Configure Railway service for `apps/api/` with Dockerfile path
- [ ] **T4.5** Add smoke test in deploy workflow: `curl $RAILWAY_API_URL/health` → fail deploy if not 200

---

## Data Flow & Dependencies

```
[Browser]
  │─ magic link email ─▶ [Supabase Auth]
  │◀────────── JWT ────────────────────
  │
  │─ GET /users/me (Bearer <jwt>) ─▶ [FastAPI :8000]
                                          │
                                   middleware/auth.py
                                   (python-jose decode)
                                          │
                                   Depends(get_current_user)
                                          │
                                   user_repository.py
                                          │
                                   [MongoDB Atlas]
                                          │
                                   UserResponse schema ─▶ [Browser]
                                          │
                                   [Zustand store + React Query]
```

**Dependency Order:**
1. `Supabase Auth` configured → before any protected route
2. `MongoDB Atlas` connected → before `user_repository` used
3. `packages/shared-types/` exports `User` → before frontend consumes it
4. `docker-compose.yml` passes locally → before Railway deployment

---

## Testing & Observability

### Required Test Coverage

| Test | Tool | File | Target |
|---|---|---|---|
| Health endpoint 200 | pytest | `tests/integration/test_health.py` | 100% |
| JWT middleware rejects invalid token | pytest | `tests/unit/test_auth_middleware.py` | 100% |
| JWT middleware passes valid token | pytest | `tests/unit/test_auth_middleware.py` | 100% |
| MongoDB user creation | pytest | `tests/integration/test_user_repo.py` | 90% |
| `GET /users/me` returns profile | pytest | `tests/integration/test_users.py` | 100% |
| Next.js middleware redirects unauth'd | Vitest | `web/tests/unit/middleware.test.ts` | 100% |

### Observability Requirements

- [ ] Sentry DSN configured in both `apps/api/` and `apps/web/`
- [ ] Structured HTTP request logging: method, path, status, latency, user_id
- [ ] `GET /health/ready` checks MongoDB connection status
- [ ] All unhandled exceptions sent to Sentry with `user_id` context

### SLO Targets (Phase 1)

| Metric | Target |
|---|---|
| `/health` uptime | 100% |
| Auth middleware latency | < 20ms p95 |
| MongoDB connection success on start | 100% |

---

## Validation Gate

**Phase 1 is DONE when ALL pass:**

```bash
# Local: services start
docker compose up -d
curl http://localhost:8000/health        # 200 {"status":"ok"}
curl http://localhost:8000/health/ready  # 200 {"database":"connected"}

# Auth: JWT guard enforced
curl -H "Authorization: Bearer <valid_jwt>" localhost:8000/users/me  # 200
curl localhost:8000/users/me                                          # 401

# Persistence: data survives restart
docker compose restart api
curl -H "Authorization: Bearer <valid_jwt>" localhost:8000/users/me  # same user data

# CI: PR opens → GitHub Actions passes (test ✅ lint ✅ build ✅)
# Production: push to main → Railway health check passes
```

---

## Absolute 'Do-Not-Do' List for Phase 1

| Forbidden | Reason |
|---|---|
| ❌ Go API Gateway | Phase 2+ only (§03, §15) |
| ❌ LangGraph / agents / LangChain | Phase 4 ONLY — the #1 project-killer |
| ❌ BGE-small embeddings | Phase 2+ feature |
| ❌ Phi-2 fallback | Phase 2+ feature |
| ❌ Boss battles / leaderboard / badges | Phase 3 |
| ❌ Framer Motion animations | Phase 3; use toast only |
| ❌ Split FastAPI into microservices | Monolith first per §15 |
| ❌ Commit `.env` files | Secrets rules §20, §27 |
| ❌ `exec()` / `eval()` anywhere | AI safety §16 |
| ❌ Import `ai-services/` in `apps/api/services/` | Architecture boundary §07 |
| ❌ Raw `fetch`/`axios` from React components | Use feature `api/` layer §05 |
| ❌ OAuth providers | Magic link only in MVP §14 |
| ❌ Redux / MobX | Zustand only §05, §27 |

---

*Phase 1 Target: Days 1–3 | MVP Gate: Day 10*
*Owner: `senior-architect` · `backend-developer` · `frontend-developer`*
*Next: [PHASE_02_DATA_MODELING.md](./PHASE_02_DATA_MODELING.md)*
