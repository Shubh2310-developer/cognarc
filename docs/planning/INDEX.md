# COGNARC — Master Planning Index
> **Version:** 2.0 — Execution Edition
> **Agents:** `gsd-roadmapper` · `gsd-planner` | **Skills:** `gepetto` · `senior-architect`
> **Last Updated:** 2026-05-06

---

## Build Sequence Overview

```
MVP (Days 1–10)          Phase 2 (Days 11–25)    Phase 3 (Days 26–45)    Phase 4 (Days 46–70)
─────────────────────    ──────────────────────   ─────────────────────   ──────────────────────
PHASE_01_FOUNDATION      PHASE_07_MICROSERVICES   PHASE_09_ADVANCED_      PHASE_10_AGENTIC_
PHASE_02_DATA_MODELING   PHASE_08_OFFLINE_AND_     GAMIFICATION            ORCHESTRATION
PHASE_03_MVP_AI_PIPELINE  EVALUATION
PHASE_04_FRONTEND_UI
PHASE_05_MVP_GAMIFICATION
PHASE_06_MVP_DEPLOYMENT
```

---

## Phase Files

| # | File | Goal | Target Days | Gate |
|---|---|---|---|---|
| 01 | [PHASE_01_FOUNDATION.md](./PHASE_01_FOUNDATION.md) | Monorepo, Docker, Next.js, FastAPI, Auth | Days 1–3 | All services green, JWT auth working |
| 02 | [PHASE_02_DATA_MODELING.md](./PHASE_02_DATA_MODELING.md) | MongoDB schemas, indexes, repositories | Days 3–5 | All CRUD operations tested |
| 03 | [PHASE_03_MVP_AI_PIPELINE.md](./PHASE_03_MVP_AI_PIPELINE.md) | Groq adapter, prompt template, quest generation | Days 4–6 | 3 valid quests from real user context |
| 04 | [PHASE_04_FRONTEND_UI.md](./PHASE_04_FRONTEND_UI.md) | Zustand, feature-first structure, App Router | Days 7–8 | Quest display + XP update without reload |
| 05 | [PHASE_05_MVP_GAMIFICATION.md](./PHASE_05_MVP_GAMIFICATION.md) | XP formula, level engine, Redis streaks | Days 8–9 | Quest → XP → streak fully wired |
| 06 | [PHASE_06_MVP_DEPLOYMENT.md](./PHASE_06_MVP_DEPLOYMENT.md) | Railway, Vercel, Day 10 E2E gates | Day 10 | Full loop on production URL < 5 min |
| 07 | [PHASE_07_MICROSERVICES.md](./PHASE_07_MICROSERVICES.md) | Go API Gateway, service splitting, BGE dedup | Days 11–25 | All services independent on Railway |
| 08 | [PHASE_08_OFFLINE_AND_EVALUATION.md](./PHASE_08_OFFLINE_AND_EVALUATION.md) | next-pwa, Dexie sync, sandboxed eval, Phi-2 | Days 11–25 | Offline quest + code evaluation working |
| 09 | [PHASE_09_ADVANCED_GAMIFICATION.md](./PHASE_09_ADVANCED_GAMIFICATION.md) | Boss Battles, Supabase Leaderboard, Framer Motion | Days 26–45 | Boss battle + badges + animations live |
| 10 | [PHASE_10_AGENTIC_ORCHESTRATION.md](./PHASE_10_AGENTIC_ORCHESTRATION.md) | LangGraph Planner→Generator→Evaluator→Adaptation | Days 46–70 | Multi-agent quest generation in production |

---

## Critical Rules (Never Violate)

1. **Never build Phase 2+ before Day 10 MVP gate passes** — §13, §14
2. **AI logic belongs exclusively in `ai-services/`** — §07
3. **Never use `exec()` or `eval()` on user code** — §16
4. **DB queries only in `repositories/` layer** — §06
5. **Never let Redis diverge from MongoDB on XP/streak** — §08
6. **LangGraph is Phase 4 ONLY** — §07 phase gate
7. **One service at a time during microservice extraction** — §15

---

*COGNARC v2.0 Execution Edition — 70-Day Build Plan*
*© Principal Engineering | `senior-architect` + `senior-fullstack` reviewed*
