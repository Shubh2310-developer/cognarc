# CLAUDE.md — COGNARC Engineering Governance Document

> **Cognitive Optimization & Gamified Neural Adaptive Reinforcement Console**
> Version: 2.0 — Execution Edition | Production-Grade | Multi-Year SaaS Codebase

---

## §00 — DEVELOPER SYSTEM SPECS

> **AGENT INSTRUCTIONS:** Always read this section to understand hardware constraints before
> recommending dependencies, Docker memory limits, or ML model sizes.

| Component | Spec |
|---|---|
| **OS** | EndeavourOS (Arch Linux) x86_64 — Kernel 6.18.26-2-lts |
| **CPU** | AMD Ryzen 7 7735HS (16 threads) @ 3.20 GHz |
| **RAM** | ~15 GB total (~5–6 GB typically free during dev) |
| **GPU** | NVIDIA GeForce RTX 4050 Mobile Max-Q (Discrete) |
| **VRAM** | **6 GB** (6141 MiB) — ~4.7 GB available after display/KDE |
| **CUDA Driver** | 595.71.05 → CUDA Runtime **13.2** |
| **GPU 2** | AMD Radeon 680M (Integrated — for display only) |
| **Python** | **3.12.0** (via Conda env named `cognarc`) |
| **Conda Env** | `cognarc` at `/home/agentrogue/miniconda3/envs/cognarc` |
| **Activate** | `source ~/miniconda3/etc/profile.d/conda.sh && conda activate cognarc` |
| **Node.js** | v25.9.0 (system) |
| **pnpm** | 10.33.4 |
| **Docker** | 29.4.2 + Compose v5.1.3 |
| **DE** | KDE Plasma 6.6.4 (Wayland) |

### Hardware Constraints for Claude

- **PyTorch:** Install with `--index-url https://download.pytorch.org/whl/cu124` (CUDA 12.4 build runs on 13.2 driver via backward compatibility)
- **Phi-2 / Local LLM:** Max safe GGUF size is **Q4_K_M (~1.7 GB)**. Do NOT suggest Q8 or FP16 models.
- **Batch sizes:** Keep GPU batch size ≤ 8 for inference tasks to avoid OOM with 4.7 GB free VRAM.
- **llama-cpp-python:** Must be installed with `CMAKE_ARGS="-DGGML_CUDA=on"` to use GPU acceleration.
- **FAISS:** Use `faiss-cpu` for development. GPU FAISS is unnecessary for BGE-small dedup.
- **Docker memory:** Keep container limits to ≤ 3 GB RAM each to avoid swap thrashing.

---

## §00.5 — PROVISIONED INFRASTRUCTURE

> **Status as of 2026-05-07 — Environment fully verified and developer-ready.**
> All keys confirmed working via `scripts/verify_keys.py`.

### External Services (All Provisioned)

| Service | Status | Key Detail |
|---|---|---|
| **Supabase** | ✅ Service Role verified | Project ID: `qnfcjqockibnnjwyxlfq` · Region: ap-south-1 |
| **MongoDB Atlas** | ✅ Ping OK | Cluster: `engunity.z6apovs.mongodb.net` · DB: `cognarc` |
| **Groq API** | ✅ Models endpoint 200 | Primary model: `llama3-70b-8192` · Planner: `mixtral-8x7b-32768` |
| **Upstash Redis** | ✅ PING OK | Instance: `driven-weasel-117499.upstash.io` |
| **Vercel** | ✅ Token authenticated | Org: `1Hl737jENxD32xXrSr6xfnIy` · Project: `prj_RIJUySky2N7Z4M3uHR0eWNFm2ZHb` |
| **Railway** | ✅ Project configured | Service: `cognarc-quests` · ID: `cmovixzzf04j6ad08a4mhgfwk` · Region: US |
| **Langfuse** | ✅ Health endpoint 200 | Host: `cloud.langfuse.com` · Project keys in env |
| **Sentry** | ✅ DSN set | Org: `cognarc` · Project: `javascript-nextjs` |

### Environment Files

| File | Purpose |
|---|---|
| `.env` | Root convenience file — loaded by direnv + local tools |
| `config/environments/.env.development` | Canonical dev environment — source of truth |
| `config/environments/.env.production` | Production (fill Railway/Vercel env vars instead) |

**Load for shell session:**
```bash
source config/environments/.env.development
# or — direnv handles it automatically via .envrc
```

**Verify all keys:**
```bash
python scripts/verify_keys.py
```

### Dependency Stack (All Installed in `cognarc` Conda Env)

| Phase | Key Packages | Status |
|---|---|---|
| MVP (1–6) | FastAPI 0.115, PyTorch 2.6.0+cu124, Motor 3.7, Sentence-Transformers | ✅ Installed |
| Phase 7 | Celery + Redis broker, Flower | ✅ Installed |
| Phase 8 | evaluate, rouge-score, nltk, scikit-learn, pywebpush 2.3.0 | ✅ Installed |
| Phase 9 | scipy, additional ML libs | ✅ Installed |
| Phase 10 | LangGraph ≥0.4, LangChain-Groq ≥0.3, ChromaDB, Mem0 | ✅ Installed |
| **llama-cpp-python** | Phi-2 GGUF local fallback (Phase 8) | ⏳ Requires `yay -S gcc13` first |

**Re-install command:**
```bash
make install-all
```

**llama-cpp-python (when gcc13 available):**
```bash
yay -S gcc13    # AUR — gcc13 is NOT in official Arch repos (pacman -S gcc13 will fail)
make install-all  # auto-detects g++-13 and compiles with CUDA
```

### VAPID Keys (Push Notifications — Phase 8)

Already generated and stored in env files. Public key available in `VAPID_PUBLIC_KEY` env var.
To regenerate: `npx web-push generate-vapid-keys` (use `npx`, not `npm install -g` — avoids permission errors).

### Known Issues & Gotchas

| Issue | Status | Fix |
|---|---|---|
| `groq==0.28.0` too old for langchain-groq 0.3.x | ✅ Fixed | Bumped to `groq>=0.30.0,<1.0.0` in `apps/api/requirements.txt` |
| MongoDB/Postgres URI with `@` in password | ✅ Fixed | Password `@` escaped to `%40` in both env files |
| `npm install -g web-push` permission error | ✅ Documented | Use `npx web-push generate-vapid-keys` instead |
| `llama-cpp-python` CUDA build fails | ⏳ Pending | Needs `gcc13` from AUR (`yay -S gcc13`) |
| Supabase Anon Key health check 401 | ⚠️ Investigate | Service role key works. Re-check anon key in Supabase dashboard → Settings → API |

---


## §01 — PROJECT OVERVIEW


COGNARC is an AI-powered gamified skill development SaaS platform. It replaces passive learning with an intelligent quest system that generates personalized daily missions, tracks XP and streaks, enforces skill-tree dependencies, and evolves into a multi-agent AI orchestration system.

**Canonical Repository:** `/home/agentrogue/cognarc` (Turborepo monorepo)
**Primary Language Stack:** TypeScript (frontend), Python (backend + AI), Go (gateway, Phase 2+)
**Deployment Targets:** Vercel (web), Railway (API), MongoDB Atlas, Supabase, Upstash Redis

---

## §02 — CORE PRODUCT VISION

| Pillar | Description |
|---|---|
| AI Quest Generation | Daily personalized micro-quests via Groq API + skill context |
| Skill Tree (DAG) | Dependency-enforced progression, topological ordering |
| Gamification Engine | XP, levels, streaks, boss battles, badges, streak shields |
| Adaptive Intelligence | Anti-boredom/frustration/plateau engine via behavioral signals |
| Offline-First | IndexedDB + Dexie.js + Phi-2 local fallback |
| Multi-Agent Future | LangGraph Planner→Generator→Evaluator→Adaptation (Phase 4) |

**UVP:** The only platform where the user never decides what to learn next. The system generates, evaluates, and adapts the entire learning journey.

---

## §03 — SYSTEM ARCHITECTURE

### Architecture Strategy: Phase-Gated

| Phase | Pattern | When |
|---|---|---|
| MVP (Days 1–10) | Single FastAPI monolith + Next.js frontend | Build this first |
| Phase 2 (Days 11–25) | Add Go API Gateway + BGE dedup + Phi-2 fallback | After MVP ships |
| Phase 3 (Days 26–45) | Boss battles, leaderboard, full gamification | After Phase 2 stable |
| Phase 4 (Days 46–70) | LangGraph multi-agent orchestration | ONLY after Phase 1–3 validated |

**CRITICAL RULE:** Never build Phase 2+ features before the MVP gate passes on Day 10.

### Target Architecture (Phase 3+)

```
CLIENT LAYER (Next.js 14 PWA + IndexedDB)
        │ HTTPS / WebSocket
API GATEWAY (Go/Gin · JWT · Rate Limit · CORS)
        │
┌───────┬──────────┬──────────┬────────────┐
Quest   Progress   User       Gamification
FastAPI FastAPI    Go/Fiber   FastAPI
└───────┴──────────┴──────────┴────────────┘
        │
AI ORCHESTRATION LAYER (ai-services/)
  Groq API · BGE-small · Phi-2 fallback · LangGraph
        │
PERSISTENCE LAYER
  MongoDB Atlas · Supabase · Upstash Redis
```

### MVP Architecture (Build First)

```
Next.js 14 (React + Zustand + Dexie.js)
        │ HTTPS
Single FastAPI app (port 8000)
  /auth/*  /quests/*  /progress/*  /gamification  /ai/*
        │
MongoDB Atlas    Groq API
```

---

## §04 — MONOREPO STRUCTURE RULES

```
cognarc/
├── apps/
│   ├── api/                  # FastAPI backend
│   │   └── app/
│   │       ├── api/v1/       # Route handlers ONLY — no business logic
│   │       ├── services/     # Business logic — no DB calls
│   │       ├── engines/      # Domain engines (quest, gamification, battle, skill)
│   │       ├── repositories/ # DB access ONLY — mongo/ and cache/
│   │       ├── adapters/     # External API clients (Groq, Supabase, etc.)
│   │       ├── workers/      # Celery/background tasks
│   │       ├── events/       # Internal event definitions
│   │       ├── middleware/   # Auth, rate limit, telemetry middleware
│   │       ├── websocket/    # WebSocket handlers
│   │       ├── telemetry/    # Observability instrumentation
│   │       ├── models/       # Pydantic/ODM models
│   │       ├── schemas/      # Request/response schemas
│   │       ├── core/         # Config, security, dependencies
│   │       ├── db/           # DB connection management
│   │       └── security/     # JWT, auth utilities
│   ├── web/                  # Next.js 14 frontend
│   │   └── src/
│   │       ├── features/     # Feature-first modules (see §05)
│   │       ├── shared/       # Shared components, hooks, stores, types, utils
│   │       ├── config/       # App-level config
│   │       ├── styles/       # Global styles + design tokens
│   │       └── assets/       # Static assets
│   ├── admin/                # Admin panel
│   ├── worker/               # Background worker process
│   └── docs-site/            # Documentation site
├── ai-services/              # ALL AI logic — isolated here
│   ├── agents/               # Agent definitions (quest, tutor, evaluation)
│   ├── orchestration/        # LangGraph router, retry, fallback
│   ├── embeddings/           # BGE-small embedding service
│   ├── evaluators/           # Hybrid evaluator (test cases + AI)
│   ├── memory/               # Agent memory layer
│   ├── prompts/              # All prompt templates
│   ├── parsers/              # LLM output parsers
│   ├── adapters/             # AI provider clients
│   ├── behavioral_engine/    # Adaptation signals + difficulty modifier
│   └── validation/           # AI output validators
├── packages/                 # Shared TS/JS packages
│   ├── shared-types/         # Canonical TypeScript type definitions
│   ├── shared-hooks/         # Shared React hooks
│   ├── ui/                   # Shared UI component library
│   ├── auth-client/          # Supabase auth client wrapper
│   ├── websocket-client/     # Shared WS client
│   ├── logger/               # Logging utilities
│   ├── design-tokens/        # Design system tokens
│   ├── feature-flags/        # Feature flag client
│   ├── shared-config/        # Shared config schemas
│   ├── analytics-sdk/        # Analytics event client
│   └── testing-utils/        # Shared test utilities
├── infrastructure/
│   ├── docker/               # Dockerfiles per service
│   ├── kubernetes/           # K8s manifests (Phase 3+)
│   ├── terraform/            # IaC (Phase 3+)
│   ├── github-actions/       # CI/CD workflows
│   ├── railway/              # Railway service configs
│   ├── vercel/               # Vercel project config
│   ├── nginx/                # Reverse proxy config
│   ├── monitoring/           # Grafana dashboards, Prometheus rules
│   ├── observability/        # Tracing, logging pipeline
│   ├── security/             # Security policies, secrets management
│   └── backups/              # Backup scripts and schedules
├── docs/                     # Engineering documentation
│   ├── architecture/         # ADRs and system diagrams
│   ├── api/                  # API reference
│   ├── decisions/            # Architecture Decision Records
│   ├── deployment/           # Deployment runbooks
│   ├── runbooks/             # Incident runbooks
│   ├── ai/                   # AI system documentation
│   ├── diagrams/             # System diagrams
│   ├── product/              # Product specifications
│   └── onboarding/           # Developer onboarding
├── tests/                    # Root-level integration + E2E tests
├── monitoring/               # Global monitoring configuration
├── data/                     # Seed data, fixtures
├── scripts/                  # Operational scripts
├── config/                   # Shared config files
├── .claude/                  # Agent instructions, skills, agents
│   ├── CLAUDE.md             # This file
│   ├── agents/               # Agent definitions
│   └── skills/               # Skill modules
├── .agents/                  # Agent runtime state
├── docker-compose.yml        # Base compose
├── docker-compose.dev.yml    # Development overrides
├── docker-compose.prod.yml   # Production overrides
├── docker-compose.staging.yml
├── turbo.json                # Turborepo pipeline
├── pnpm-workspace.yaml       # PNPM workspace
└── Makefile                  # Common dev commands
```

**Monorepo Rules:**
- ALL packages versioned together. No independent semantic versioning per package.
- Cross-package imports: always via `packages/*` workspace aliases, never relative `../../` across app boundaries.
- AI logic NEVER bleeds into `apps/api/` services. It belongs exclusively in `ai-services/`.
- Shared types live ONLY in `packages/shared-types/`. Never duplicate type definitions.


---

## §05 — FRONTEND ARCHITECTURE RULES

### Feature-First Structure (MANDATORY)

Every feature in `apps/web/src/features/` MUST follow this exact layout:

```
features/<feature-name>/
├── components/     # Feature-specific React components
├── hooks/          # Feature-specific custom hooks
├── stores/         # Zustand stores scoped to this feature
├── types/          # Feature-specific TypeScript types
├── api/            # API call functions for this feature
├── utils/          # Feature-specific utilities
└── tests/          # Co-located tests
```

**Active Features:**
- `auth/` — Supabase magic link, OAuth, JWT refresh
- `quests/` — Quest display, completion, evaluation submission
- `gamification/` — XP bar, level-up, streak display, badges
- `skill-tree/` — DAG visualization, node progression
- `battles/` — Boss battle UI, timer, multi-part submission
- `leaderboard/` — Top 100 XP ranking, peer comparison
- `analytics/` — Activity heatmap, progress charts
- `notifications/` — Push notification management
- `onboarding/` — 3-screen mandatory onboarding tour

### State Management Rules

| State Type | Tool | Location |
|---|---|---|
| Global user state (XP, level, streak) | Zustand | `shared/stores/` |
| Server-fetched data | React Query | Feature `hooks/` |
| Offline cache | Dexie.js (IndexedDB) | `shared/utils/db.ts` |
| Feature-local UI state | React `useState` | Component level only |
| Form state | React Hook Form | Component level only |

**Rules:**
- NEVER use Redux. Zustand is the only global state manager.
- NEVER make raw `fetch`/`axios` calls from components. All API calls go through feature `api/` layer.
- NEVER call AI endpoints directly from the frontend. Always via backend API.
- Server state (React Query) and client state (Zustand) must NEVER hold the same data.

### Next.js 14 Specific Rules

- Use App Router (`app/` directory) for all pages. No Pages Router.
- Server Components by default. Use `'use client'` only when required (interactivity, browser APIs).
- Dynamic imports (`next/dynamic`) for heavy components: Framer Motion animations, Recharts, DAG visualizer.
- `next/image` for ALL images. No raw `<img>` tags.
- API routes: only for BFF patterns (e.g., token exchange). Never proxy general business logic.
- `middleware.ts` handles auth guard. Never replicate auth checks in individual page components.

### Design System Rules — Tactical IDE / Industrial Blueprint

**PARADIGM:** COGNARC uses a strict **Tactical IDE / Industrial Blueprint** design language.
This is NOT a consumer app. It is a HUD/terminal/code-editor aesthetic.

#### Color System (ABSOLUTE ENFORCEMENT)

| CSS Var | Hex | Tailwind | Usage |
|---|---|---|---|
| `--color-obsidian` | `#0B0C10` | `bg-[#0B0C10]` | Main background — absolute dark void |
| `--color-gunmetal` | `#16181D` | `bg-[#16181D]` | Card/Bento surfaces |
| `--color-forge`    | `#FF6B00` | `text-[#FF6B00]` | Primary CTA, streaks, active nodes |
| `--color-volt`     | `#CCFF00` | `text-[#CCFF00]` | Success, quest complete, level-up |
| `--color-bright`   | `#F8FAFC` | `text-slate-50` | Headings, primary reading text |
| `--color-muted`    | `#8B949E` | `text-[#8B949E]` | Secondary/inactive text |
| `--color-tactical` | `#2D3748` | `border-[#2D3748]` | All borders — 1px sharp |

**BANNED COLORS** (never use in any component, ever):
- Purple / `purple-*` / `#7C3AED`, `#6D28D9`, `#8B5CF6`
- Violet / `violet-*`
- Indigo / `indigo-*`
- Magenta / any pink
- Blue (except `#2D3748` border context)

#### Typography System (Three-Tier Mandatory)

| Tier | Font | Use For |
|---|---|---|
| Headings | Space Grotesk | H1–H6, narrative titles, page names |
| Telemetry | JetBrains Mono | XP counts, level indicators, button labels, time, tags, badges |
| Body | Inter | Standard body copy, descriptions, error messages |

#### Component Rules (CRITICAL — No Exceptions)

- **`rounded-none` on everything.** `border-radius: 0px` globally via `tailwind.config.ts`. No exceptions including `rounded-full`.
- **Zero box-shadows.** No `shadow-*`, no `drop-shadow-*`, no CSS `box-shadow`. Depth = borders only.
- **No glassmorphism.** No `backdrop-blur`, no semi-transparent glowing overlays.
- **Dense Bento layout.** `grid` with 1px `bg-[#2D3748]` separators between cells. See `apps/web/app/dashboard/page.tsx`.
- **Borders create depth.** Active = `border-[#FF6B00] border-l-2`. Success = `border-[#CCFF00]`. Default = `border-[#2D3748]`.

#### Animation Rules (Framer Motion)

- **Spring physics only.** Standard: `type: 'spring', stiffness: 300, damping: 30`.
- **No floaty fades.** No `ease: 'easeOut'` on slow opacity transitions.
- **Acceptable:** hard snaps, mechanical slides, typewriter reveals, `whileTap: { scale: 0.97 }`.
- **`next/dynamic`** required for pages importing Framer Motion (performance budget).

#### File Locations

- Design tokens CSS vars → `apps/web/app/globals.css` (`:root` block)
- Tailwind config → `apps/web/tailwind.config.ts`
- Shared UI components → `apps/web/src/shared/components/ui/`
  - `TacticalButton.tsx` — forge / volt / ghost / danger variants
  - `TacticalCard.tsx` — bento surface with optional corner accent bracket
- Layout components → `apps/web/src/shared/components/layout/`
  - `Sidebar.tsx` — 56px icon nav, animated active indicator
  - `Navbar.tsx` — top bar with system clock, breadcrumb, telemetry strip

---

## §06 — BACKEND ARCHITECTURE RULES

### Layer Responsibilities (STRICT)

```
HTTP Request
    │
[Router Layer]  apps/api/app/api/v1/*.py
    │  — Route registration, request parsing, response serialization ONLY
    │  — No business logic, no DB calls, no AI calls
    │
[Service Layer] apps/api/app/services/*.py
    │  — Orchestrates business workflows
    │  — Calls engines and repositories
    │  — No direct DB access, no direct AI calls
    │
[Engine Layer]  apps/api/app/engines/*_engine/
    │  — Domain algorithms: XP calc, streak logic, DAG traversal, difficulty modifier
    │  — Pure functions where possible. No I/O.
    │
[Repository Layer] apps/api/app/repositories/
    │  — DB read/write ONLY. No business logic.
    │  — mongo/: MongoDB via Motor async driver
    │  — cache/: Upstash Redis via upstash-redis client
    │
[Adapter Layer] apps/api/app/adapters/
       — External service clients: Groq, Supabase, push notification providers
       — Wraps external APIs with retry, timeout, circuit breaker
```

### Active Route Handlers (apps/api/app/api/v1/)

| File | Routes Owned |
|---|---|
| `auth.py` | POST /auth/login, POST /auth/logout, POST /auth/refresh |
| `quests.py` | GET /quests/today, POST /quests/generate, POST /quests/{id}/evaluate, POST /quests/{id}/skip |
| `users.py` | GET /users/me, PATCH /users/me, GET /users/{id}/profile |
| `gamification.py` | GET /gamification/dashboard, GET /gamification/xp, POST /gamification/level-check |
| `skills.py` | GET /skills/tree, GET /skills/{node}, POST /skills/{node}/progress |
| `battles.py` | GET /battles/weekly, POST /battles/{id}/start, POST /battles/{id}/submit |
| `analytics.py` | GET /analytics/activity, GET /analytics/velocity |
| `notifications.py` | POST /notifications/subscribe, DELETE /notifications/subscribe |
| `admin.py` | Admin-only endpoints (role-gated) |
| `health.py` | GET /health, GET /health/ready, GET /health/live |

### Backend Coding Rules

- Routes accept Pydantic schemas, return Pydantic schemas. Always. No raw dicts.
- All route functions are `async def`. No synchronous blocking calls in route handlers.
- Use FastAPI `Depends()` for: auth, DB sessions, rate limiting, feature flags.
- Background tasks via FastAPI `BackgroundTasks` for non-critical post-response work.
- Use `motor` (async MongoDB driver). Never use `pymongo` synchronously.
- All external calls (Groq, Supabase) go through `adapters/` with timeout + retry.
- HTTP status codes: 200 OK, 201 Created, 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 422 Unprocessable Entity, 429 Too Many Requests, 500 Internal Server Error.

### Active Services

| Service | Responsibility |
|---|---|
| `quest_service.py` | Quest generation pipeline, context building, dedup check |
| `evaluation_service.py` | Hybrid evaluator: test cases + AI feedback |
| `gamification_service.py` | XP award, level check, streak update, multiplier |
| `auth_service.py` | JWT validation, user session management |
| `user_service.py` | Profile CRUD, skill tree state management |
| `skill_service.py` | DAG traversal, node unlock, mastery detection |
| `battle_service.py` | Boss battle lifecycle, timer, multi-part scoring |
| `analytics_service.py` | Behavioral signal aggregation, activity logging |

---

## §07 — AI SYSTEM ARCHITECTURE RULES

### Core Rule: AI Isolation

**ALL AI logic MUST live exclusively in `ai-services/`. NEVER import AI modules into `apps/api/`.**

The backend API communicates with `ai-services/` via:
- Direct Python module import (MVP/monolith phase)
- Internal HTTP/gRPC calls (microservices phase)

### AI Architecture by Phase

| Phase | What Exists | What is FORBIDDEN |
|---|---|---|
| MVP | Single Groq prompt call in `ai-services/adapters/` | Agents, LangGraph, Planner, BGE |
| Phase 2 | BGE-small dedup, Phi-2 fallback, hybrid evaluator | LangGraph, multi-agent state |
| Phase 3 | Evaluator with sandboxed code runner | Autonomous agents |
| Phase 4 | LangGraph multi-agent: Planner→Generator→Evaluator→Adaptation | Fine-tuning (future scope) |

### AI Service Structure

```
ai-services/
├── agents/
│   ├── base_agent.py          # Abstract base for all agents
│   ├── quest_agent/           # Quest generation agent (Phase 4)
│   ├── tutor_agent/           # AI tutor mode (future)
│   └── evaluation_agent/      # Hybrid evaluator agent
├── orchestration/
│   ├── router.py              # Routes requests to correct provider
│   ├── retry.py               # Retry + exponential backoff
│   └── fallback.py            # Groq → Phi-2 fallback logic
├── embeddings/                # BGE-small-en-v1.5 (384-dim)
├── evaluators/                # Sandboxed test runner + AI feedback
├── memory/                    # Agent memory (MongoDB-backed)
├── prompts/                   # ALL prompt templates (versioned)
├── parsers/                   # Pydantic output parsers for LLM responses
├── adapters/                  # Groq client, Phi-2 llama.cpp client
├── behavioral_engine/         # Anti-boredom signals, difficulty_modifier
└── validation/                # Schema validation for AI outputs
```

### MVP Quest Generation Pipeline

```python
# Inputs: user_level, skill_node_current, streak_count,
#         difficulty_modifier, recent_quest_types, completion_rate_7d
# Flow:
# 1. Build context payload from MongoDB + Redis (~50ms)
# 2. Call Groq API with system+user prompt (~700–900ms)
# 3. Parse + validate output via Pydantic parser
# 4. On parse failure: retry once → fallback to cached quests
# 5. Store quests in MongoDB + Redis (TTL 24h)
# Total target: < 1200ms cold, < 80ms cached
```

### Hybrid Code Evaluation (Phase 2+)

| Layer | Method | Weight |
|---|---|---|
| Primary | Sandboxed subprocess test cases | Pass/fail gate (must pass for full XP) |
| Secondary | Groq AI quality feedback | Advisory only — does not block XP |
| Fallback | Self-report (honor system) | Theory/research quests only |

**Sandboxing Rule:** ALWAYS use `subprocess.run()` with `timeout=10`. NEVER use `exec()` or `eval()` on user code.

### LangGraph Multi-Agent Architecture (Phase 4 ONLY)

| Agent | Model | Trigger | Output |
|---|---|---|---|
| Planner | Mixtral-8x7B | Sunday + post-boss | 7-day quest schedule in `users.agent_state` |
| TaskGenerator | Llama-3-70B | Daily 05:00 AM user-local | 3 quest objects in production schema |
| Evaluator | Mixtral-8x7B | On submission | score, passed, xp_award, feedback, hints |
| Adaptation | Pure Python (no LLM) | 10 min post-session | Updated `difficulty_modifier` + `behavioral_profile` |

**Phase Gate:** Do NOT implement LangGraph before Phase 1–3 are stable in production. This is the single most common reason AI projects never ship.

---

## §08 — DATABASE RULES

### Database Allocation

| Database | Role | Free Tier |
|---|---|---|
| MongoDB Atlas M0 | Primary document store: users, quests, progress_logs, streaks, skill states | 512MB |
| Supabase PostgreSQL | Auth (via Supabase Auth), leaderboard, achievements, boss battles, guild_members | 500MB DB |
| Upstash Redis | Quest cache (TTL 24h), streak counters, rate limiting | 10,000 req/day |

### MongoDB Collection Rules

- `users`: auth_id (FK to Supabase), level, total_xp, active_skill_tree, skill_state (DAG), behavioral_profile, settings
- `quests`: user_id, date, title, type, difficulty, xp_reward, skill_node, evaluation_criteria, embedding, status, generated_by
- `progress_logs`: user_id, quest_id, completed_at, xp_earned, time_taken_min, evaluation_score
- `streaks`: user_id, current_streak, longest_streak, last_completion_date, shield_count

**Index Requirements:**
- `users`: `auth_id` (unique), `level` (for leaderboard aggregation)
- `quests`: `{user_id, date}` (compound, for daily fetch), `status` (for pending queries)
- `quests.embedding`: TTL index 30 days
- `progress_logs`: `{user_id, completed_at}` (compound)

### Supabase Table Rules

- `auth.users` — managed by Supabase. NEVER modify this table directly.
- `public.leaderboard` — materialized view, refreshed every 15 minutes.
- `public.achievements` — immutable insert-only. Never UPDATE or DELETE achievement records.
- `public.boss_battles` — attempt log. `status` enum: `in_progress | passed | failed`.

### Data Access Rules

- NEVER perform DB queries in service layer. Only in `repositories/`.
- NEVER store Supabase auth secrets in MongoDB.
- All MongoDB queries use Motor async driver. No synchronous pymongo.
- Use TTL indexes for: quest embeddings (30d), progress logs archive (90d).
- Redis is cache-only. MongoDB is the source of truth. Never let Redis diverge from MongoDB state on critical fields (XP, streak).

---

## §09 — EVENT SYSTEM RULES

### Internal Event Architecture

```
Quest Completed → QuestCompletedEvent
    → XP Calculation (synchronous, in-request)
    → Streak Update (synchronous, in-request)
    → Achievement Check (background task)
    → Leaderboard Update (background task)
    → Behavioral Signal Record (background task)
    → Push Notification Check (background task)
```

### Event Definitions (apps/api/app/events/)

| Event | Trigger | Consumers |
|---|---|---|
| `QuestGeneratedEvent` | POST /quests/generate success | Analytics service |
| `QuestCompletedEvent` | POST /quests/{id}/evaluate pass | Gamification, Achievement, Streak, Leaderboard, Analytics |
| `QuestSkippedEvent` | POST /quests/{id}/skip | Behavioral engine, Analytics |
| `LevelUpEvent` | XP crosses level threshold | Notification service, Achievement service |
| `StreakBrokenEvent` | Calendar day missed | Notification, Comeback mode activation |
| `BossBattleCompletedEvent` | Battle submission graded | Achievement, Leaderboard |
| `BehaviorSignalEvent` | After session end (10 min delay) | Adaptation agent (Phase 4) |

### Async Workflow Rules

- Synchronous in-request: XP calculation, streak increment, quest storage
- Background tasks: achievement checks, leaderboard updates, push notifications, behavioral analysis
- Queue-based (Phase 3+): email notifications, weekly boss battle generation, Planner agent runs
- NEVER block HTTP response waiting for AI calls beyond quest generation endpoint


---

## §10 — AGENT HIERARCHY

### How Agents Operate in this Repository

Agents read this file first. Then they execute their assigned role within the scope defined below. Agents MUST NOT exceed their domain. Cross-domain actions require explicit coordination through the `gsd-planner` agent.

### Primary Agents

| Agent | Domain | Activation Trigger |
|---|---|---|
| `senior-architect` | System design, ADRs, tech decisions, architecture reviews | New system design, phase transitions, tech debt assessment |
| `backend-architect` | FastAPI structure, layer design, API contract definition | Backend feature design, service boundary decisions |
| `ai-engineer` | ai-services/ architecture, prompt engineering, agent design | Any AI feature, prompt changes, evaluation changes |
| `frontend-developer` | Next.js features, component architecture, state management | Any frontend change |
| `backend-developer` | Implementation of FastAPI routes, services, engines, repos | Backend implementation tasks |
| `database-architect` | Schema design, index strategy, query optimization | Schema changes, new collections, migration planning |
| `code-reviewer` | PR review, pattern enforcement, quality gates | Before any merge to main |
| `gsd-planner` | Sprint planning, task breakdown, dependency ordering | Start of any multi-day task |
| `gsd-executor` | Step-by-step task execution | After gsd-planner produces a plan |
| `gsd-verifier` | Post-execution validation against plan | After gsd-executor completes |
| `playwright-tester` | E2E test authoring and execution | After any UI feature |
| `performance-monitor` | Load testing, bottleneck detection, optimization | Pre-production, after Phase transitions |

### Secondary Agents

| Agent | Domain |
|---|---|
| `nextjs-developer` | Next.js 14 specific patterns, App Router, Server Components |
| `typescript-pro` | TypeScript strictness, type safety, generics |
| `database-optimization` | Query profiling, index tuning, aggregation pipeline optimization |
| `gsd-codebase-mapper` | Full codebase discovery before multi-file operations |
| `gsd-debugger` | Root cause analysis for failing systems |
| `gsd-plan-checker` | Validates that a plan is safe and complete before execution |
| `gsd-roadmapper` | Phase roadmap updates, milestone tracking |
| `gsd-integration-checker` | Validates cross-service integration contracts |

### Agent Execution Protocol

```
1. READ this CLAUDE.md completely before any action
2. DISCOVER: read all files you will touch (never blind-edit)
3. PLAN: state changes + affected files before editing
4. EDIT: minimal diff only — no scope creep
5. VALIDATE: run required checks (see §18)
6. REPORT: what changed, what was tested, residual risk
```

---

## §11 — ACTIVE AGENTS

All agent definitions live in `.claude/agents/`. Current inventory:

**Production Agents:** ProjectRecovery, agent-organizer, ai-engineer, backend-architect, backend-developer, code-reviewer, database-architect, database-optimization, frontend-developer, gsd-codebase-mapper, gsd-debugger, gsd-executor, gsd-integration-checker, gsd-phase-researcher, gsd-plan-checker, gsd-planner, gsd-project-researcher, gsd-research-synthesizer, gsd-roadmapper, gsd-verifier, nextjs-developer, performance-monitor, playwright-tester, typescript-pro

**Agent Invocation Rule:** Always specify agent role explicitly. Never allow agents to self-expand their scope mid-task.

---

## §12 — ACTIVE SKILLS

All skill modules live in `.claude/skills/`. Current inventory:

**AI/ML Skills:** agents-langchain, agents-llamaindex, agents-autogpt, ai-agents-architect, autonomous-agents, agent-evaluation, langgraph, rag-engineer, rag-faiss, rag-implementation, rag-sentence-transformers, observability-langsmith, langfuse, prompt-caching, prompt-engineer, senior-prompt-engineer, optimization-gguf, inference-serving-vllm

**Engineering Skills:** senior-architect, senior-fullstack, senior-backend, backend-dev-guidelines, cc-skill-backend-patterns, subagent-driven-development, refactor-safely, review-changes, qa-test-planner, explore-codebase, documentation-templates

**Frontend Skills:** frontend-design, tailwind-patterns, ui-design-system, ui-ux-pro-max, ux-researcher-designer, backend-to-frontend-handoff-docs

**Infrastructure Skills:** infrastructure-modal, google-analytics, agent-memory-mcp, agent-manager-skill, context7-auto-research, e2e-page-validator

**Research Skills:** brainstorming, research-engineer, ml-paper-writing, perplexity, multimodal-llava, multimodal-segment-anything, voice-ai-development, gepetto, loki-mode

---

## §13 — DEVELOPMENT PHASES

### Phase 1 — MVP Foundation (Days 1–10)

**Goal:** Working system: register → receive AI quests → mark complete → XP updates.

| Day | Task | Status | Gate |
|---|---|---|---|
| 1 | Scaffold: Next.js + FastAPI + Docker Compose | ✅ Done | GET /health → 200 all services |
| 2 | Supabase Auth + JWT middleware | ✅ Done | Register → valid JWT → 401 without token |
| 3 | MongoDB Atlas: users, quests, progress collections | ✅ Done | Profile page loads from MongoDB |
| 4 | Groq API integration + AI Adapter + prompt template | ✅ Done | /ai/generate → 3 valid quest objects |
| 5 | Quest Service: /quests/generate end-to-end | ✅ Done | Real user context → quests stored in MongoDB |
| 6 | Progress Service: completion + XP calculation | ✅ Done | Quest marked done → XP stored |
| 7 | Next.js dashboard: Tactical IDE UI system | ✅ Done | Dashboard renders quests + XP bar + streak |
| 8 | XP + Level formulas in Gamification Engine | ✅ Done | Level derived from XP, bar shows correct % |
| 9 | Streak Engine: Redis streak counters | ✅ Done | Streak increments daily, resets on miss |
| 10 | E2E test + Railway + Vercel deploy | ⏳ Pending | Full loop on public URL in < 5 minutes |

**Day 7 Deliverables (Tactical IDE UI System):**
- `apps/web/tailwind.config.ts` — Full Tactical IDE token system (zero radius, zero shadows)
- `apps/web/app/globals.css` — CSS custom properties, bento utilities, grid background
- `apps/web/app/layout.tsx` — Root layout with Space Grotesk + Inter + JetBrains Mono
- `apps/web/app/dashboard/page.tsx` — Full Bento dashboard: XP bar, quest list, stats, skill node
- `apps/web/app/login/page.tsx` — Terminal-style magic link auth page
- `apps/web/src/shared/components/ui/TacticalButton.tsx` — forge/volt/ghost/danger variants
- `apps/web/src/shared/components/ui/TacticalCard.tsx` — Bento card with corner bracket accent
- `apps/web/src/shared/components/layout/Sidebar.tsx` — 56px icon nav with animated indicator
- `apps/web/src/shared/components/layout/Navbar.tsx` — Top bar with live clock + telemetry strip
- `apps/web/src/features/gamification/components/XPBar.tsx` — Spring-animated XP progress
- `apps/web/src/features/quests/components/QuestCard.tsx` — Industrial quest card with expand/skip/complete

**Non-Negotiable MVP Rules:**
- ONE FastAPI app, ONE Railway service, ONE port (8000)
- NO microservices, NO Go gateway, NO LangGraph, NO agents
- NO boss battles, NO leaderboard, NO badges, NO Framer Motion
- AI Adapter = single synchronous Groq call, one prompt template

### Phase 2 — Core Engine (Days 11–25)

Add: Go API Gateway · BGE-small dedup · Hybrid evaluator (test cases) · Phi-2 fallback · PWA offline (Dexie.js + service worker) · Background sync · Push notifications (streak warnings)

### Phase 3 — Full Gamification (Days 26–45)

Add: Boss Battle system · Achievement badges (30+) · Supabase leaderboard (materialized view) · Framer Motion UI polish · Streak shields · 90-day activity heatmap · Recharts DAG visualization · Level-up ceremony animation

### Phase 4 — Agentic AI (Days 46–70)

Add: LangGraph multi-agent graph (Planner→TaskGenerator→Evaluator→Adaptation) · Personalization Engine · A/B testing (single pipeline vs multi-agent quality) · Full documentation + demo

---

## §14 — MVP SCOPE RULES

**Phase Freeze Protocol:** Phase 2 code goes in a separate git branch (`feat/phase-2`). It MUST NOT merge into `main` until Day 10 MVP gate passes completely.

**MVP Intentional Simplifications:**

| Feature | MVP Implementation | What is Deferred |
|---|---|---|
| AI Quest Gen | One sync Groq call, one prompt template | Agents, LangGraph, BGE, Phi-2 |
| Code Eval | Self-report (honor system) | Sandboxed test runner |
| Skill Tree | Text list of nodes, current node shown | Interactive DAG visualization |
| Offline | IndexedDB quest cache via Dexie.js | Phi-2 fallback, background sync |
| Auth | Supabase magic link only | OAuth providers |
| Gamification | XP + level counter | Badges, boss battles, leaderboard, animations |
| Animations | Simple toast notifications | Framer Motion ceremonies |

---

## §15 — MICROSERVICE MIGRATION RULES

**Trigger Conditions for Microservice Split (Phase 2+):**
- MVP has been in production for at least 14 days without critical failures
- A specific service (Quest, Gamification, User) shows > 80% of CPU or memory usage
- A team of > 1 developer needs independent deployment of a service

**Migration Order:**
1. Extract Go API Gateway first (routing + auth only, no business logic)
2. Extract Quest Service (highest AI load)
3. Extract User Service (Go/Fiber for performance)
4. Extract Gamification Engine
5. ai-services/ becomes standalone AI microservice (last, most complex)

**Migration Rules:**
- Each service gets its own Dockerfile, Railway service, and environment config
- Shared database access becomes service-owned DB collections
- Services communicate only via HTTP/gRPC — never shared database access across service boundaries
- Deploy one new microservice at a time, validate fully before extracting the next

---

## §16 — AI SAFETY RULES

1. **Never execute user-provided code with `exec()` or `eval()`.** Always use `subprocess.run()` with `timeout=10`.
2. **Never trust AI output as ground truth.** All AI quest outputs pass through Pydantic validators before storage.
3. **Prompt injection is a real attack vector.** Sanitize all user-controlled strings before injection into prompts.
4. **AI failure is not a fatal error.** Every AI call has a defined fallback: cached quests, Phi-2, or self-report.
5. **Never let AI award XP directly.** AI output is advisory. XP calculation happens in the deterministic Gamification Engine.
6. **Log all AI inputs and outputs.** Every Groq API call is logged (truncated at 500 chars) to Sentry + Langfuse.
7. **Version all prompt templates.** Prompts are stored in `ai-services/prompts/` with version suffixes. Never edit a deployed prompt in-place — create a new version.
8. **Groq API keys rotate.** Support multiple keys in `GROQ_API_KEYS` env var for round-robin rotation.
9. **Sandboxed code execution:** subprocess with no network, no filesystem write, 10s timeout, 64MB memory limit.
10. **AI evaluation is advisory.** Pass/fail decision on quest completion comes from test cases. AI gives feedback only.

---

## §17 — CODE QUALITY RULES

### Naming Conventions

| Context | Convention | Example |
|---|---|---|
| Python files/vars | `snake_case` | `quest_service.py`, `user_id` |
| Python classes | `PascalCase` | `QuestGenerationService` |
| Python constants | `UPPER_SNAKE_CASE` | `MAX_QUEST_PER_DAY` |
| TypeScript files (components) | `PascalCase` | `QuestCard.tsx` |
| TypeScript files (utils/hooks) | `camelCase` | `useQuestStore.ts` |
| React components | `PascalCase` | `StreakDisplay` |
| API routes | `kebab-case` | `/api/v1/quest-generate` |
| Env vars | `UPPER_SNAKE_CASE` | `GROQ_API_KEY` |
| Zustand stores | `use<Name>Store` | `useGamificationStore` |
| React Query keys | `['resource', id]` tuple | `['quests', userId, date]` |

### Absolute Code Rules

- **No business logic in route handlers.** Routes parse requests and call services.
- **No DB logic in service layer.** Services call repositories.
- **No AI calls from services.** Services call the AI adapter interface only.
- **No circular imports.** Direction is always: router → service → engine/repository → adapter.
- **No giant files.** Max 300 lines per file. Split at 200 lines as a warning.
- **No uncontrolled global state.** All Zustand stores are explicitly defined and typed.
- **No duplicated type definitions.** All types in `packages/shared-types/`.
- **No `any` in TypeScript.** ESLint rule enforced. Use `unknown` with type guards instead.
- **No commented-out code committed.** Remove dead code. Git history preserves it.
- **No `console.log` or `print()` in committed code.** Use the structured logger.
- **No secrets in source code.** All secrets via environment variables.

### File Organization Rules

- One class per file in Python. One component per file in TypeScript.
- Feature code never imports from another feature directly. Use `packages/shared-*` for cross-feature sharing.
- `ai-services/` modules are NEVER imported directly by `apps/api/` services without going through the adapter interface.


---

## §18 — TESTING REQUIREMENTS

### Testing Pyramid

| Tier | Type | Tools | Coverage Target |
|---|---|---|---|
| Unit | Business logic, engines, parsers | pytest (Python), Vitest (TS) | 80% for engines + services |
| Integration | API routes + DB | pytest + TestClient + Motor test DB | All critical paths |
| E2E | Full user flows in browser | Playwright | Core journeys: auth, quest, XP |
| AI Eval | Prompt output quality | Custom LLM evaluator + Langsmith | All prompt templates |
| Load | Performance under traffic | Locust | Quest generation endpoint |

### Validation Gates Per Change

| Change Type | Required Checks |
|---|---|
| Python backend | `pytest tests/ -v` + `ruff check .` + `mypy` |
| TypeScript frontend | `npx tsc --noEmit` + `npm run lint` + `npm run test` |
| AI prompt change | AI eval suite in Langsmith before merge |
| Database schema | Migration reversibility test (`alembic downgrade -1` in dev) |
| New API endpoint | OpenAPI schema check + integration test |
| UI change | `npm run test:e2e` for affected flows |

### Test Organization

```
apps/api/tests/
├── unit/           # Pure function tests for engines and services
├── integration/    # Route tests with TestClient + test MongoDB
└── fixtures/       # Shared pytest fixtures

apps/web/tests/
├── unit/           # Vitest component and hook tests
└── e2e/            # Playwright end-to-end specs

tests/              # Root-level integration tests (cross-service)
```

### Testing Rules

- Every new service method gets a unit test before merging.
- Every new API route gets an integration test.
- Flaky tests are quarantined and tracked as P1 issues.
- Never skip a failing test without documenting why and creating a follow-up issue.
- AI output tests use deterministic seeds and recorded responses where possible.

---

## §19 — OBSERVABILITY REQUIREMENTS

### Observability Stack

| Tool | Role | Where |
|---|---|---|
| Sentry | Error tracking, exception capture | All services, 5,000 errors/month free |
| Langfuse / Langsmith | LLM prompt tracing, evaluation | ai-services/ all AI calls |
| Prometheus | Metrics collection | infrastructure/monitoring/ |
| Grafana | Metrics dashboards | infrastructure/monitoring/ |
| Structured logging | JSON logs per service | packages/logger/ |

### Required Instrumentation (Day 1)

- **HTTP request logging:** method, path, status code, latency, user_id
- **AI call logging:** provider, prompt_tokens, completion_tokens, latency_ms, success/failure
- **Business event logging:** quest_generated, quest_completed, level_up, streak_broken
- **Error capture:** all unhandled exceptions to Sentry with user context
- **Health endpoints:** `GET /health` (liveness) + `GET /health/ready` (readiness)

### SLO Targets

| Metric | Target |
|---|---|
| Quest generation latency (p95) | < 1500ms (cold) |
| Quest fetch from cache (p95) | < 100ms |
| Dashboard load (p95) | < 800ms |
| API uptime | > 99.5% |
| Error rate | < 1% of requests |

### Alerting Rules

- Error rate > 5% for 5 minutes → PagerDuty (P1)
- Quest generation latency p95 > 3s for 10 minutes → Slack (P2)
- Groq API failure rate > 20% → auto-activate Phi-2 fallback (automated)
- MongoDB Atlas connection failures > 3 in 1 minute → Slack (P1)

---

## §20 — SECURITY REQUIREMENTS

### Authentication & Authorization

- Supabase Auth is the ONLY authentication provider. No custom auth tables.
- JWT validation happens in FastAPI middleware (`middleware/auth.py`). Never in route handlers.
- JWT tokens expire in 1 hour. Refresh tokens expire in 7 days.
- Frontend refreshes tokens silently via React Query before expiry.
- All API routes require JWT except: `GET /health`, `POST /auth/login`.
- Admin routes require `role: admin` in JWT claims. Role checked via FastAPI dependency.

### Secrets Management

| Variable | Required | Purpose |
|---|---|---|
| `SUPABASE_URL` | ✅ | Supabase project URL |
| `SUPABASE_ANON_KEY` | ✅ | Supabase public anon key |
| `SUPABASE_SERVICE_ROLE_KEY` | ✅ | Supabase admin key (backend only) |
| `SUPABASE_JWT_SECRET` | ✅ | JWT validation |
| `MONGODB_URL` | ✅ | MongoDB Atlas connection string |
| `MONGODB_DB_NAME` | ✅ | MongoDB database name |
| `GROQ_API_KEY` | ✅ | Primary Groq API key |
| `GROQ_API_KEYS` | Opt | Comma-separated rotation keys |
| `UPSTASH_REDIS_REST_URL` | ✅ | Upstash Redis REST URL |
| `UPSTASH_REDIS_REST_TOKEN` | ✅ | Upstash Redis token |
| `SENTRY_DSN` | Opt | Error tracking |
| `NEXT_PUBLIC_API_URL` | ✅ | Frontend → backend URL |
| `NEXT_PUBLIC_SUPABASE_URL` | ✅ | Frontend Supabase URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | ✅ | Frontend Supabase key |

**Secrets Rules:**
- NEVER commit `.env`, `*.env.local`, or any file containing secrets.
- NEVER log secrets. Never log full JWT tokens.
- NEVER hardcode API keys in source. Always env vars.
- NEVER read `.env` file contents in agent tasks. Only verify existence with `ls -la`.

### Input Validation

- All API inputs validated via Pydantic schemas with `model_config = {"extra": "forbid"}`.
- All user-submitted code sanitized before sandbox execution.
- Rate limiting enforced at API gateway level AND per-route via Redis counters.
- Rate limits: quest generation 5/day/user; evaluation 10/day/user; progress updates 100/day/user.

---

## §21 — PERFORMANCE RULES

### XP Calculation Formula

```python
xp_earned = (
    base_xp[difficulty]          # easy:50, medium:100, hard:200, boss:500
    * difficulty_multiplier       # 0.5–2.0 from adaptive engine
    * streak_multiplier           # 1.00–2.00 based on streak_count
    * time_bonus_multiplier       # 1.2 if completed < 80% of estimated_time
    * quest_type_multiplier       # theory:0.8, coding:1.0, debug:1.1, build:1.3
)
```

### Level Progression Formula

```python
xp_for_level(N) = 100 * (N ** 1.8)
current_level = floor((total_xp / 100) ** (1/1.8))
```

### Caching Strategy

| Data | Cache | TTL | Invalidation |
|---|---|---|---|
| Today's quests | Redis + IndexedDB | 24 hours | On quest generation |
| Dashboard state | React Query | 60 seconds | On any XP/streak change |
| Skill tree state | React Query | 5 minutes | On node progress update |
| Leaderboard | Supabase materialized view | 15 minutes | Scheduled refresh |
| User profile | React Query | 2 minutes | On profile update |

### Performance Budget

- **First Contentful Paint:** < 1.5s (Vercel CDN)
- **Time to Interactive:** < 3s
- **Bundle size (initial):** < 200KB gzipped
- **API response (non-AI):** < 200ms p95
- **Quest generation:** < 1200ms cold, < 80ms cached
- Use `next/dynamic` for: Framer Motion, Recharts, DAG visualizer, Monaco editor

---

## §22 — CI/CD RULES

### Pipeline: GitHub Actions

```yaml
# Trigger: push to main or PR to main
Pipeline:
  test:
    - pytest apps/api/tests/ -v --cov
    - npx vitest run apps/web
    - npx tsc --noEmit (apps/web)
  lint:
    - ruff check apps/api/
    - mypy apps/api/app/
    - eslint apps/web/src/
  build:
    - docker build apps/api/ -t cognarc-api
    - npm run build (apps/web)
  deploy (main only):
    - Railway: railway up --service cognarc-api
    - Vercel: automatic via GitHub integration
```

### Branch Strategy

- `main` — production-ready. Protected. Requires PR + 1 review + all CI green.
- `develop` — integration branch. All feature PRs target here first.
- `feat/phase-N` — phase-locked feature branches. Phase 2 code never merges to main before Day 10 MVP gate.
- `feat/<description>` — individual feature branches. Max 3 days before merge.
- `fix/<issue>` — bug fix branches.
- `chore/<task>` — maintenance tasks.

### Commit Convention

Format: `type(scope): short description`

Types: `feat`, `fix`, `chore`, `refactor`, `test`, `docs`, `ci`, `perf`

Examples:
```
feat(quests): add BGE-small deduplication to quest generation pipeline
fix(gamification): correct streak multiplier boundary at day 14
chore(docker): upgrade python base image to 3.11-slim
perf(api): add Redis caching to dashboard endpoint
```

### Deployment Rules

- NEVER `git push --force` to `main`.
- NEVER merge a PR with failing tests.
- NEVER deploy to production without staging validation.
- Every deployment triggers a smoke test: `curl /health` → 200 OK.
- Rollback plan: Railway one-click rollback to previous deployment.

---

## §23 — DOCUMENTATION RULES

### Required Documentation

| Document | Location | Updated When |
|---|---|---|
| Architecture Decision Records | `docs/decisions/ADR-*.md` | Any significant tech decision |
| API Reference | `docs/api/` | Any API contract change |
| Deployment Runbook | `docs/deployment/` | Any infra change |
| Incident Runbooks | `docs/runbooks/` | After every P1 incident |
| AI System Docs | `docs/ai/` | Any AI pipeline change |
| Onboarding Guide | `docs/onboarding/` | Monthly review |

### ADR Format

```markdown
# ADR-NNN: Title
Date: YYYY-MM-DD
Status: Proposed | Accepted | Deprecated | Superseded

## Context
Why is this decision needed?

## Decision
What was decided?

## Consequences
What are the trade-offs?
```

### Documentation Rules

- API contracts documented in OpenAPI (auto-generated by FastAPI). Manually annotated with `summary`, `description`, `response_model`.
- Every new feature requires a corresponding `docs/` entry before the PR is merged.
- Diagrams use Mermaid in Markdown files. No proprietary diagram tools.

---

## §24 — GIT WORKFLOW

### Agent Git Rules

1. ALWAYS run `git status` and `git diff --stat` before starting any task.
2. Read all files you will touch BEFORE editing them. Never blind-edit.
3. Make minimal diffs. One logical change per commit.
4. Before committing: `git diff --staged` to verify exactly what is being committed.
5. NEVER commit: `.env` files, model weights (`*.pt`, `*.gguf`), `__pycache__/`, `.next/`, secrets of any kind.
6. NEVER revert or overwrite user-made commits without explicit instruction.
7. NEVER `git push --force` to `main`.
8. If worktree is dirty on task start: stash only if changes are clearly unrelated. Document stashed changes in report.

### PR Checklist (Definition of Done)

- [ ] All changed files were read before editing
- [ ] Code changes are minimal and scoped to the task
- [ ] No secrets, debug logs, or commented-out code
- [ ] `npx tsc --noEmit` passes (frontend)
- [ ] `ruff check .` passes (backend)
- [ ] `pytest tests/ -v` passes (backend)
- [ ] `npm run test` passes (frontend)
- [ ] `git diff --staged` reviewed before commit
- [ ] Commit message follows convention
- [ ] No unrelated files modified
- [ ] Any unrun tests documented with reason

---

## §25 — TASK EXECUTION RULES

### Standard Execution Loop

```
DISCOVER → PLAN → EDIT → VALIDATE → REPORT
```

**DISCOVER:** Read all files in scope. Trace imports. Identify test coverage.

**PLAN:** State what will change and why. List all affected files. Identify required tests.

**EDIT:** Minimal diff. Match existing code style. No unrelated changes.

**VALIDATE:** Run tier-appropriate validation (see §18).

**REPORT:**
```
## Task Complete: [Task Name]

### Changes Made
- [file]: [what changed and why]

### Tests Run
- ✅ [test command] — [N tests passed]
- ⚠️ [test command] — skipped ([reason + risk level])

### Residual Risk
[Low/Medium/High] — [explanation]

### Outstanding Items
[Follow-up tasks or known issues]
```

### When to Stop and Ask

- Task touches auth middleware, JWT logic, or Supabase RLS rules
- Correct behavior is genuinely ambiguous after reading the code
- Tests fail for reasons unrelated to your change
- Task requires deleting files or reverting user changes
- Task scope has expanded beyond original description
- Any production data or credentials are involved

---

## §26 — CODE REVIEW RULES

### Review Checklist

**Architecture:**
- [ ] No business logic in route handlers
- [ ] No DB queries in service layer
- [ ] No AI calls outside ai-services/
- [ ] No circular imports
- [ ] No cross-feature direct imports (must go through packages/)

**Code Quality:**
- [ ] No `any` types in TypeScript
- [ ] No `print()`/`console.log()` in committed code
- [ ] All new functions have docstrings (Python) or JSDoc (TS, for non-obvious functions)
- [ ] File length < 300 lines
- [ ] No hardcoded secrets or magic numbers

**Testing:**
- [ ] New service methods have unit tests
- [ ] New API routes have integration tests
- [ ] No skipped tests without documented reason

**Security:**
- [ ] All inputs validated via Pydantic/Zod
- [ ] No secrets in diff
- [ ] User code never directly executed (sandboxed only)

**UI/UX Constraints (Tactical IDE):**
- [ ] No trace of the color purple/magenta/violet in Tailwind classes.
- [ ] No drop shadows or backdrop-blur. 
- [ ] Heavy use of monospace fonts for data and 1px sharp borders.

---

## §27 — ABSOLUTE DO-NOT-DO LIST

The following actions are FORBIDDEN without explicit written user instruction:

| Action | Risk Level | Why |
|---|---|---|
| `docker compose down -v` | CRITICAL | Destroys all volumes (data loss) |
| `DROP TABLE` / `TRUNCATE` | CRITICAL | Permanent data loss |
| `git push --force` to main | CRITICAL | Overwrites shared history |
| Deleting MongoDB collections | CRITICAL | Permanent data loss |
| `exec()` / `eval()` on user code | CRITICAL | Remote code execution |
| Modifying `.github/workflows/` | HIGH | Breaks CI/CD for all developers |
| Editing applied Alembic migrations | HIGH | Corrupts migration history |
| Reading `.env` file contents | HIGH | Secrets exposure |
| Logging JWT tokens or API keys | HIGH | Security breach |
| Implementing Phase 2+ features before MVP gate | HIGH | Project failure pattern |
| Importing ai-services directly into apps/api services | HIGH | Violates architecture boundary |
| Adding Redux or MobX | MEDIUM | Violates state management contract |
| Making fetch/axios calls from React components | MEDIUM | Violates API layer contract |
| Duplicating type definitions outside packages/shared-types | MEDIUM | Type drift |
| Committing model weights (*.pt, *.gguf) | MEDIUM | Binary bloat in git history |
| Auto-formatting entire files without task scope | LOW | Diff noise, masks real changes |
| Adding `console.log` / `print()` to committed code | LOW | Log pollution |

---

## §28 — FAILURE RECOVERY RULES

### Environment Failures

```bash
# Service down
docker compose ps
docker compose logs backend --tail=50
docker compose restart backend

# MongoDB connection failure
# → Serve cached quests from Redis
# → Log all progress locally in IndexedDB
# → Batch sync on reconnect
# → Show system status banner in UI

# Groq API down
# → Phase 1: serve yesterday's cached quests with UI notice
# → Phase 2+: activate Phi-2 local fallback automatically

# Railway free credit exhaustion
# → Render.com as FastAPI backup
# → Fly.io as Go services backup

# Nuclear reset (CONFIRM WITH USER FIRST)
docker compose down -v
docker compose up -d --build
```

### Code Failures

```bash
# Tests failing
git stash && pytest tests/ -v && git stash pop  # Check if pre-existing

# Frontend broken
cd apps/web && rm -rf .next && npm run dev

# Type errors
cd apps/web && npx tsc --noEmit 2>&1 | head -50
```

### Failure Recovery Matrix

| Failure | Severity | Automated Recovery |
|---|---|---|
| Groq API down | HIGH | Phi-2 fallback (Phase 2+), else cached quests |
| MongoDB Atlas down | CRITICAL | Redis cache serving, local queue |
| Railway crash | HIGH | Auto-restart; frontend shows retry with backoff |
| Evaluator failure | MEDIUM | 50% partial XP, async re-evaluation |
| Streak sync conflict | MEDIUM | Server authoritative, notify user |
| Sandboxed eval timeout | HIGH | Return timeout error, no XP awarded |

### When to Escalate Immediately

- Any production data loss (even 1 record)
- Auth bypass (any user accessing another user's data)
- Secrets exposed in logs or git history
- Groq API cost spike (check usage dashboard immediately)

---

## §29 — SCALING STRATEGY

### Free Tier Constraints + Mitigations

| Constraint | Value | Mitigation |
|---|---|---|
| Groq free rate limit | 30 req/min, 14,400/day | Redis cache (1 call/user/day baseline); BGE dedup reduces retries |
| MongoDB Atlas M0 | 512MB | TTL indexes on embeddings (30d), archive logs (90d) |
| Supabase free | 500MB DB, 50K MAU | Materialized views, efficient queries |
| Upstash Redis | 10,000 req/day | Streak + cache only (3 ops/user/day = 3,333 users covered) |
| Railway | $5 credit/month | MVP monolith: 0.5 vCPU + 512MB fits comfortably |
| Vercel Hobby | 100GB bandwidth | Static assets via CDN, aggressive caching |

### Scaling Triggers (When to Upgrade)

| Metric | Trigger | Action |
|---|---|---|
| API latency p95 > 500ms | > 1,000 DAU | Upgrade Railway plan; add connection pooling |
| MongoDB > 400MB | > 5,000 users | Upgrade Atlas or archive data |
| Groq rate limit hits | > 500 DAU | Add key rotation (GROQ_API_KEYS) or upgrade plan |
| Redis > 8,000 req/day | > 2,500 DAU | Upgrade Upstash |

### Horizontal Scaling Path (Phase 3+)

1. Add Railway replica for API service (stateless, no code changes required)
2. Split into microservices (see §15 migration rules)
3. Add CDN layer (Cloudflare) in front of Railway
4. Move to dedicated MongoDB Atlas cluster (M10+)
5. Add read replicas for leaderboard queries

---

## §30 — FUTURE AGENTIC AI ROADMAP

### Phase 4 LangGraph Architecture (Days 46–70)

```python
# Agent State Machine
class CognarcAgentState(TypedDict):
    user_id: str
    skill_state: dict
    behavioral_profile: dict
    weekly_plan: list[dict]       # Planner output
    today_quests: list[dict]      # TaskGenerator output
    evaluation_results: list[dict] # Evaluator output
    adaptation_signals: dict       # Adaptation output

# Graph Definition
graph = StateGraph(CognarcAgentState)
graph.add_node("planner", planner_agent)
graph.add_node("task_generator", task_generator_agent)
graph.add_node("evaluator", evaluator_agent)
graph.add_node("adaptation", adaptation_agent)  # No LLM — pure Python

graph.add_edge("planner", "task_generator")
graph.add_conditional_edges("task_generator", route_to_evaluator)
graph.add_edge("evaluator", "adaptation")
```

### Future Feature Roadmap (Post-Phase 4)

| Feature | Priority | Effort |
|---|---|---|
| React Native mobile app (Expo) | P0 | 3 months |
| Guild/multiplayer system | P0 | 2 months |
| AI Tutor Mode (per-quest conversational AI) | P1 | 2 months |
| Quest Marketplace (community-created quests) | P1 | 3 months |
| Company Team Plans (manager dashboard) | P1 | 2 months |
| Job Integration (LinkedIn/Wellfound skill gap) | P2 | 1 month |
| Phi-2 fine-tuning on quest-completion data | P3 | 4 months |
| Browser extension (XP goal status) | P3 | 1 month |

### Multi-Agent System Rules (Phase 4+)

- All agent state stored in `users.agent_state` in MongoDB. Never in memory.
- Planner agent runs Sunday night + after every boss battle (background job).
- TaskGenerator runs at 05:00 AM user-local time (scheduled via Railway cron).
- Adaptation agent is ALWAYS async. It NEVER blocks the HTTP response.
- LangGraph graph must complete in < 30s for synchronous paths.
- All agent invocations logged to Langfuse with full input/output trace.

---

## §31 — DESIGN SYSTEM REFERENCE

### Animation Specifications

| Animation | Trigger | Library | Duration |
|---|---|---|---|
| XP Bar Fill | Quest completion | Framer Motion (spring) | 0.8s ease-out |
| Level-Up Burst | XP crosses threshold | Framer Motion (full-screen) | 3.5s (unskippable) |
| Quest Completion | Mark complete | Framer Motion (card flip + green glow) | 0.4s |
| Streak Extension | First completion of day | Framer Motion (pulse) | 0.6s |
| Boss Battle Entry | Enter boss battle | Framer Motion (dim + title card) | 2.0s |
| Skill Node Unlock | Node mastery achieved | Framer Motion (gold pulse) | 1.5s |

### Dashboard Layout

```
┌──────────────────────────────────────────────────────────────┐
│ HEADER: Logo | Level 14 ▓▓▓▓▓░ 45,231 XP | 🔥 8 | Avatar   │
├──────────────────────────────────────────────────────────────┤
│  TODAY'S QUESTS (3)              │  SKILL TREE               │
│  [Quest Card 1 — CODING]         │  AI Engineering ▶         │
│  [Quest Card 2 — THEORY]         │  ◉ Python Basics ✓        │
│  [Quest Card 3 — DEBUG]          │  ◎ RAG Systems ← you      │
│                                  │  ○ Agentic AI (locked)    │
├──────────────────────────────────────────────────────────────┤
│  STREAK 🔥 8 days  │  BOSS BATTLE ⚔ AVAILABLE!  │ #47 Top 4%│
├──────────────────────────────────────────────────────────────┤
│  ACTIVITY (90 days — GitHub heatmap style, purple tones)     │
└──────────────────────────────────────────────────────────────┘
```

---

## §32 — QUICK REFERENCE: COMMON COMMANDS

```bash
# Local development
docker compose up -d                          # Start all services
docker compose logs -f api                    # Watch API logs
docker compose restart api                    # Restart API service

# Frontend
cd apps/web && npm run dev                    # Dev server (port 3000)
cd apps/web && npx tsc --noEmit              # Type check
cd apps/web && npm run lint                   # ESLint
cd apps/web && npm run test                   # Vitest unit tests
cd apps/web && npm run test:e2e              # Playwright E2E

# Backend
cd apps/api && uvicorn app.main:app --reload  # Dev server (port 8000)
cd apps/api && pytest tests/ -v              # Unit + integration tests
cd apps/api && ruff check app/               # Linter
cd apps/api && mypy app/                     # Type check

# Health checks
curl http://localhost:8000/health             # API liveness
curl http://localhost:3000/api/health        # Frontend BFF health

# Production
railway up --service cognarc-api             # Deploy API to Railway
vercel --prod                                # Deploy frontend to Vercel
```

---

*COGNARC Engineering Governance Document — v2.0 Execution Edition*
*Generated: 2026-05-06 | Covers: MVP through Phase 4 Agentic AI*
*Owner: Principal Engineering | Reviewed by: senior-architect + senior-fullstack skills*


<!-- code-review-graph MCP tools -->
## MCP Tools: code-review-graph

**IMPORTANT: This project has a knowledge graph. ALWAYS use the
code-review-graph MCP tools BEFORE using Grep/Glob/Read to explore
the codebase.** The graph is faster, cheaper (fewer tokens), and gives
you structural context (callers, dependents, test coverage) that file
scanning cannot.

### When to use graph tools FIRST

- **Exploring code**: `semantic_search_nodes` or `query_graph` instead of Grep
- **Understanding impact**: `get_impact_radius` instead of manually tracing imports
- **Code review**: `detect_changes` + `get_review_context` instead of reading entire files
- **Finding relationships**: `query_graph` with callers_of/callees_of/imports_of/tests_for
- **Architecture questions**: `get_architecture_overview` + `list_communities`

Fall back to Grep/Glob/Read **only** when the graph doesn't cover what you need.

### Key Tools

| Tool | Use when |
|------|----------|
| `detect_changes` | Reviewing code changes — gives risk-scored analysis |
| `get_review_context` | Need source snippets for review — token-efficient |
| `get_impact_radius` | Understanding blast radius of a change |
| `get_affected_flows` | Finding which execution paths are impacted |
| `query_graph` | Tracing callers, callees, imports, tests, dependencies |
| `semantic_search_nodes` | Finding functions/classes by name or keyword |
| `get_architecture_overview` | Understanding high-level codebase structure |
| `refactor_tool` | Planning renames, finding dead code |

### Workflow

1. The graph auto-updates on file changes (via hooks).
2. Use `detect_changes` for code review.
3. Use `get_affected_flows` to understand impact.
4. Use `query_graph` pattern="tests_for" to check coverage.

---

## §33 — BUILD PROGRESS TRACKER

> **AGENT INSTRUCTIONS:** Read this section FIRST at the start of every session.
> This is the authoritative record of what has been built and validated in production.
> Only check a box when the validation gate has passed. Checked = done. Empty = not started.
> Update "Last Updated", "Current Phase", and the Summary table whenever you check a gate.

**Last Updated:** 2026-05-06
**Current Phase:** Planning complete — ready to begin Phase 1
**Current Day:** Day 0 (pre-build)
**Production URL (API):** _not yet deployed_
**Production URL (Web):** _not yet deployed_

---

### PHASE 1 — FOUNDATION (Days 1–3 target)
_Goal: Monorepo, Docker, Next.js, FastAPI, Supabase Auth, MongoDB Atlas_

#### Scaffold & Docker
- [ ] T1.1 — Turborepo initialized with pnpm workspaces
- [ ] T1.2 — `pnpm-workspace.yaml` configured (`apps/*`, `packages/*`)
- [ ] T1.3 — `turbo.json` pipelines: build, dev, test, lint
- [ ] T1.4 — `apps/api/` FastAPI skeleton scaffolded (`main.py`, `config.py`, `health.py`)
- [ ] T1.5 — `apps/web/` Next.js 14 App Router scaffolded
- [ ] T1.6 — `packages/shared-types/` created (exports: `User`, `Quest`, `Progress`)
- [ ] T1.7 — `packages/design-tokens/` created (CSS variables: purples, golds, dark surfaces)
- [ ] T1.8 — `packages/logger/` created (structured JSON logger stub)
- [ ] T1.9 — Root `Makefile` created (`dev`, `test`, `lint`, `build`, `deploy`)
- [ ] T1.10 — `docker-compose.yml` written (api :8000, web :3000, cognarc-net)
- [ ] T1.11 — `docker-compose.dev.yml` written (volume mounts for hot reload)
- [ ] T1.12 — `infrastructure/docker/api/Dockerfile` written (python:3.11-slim)
- [ ] T1.13 — `infrastructure/docker/web/Dockerfile` written (multi-stage Next.js)
- [ ] T1.14 — `GET /health`, `GET /health/ready`, `GET /health/live` implemented
- [ ] **GATE 1A:** `docker compose up -d` → `curl localhost:8000/health` → `{"status":"ok"}`

#### Supabase Auth + JWT
- [ ] T2.1 — Supabase project created, Magic Link enabled
- [ ] T2.2 — Env vars set: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`
- [ ] T2.3 — `apps/api/app/middleware/auth.py` implemented (python-jose JWT decode, 401 on fail)
- [ ] T2.4 — `apps/api/app/core/dependencies.py` implemented (`get_current_user`, `require_admin`)
- [ ] T2.5 — `apps/api/app/adapters/supabase_adapter.py` implemented (retry/timeout)
- [ ] T2.6 — `apps/api/app/api/v1/auth.py` implemented (`/auth/login`, `/auth/logout`, `/auth/refresh`)
- [ ] T2.7 — `packages/auth-client/` implemented (Next.js magic link wrapper)
- [ ] T2.8 — `apps/web/src/middleware.ts` implemented (route-level auth guard)
- [ ] **GATE 1B:** Register → JWT → `GET /users/me` with token → 200; without → 401

#### MongoDB Atlas
- [ ] T3.1 — MongoDB Atlas M0 cluster created; Railway + local IPs whitelisted
- [ ] T3.2 — DB user created; `MONGODB_URL`, `MONGODB_DB_NAME` set in env
- [ ] T3.3 — `apps/api/app/db/mongodb.py` implemented (Motor async singleton)
- [ ] T3.4 — `apps/api/app/models/user.py` implemented (Pydantic, all fields)
- [ ] T3.5 — `apps/api/app/repositories/mongo/user_repository.py` implemented
- [ ] T3.6 — `apps/api/app/services/user_service.py` implemented
- [ ] T3.7 — `GET /users/me`, `PATCH /users/me` implemented
- [ ] T3.8 — MongoDB indexes applied (`auth_id` unique, `level` regular)
- [ ] **GATE 1C:** Login → `GET /users/me` → MongoDB document returned → 200

#### CI/CD
- [ ] T4.1 — `.github/workflows/ci.yml` created (pytest + ruff + tsc + eslint on PR)
- [ ] T4.2 — `.github/workflows/deploy.yml` created (Railway + Vercel on push to `main`)
- [ ] T4.3 — Vercel linked to GitHub repo
- [ ] T4.4 — Railway service `cognarc-api` configured
- [ ] T4.5 — Smoke test step added to deploy workflow
- [ ] **GATE 1D:** Open PR → GitHub Actions: test ✅ lint ✅ build ✅

**Phase 1 STATUS:** ⬜ Not Started | 🟡 In Progress | ✅ Complete

---

### PHASE 2 — DATA MODELING (Days 3–5 target)
_Goal: All MongoDB collections, Supabase SQL, indexes, CRUD repositories_

- [ ] T1.1 — `app/models/user.py` full model (SkillState, BehavioralProfile, UserSettings)
- [ ] T1.2 — `app/models/quest.py` full model (EvaluationCriteria, all fields)
- [ ] T1.3 — `app/models/progress_log.py` created
- [ ] T1.4 — `app/models/streak.py` created
- [ ] T2.1–T2.4 — All Pydantic schemas (user, quest, progress) + shared-types TS mirror
- [ ] T3.1–T3.5 — All MongoDB indexes applied + TTL indexes (users, quests, progress_logs)
- [ ] T4.1 — `user_repository.py` fully implemented (5 methods)
- [ ] T4.2 — `quest_repository.py` fully implemented (5 methods)
- [ ] T4.3 — `progress_repository.py` fully implemented (3 methods + aggregation)
- [ ] T4.4 — `streak_repository.py` fully implemented (2 methods)
- [ ] T4.5 — `redis_cache.py` fully implemented (quest cache + streak counters)
- [ ] T5.1 — Supabase SQL migration `001_initial_schema.sql` applied (leaderboard, achievements, boss_battles)
- [ ] T5.2 — Supabase RLS policies configured on all public tables
- [ ] T6.1–T6.3 — Seed scripts created (skill_trees.json, seed_user.py, seed_quests.py)
- [ ] **GATE 2A:** `pytest tests/integration/ tests/unit/ -k "repo or model or cache"` — all green
- [ ] **GATE 2B:** `GET /users/me` → full user doc with `skill_state` and `behavioral_profile`

**Phase 2 STATUS:** ⬜ Not Started | 🟡 In Progress | ✅ Complete

---

### PHASE 3 — MVP AI PIPELINE (Days 4–6 target)
_Goal: Groq adapter, versioned prompt, quest generation, XP calculation_

- [ ] T1.1–T1.3 — `ai-services/` scaffold + requirements + public `generate_quests()` interface
- [ ] T2.1–T2.4 — `groq_adapter.py` implemented (retry, key rotation, timeout, Langfuse logging)
- [ ] T3.1–T3.3 — `quest_generation_v1.py` prompt + v2 stub + prompt registry
- [ ] T4.1 — `quest_output_parser.py` implemented (json.loads → ParsedQuest × 3)
- [ ] T4.2 — `quest_validator.py` implemented (type/difficulty/xp/distinct checks + sanitization)
- [ ] T5.1 — `quest_service.py` implemented (context → Groq → validate → persist → cache)
- [ ] T5.2 — `POST /quests/generate`, `GET /quests/today`, `POST /quests/{id}/skip` implemented
- [ ] T5.3 — `gamification_engine.calculate_xp()` implemented (all multipliers)
- [ ] T5.4 — `POST /quests/{id}/evaluate` implemented (self-report MVP, XP award, streak update)
- [ ] T6.1 — `quest_context_builder.py` implemented (5 data sources, sanitization)
- [ ] **GATE 3A:** `POST /ai/generate` with hardcoded context → 3 valid quest objects
- [ ] **GATE 3B:** `POST /quests/generate` real user context → quests stored in MongoDB < 1500ms
- [ ] **GATE 3C:** Second `/quests/generate` call → same 3 quests returned (idempotent)
- [ ] **GATE 3D:** `pytest -k "quest or groq or xp"` — all green

**Phase 3 STATUS:** ⬜ Not Started | 🟡 In Progress | ✅ Complete

---

### PHASE 4 — FRONTEND UI (Days 7–8 target)
_Goal: Feature-first Next.js dashboard, Zustand stores, Dexie.js offline cache, quest display_

- [ ] T1.1–T1.4 — Design tokens CSS vars, Google Fonts, Tailwind config, globals.css
- [ ] T2.1–T2.2 — All 7 feature directories scaffolded + `shared/` subdirs
- [ ] T3.1–T3.3 — `useUserStore.ts`, `useGamificationStore.ts` implemented + devtools
- [ ] T4.1–T4.2 — Dexie `CognarcDB` v1 + `questCache.ts` utility
- [ ] T5.1 — `features/quests/api/questsApi.ts` (no raw fetch from components)
- [ ] T5.2 — `features/quests/hooks/useQuests.ts` (React Query + Dexie fallback)
- [ ] T5.3 — `QuestCard.tsx` (title, type badge, difficulty, XP, "Mark Complete")
- [ ] T5.4 — `QuestList.tsx` (3 cards, skeleton, offline banner)
- [ ] T6.1 — `XpBar.tsx` (CSS transition, reads Zustand)
- [ ] T6.2 — `LevelBadge.tsx` (level + tier name)
- [ ] T6.3 — `StreakDisplay.tsx` (flame + count, gold color)
- [ ] T7.1–T7.4 — Dashboard page, authenticated layout, login page, auth callback
- [ ] T8.1 — `SkillTreeSidebar.tsx` (text list: ◎ current, ✓ mastered, ○ locked)
- [ ] T9.1–T9.2 — `providers.tsx` + React Query config + `layout.tsx` updated
- [ ] **GATE 4A:** `npx tsc --noEmit` → 0 errors; `npm run lint` → 0 warnings
- [ ] **GATE 4B:** Dashboard loads, 3 quest cards visible, mark complete → XP bar updates (no reload)
- [ ] **GATE 4C:** Go offline → quests still visible from Dexie + offline banner shown

**Phase 4 STATUS:** ⬜ Not Started | 🟡 In Progress | ✅ Complete

---

### PHASE 5 — MVP GAMIFICATION (Days 8–9 target)
_Goal: Complete XP formula, level engine, Redis streak counters, end-to-end wiring_

- [ ] T1.1 — `gamification_engine.calculate_xp()` (all multipliers)
- [ ] T1.2 — `gamification_engine.calculate_level()` + `xp_for_level()`
- [ ] T1.3 — `gamification_engine.get_level_tier()` (6 tiers)
- [ ] T2.1 — `streak_engine.py` (increment/reset/shield logic)
- [ ] T2.2 — Redis streak counters + `last_completion_date` in `redis_cache.py`
- [ ] T2.3 — `streak_repository.py` `get_streak()` + `upsert_streak()`
- [ ] T3.1 — `gamification_service.award_quest_xp()` (full pipeline)
- [ ] T3.2 — `gamification_service.update_streak()` (Redis cache + MongoDB source of truth)
- [ ] T3.3 — `GET /gamification/dashboard` implemented
- [ ] T3.4 — `GET /gamification/xp` (7-day history)
- [ ] T4.1 — `QuestCompletedEvent` + `StreakBrokenEvent` defined
- [ ] T5.1 — `useGamificationStore.awardXp()` (level + progress recomputation)
- [ ] T5.2 — `QuestCard.tsx` updated (completeQuest → awardXp → toast)
- [ ] T5.3 — `XpBar.tsx` reads Zustand `progressPct`
- [ ] T5.4 — `StreakDisplay.tsx` shows multiplier badge (streak ≥ 7)
- [ ] **GATE 5A:** `calculate_xp('medium', 8, 20, 25, 'coding', 1.0)` == 125 (formula verified)
- [ ] **GATE 5B:** `POST /quests/{id}/evaluate` → `{xp_awarded, new_level, progress_pct, streak}` correct
- [ ] **GATE 5C:** `pytest -k "gamification or streak"` — all green
- [ ] **GATE 5D:** Mark quest complete → XP bar + streak updates (no reload)

**Phase 5 STATUS:** ⬜ Not Started | 🟡 In Progress | ✅ Complete

---

### PHASE 6 — MVP DEPLOYMENT / DAY 10 GATE (Day 10)
_Goal: Railway + Vercel on production, full E2E validation_

- [ ] T1.1–T1.3 — `Dockerfile.prod` finalized, image < 500MB, local run verified
- [ ] T2.1–T2.10 — Railway `cognarc-api` deployed, all env vars set, health probe active
- [ ] T3.1–T3.7 — Vercel linked, `vercel.json` configured, production deploy live
- [ ] T4.1–T4.3 — GitHub Actions CI + Deploy workflows finalized, secrets configured
- [ ] T5.1–T5.3 — Playwright E2E test written + added to CI
- [ ] T6.1–T6.4 — Sentry configured, alerts set, rollback doc written
- [ ] T7.1–T7.4 — Atlas IP allowlist, monitoring alerts, backup plan documented
- [ ] **GATE 6A:** `curl https://<railway-url>/health` → 200
- [ ] **GATE 6B:** `curl https://<railway-url>/health/ready` → `{"database":"connected","cache":"connected"}`
- [ ] **GATE 6C:** New user: register → quests → complete → XP updates < 5 minutes total
- [ ] **GATE 6D:** Playwright E2E passes on production URL
- [ ] **GATE 6E:** GitHub Actions CI green on `main` for 24h straight

**⚠️ PHASE 2+ CODE FROZEN UNTIL ALL GATE 6 CHECKS PASS ⚠️**

**Phase 6 STATUS:** ⬜ Not Started | 🟡 In Progress | ✅ Complete

---

### PHASE 7 — MICROSERVICES & GO GATEWAY (Days 11–25 target)
_Trigger: 14+ days stable production. Extract ONE service at a time._

- [ ] **PRE-CHECK:** MVP stable in production ≥ 14 days (start date: _________)
- [ ] T1.1–T1.5 — `apps/gateway/` Go/Gin: JWT middleware, rate limiter, reverse proxy router
- [ ] T1.6–T1.9 — `cognarc-gateway` Railway service deployed + `NEXT_PUBLIC_API_URL` updated
- [ ] **GATE 7A:** Auth through gateway works; rate limit → 429 after 5 quest/generate calls
- [ ] T2.1–T2.4 — `apps/quest-service/` extracted, gateway route updated, 48h validation
- [ ] T3.1–T3.4 — `apps/user-service/` (Go/Fiber) extracted, gateway route updated
- [ ] T4.1–T4.2 — `apps/gamification-service/` extracted, gateway route updated
- [ ] T5.1–T5.4 — Service contracts documented, circuit breakers added
- [ ] T6.1–T6.4 — BGE-small embedder + deduplication active in Quest Service
- [ ] **GATE 7B:** All 4 service health checks → 200; E2E Playwright no regressions

**Phase 7 STATUS:** ⬜ Not Started | 🟡 In Progress | ✅ Complete

---

### PHASE 8 — OFFLINE & HYBRID EVALUATION (Days 11–25 target)

- [ ] T1.1–T1.5 — next-pwa configured, manifest.json, service worker registered in Chrome
- [ ] T2.1–T2.4 — Dexie v2 schema, `syncManager.ts`, online listener, offline quest completion
- [ ] T3.1–T3.3 — Push notifications: Edge Function, `/notifications/subscribe`, frontend hook
- [ ] T4.1 — `sandbox_runner.py` (subprocess, timeout=10, no network)
- [ ] T4.2 — `ai_feedback.py` (Groq, advisory, non-blocking)
- [ ] T4.3 — `POST /quests/{id}/evaluate` updated (test cases primary, AI secondary)
- [ ] T4.4 — Test cases stored in `quests.test_cases` field
- [ ] T5.1–T5.4 — Phi-2 downloaded, `phi2_adapter.py`, fallback wired, "[Offline]" badge in UI
- [ ] T6.1–T6.3 — `behavioral_engine.py` signals + background task + `difficulty_modifier` updated
- [ ] **GATE 8A:** All 8 sandbox security scenarios pass
- [ ] **GATE 8B:** `POST /evaluate` correct code → `{passed:true, pass_rate:1.0, xp_awarded:N}`
- [ ] **GATE 8C:** Groq kill switch → Phi-2 activates → "[Offline]" quests returned
- [ ] **GATE 8D:** Offline complete → "Saved offline" toast → reconnect → XP synced to MongoDB

**Phase 8 STATUS:** ⬜ Not Started | 🟡 In Progress | ✅ Complete

---

### PHASE 9 — ADVANCED GAMIFICATION (Days 26–45 target)

- [ ] T1.1–T1.5 — Boss Battle engine + service + routes + Redis session + event
- [ ] T2.1–T2.4 — 30+ achievement triggers + background check + BadgeDisplay + BadgeEarnedToast
- [ ] T3.1–T3.5 — Supabase materialized view + pg_cron refresh + `GET /leaderboard` + LeaderboardPage
- [ ] T4.1 — Framer Motion installed + dynamic import configured
- [ ] T4.3 — XP Bar spring (0.8s ease-out)
- [ ] T4.4 — Level-Up Ceremony (3.5s, AnimatePresence)
- [ ] T4.5 — Quest Completion Card Flip (0.4s)
- [ ] T4.6 — Streak Extension Pulse (0.6s)
- [ ] T4.7 — Boss Battle Entry Animation (2.0s)
- [ ] T4.8 — Skill Node Unlock Animation (1.5s)
- [ ] T5.1–T5.2 — `GET /analytics/activity` + ActivityHeatmap.tsx (90-day, purple tones)
- [ ] T6.1–T6.3 — Streak shields: earn at 7-day multiples, auto-activate, UI icons
- [ ] **GATE 9A:** Boss battle loop: start → submit → XP awarded + badge in Supabase
- [ ] **GATE 9B:** `GET /leaderboard` → ranked list; refreshes after 15 min
- [ ] **GATE 9C:** Animations at 60fps (DevTools Performance) — no jank
- [ ] **GATE 9D:** Playwright E2E: complete boss → XP + badge — all pass

**Phase 9 STATUS:** ⬜ Not Started | 🟡 In Progress | ✅ Complete

---

### PHASE 10 — AGENTIC ORCHESTRATION (Days 46–70 target)
_Trigger: Phases 6–9 stable 30+ days. A/B plan ready._

- [ ] **PRE-CHECK:** All COGNARC Phases 6–9 stable in production ≥ 30 days (start: _______)
- [ ] **PRE-CHECK:** Single-pipeline Groq success rate > 95% over last 30 days
- [ ] **PRE-CHECK:** A/B quality metric agreed upon + Langfuse project ready
- [ ] T1.1–T1.3 — LangGraph installed; `CognarcAgentState` TypedDict; graph compiled
- [ ] T2.1–T2.3 — `planner_agent.py` (Mixtral-8x7B, 7-day plan, Sunday cron)
- [ ] T3.1–T3.4 — `task_generator_agent.py` (Llama-3-70B, 3 quests, daily 5AM cron)
- [ ] T4.1–T4.3 — `evaluator_agent.py` (Groq, advisory, background task)
- [ ] T5.1–T5.4 — `adaptation_agent.py` (PURE PYTHON, no LLM, async, `difficulty_modifier` update)
- [ ] T6.1–T6.3 — `AgentState` MongoDB field + `agent_state_repository.py` + Railway crons
- [ ] T7.1–T7.4 — Langfuse tracing on all 4 agents + dashboard + alerts
- [ ] T8.1–T8.4 — Feature flag 10% rollout + routing + satisfaction tracking + weekly A/B report
- [ ] T9.1–T9.3 — Personalization engine + onboarding goal + daily XP target on dashboard
- [ ] **GATE 10A:** Planner cron → `users.agent_state.weekly_plan` has 7 entries
- [ ] **GATE 10B:** TaskGenerator cron → `users.agent_state.today_quests` has 3 entries
- [ ] **GATE 10C:** `GET /quests/today` → quests tagged `generated_by:"langgraph"`
- [ ] **GATE 10D:** LangGraph sync path < 30s (measured)
- [ ] **GATE 10E:** Langfuse traces visible for all agent invocations
- [ ] **GATE 10F:** 7-day A/B: multi-agent satisfaction ≥ single-pipeline
- [ ] **GATE 10G:** `pytest tests/ + playwright test` — all green (no regressions)

**Phase 10 STATUS:** ⬜ Not Started | 🟡 In Progress | ✅ Complete

---

### Build Summary Dashboard

| Phase | Description | Target | Status |
|---|---|---|---|
| 01 | Foundation (monorepo, auth, MongoDB) | Days 1–3 | ⬜ Not Started |
| 02 | Data Modeling (schemas, repos, indexes) | Days 3–5 | ⬜ Not Started |
| 03 | MVP AI Pipeline (Groq, prompts, XP) | Days 4–6 | ⬜ Not Started |
| 04 | Frontend UI (Zustand, React Query, Dexie) | Days 7–8 | ⬜ Not Started |
| 05 | MVP Gamification (full XP/streak engine) | Days 8–9 | ⬜ Not Started |
| 06 | MVP Deployment (Railway, Vercel, Day 10 gate) | Day 10 | ⬜ Not Started |
| 07 | Microservices & Go Gateway | Days 11–25 | ⬜ Not Started |
| 08 | Offline & Hybrid Evaluation | Days 11–25 | ⬜ Not Started |
| 09 | Advanced Gamification (Boss, Badges, Animations) | Days 26–45 | ⬜ Not Started |
| 10 | Agentic Orchestration (LangGraph) | Days 46–70 | ⬜ Not Started |

**Total Gates Passed:** 0 / 34
**MVP Gate (Phase 6) Passed:** ❌ No
**Production Live:** ❌ No

> **HOW TO UPDATE:** When a gate passes, change `- [ ]` to `- [x]`, update "Last Updated" + "Current Phase" + "Current Day" + the Summary table status. This gives every future Claude session full build context instantly.
