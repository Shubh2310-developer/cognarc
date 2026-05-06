# PHASE 07 — MICROSERVICES & GO API GATEWAY
> **COGNARC Engineering Governance | Phase 7 of 10**
> Agents: `backend-architect` · `backend-developer` · `gsd-planner` · `gsd-integration-checker`
> Skills: `senior-architect` · `gepetto` · `cc-skill-backend-patterns` · `subagent-driven-development`

---

## Phase Goal

Extract a Go/Gin API Gateway that handles JWT auth, rate limiting, and routing — then gradually split the FastAPI monolith into separate Quest, User, and Gamification services on Railway, each with its own Dockerfile, environment config, and health check, while the system remains fully operational throughout.

---

## Architectural Rules Addressed

| Rule (CLAUDE.md) | Constraint |
|---|---|
| §03 Phase 2 Target Architecture | Go/Gin API Gateway as the entry point for all traffic in Phase 2+. |
| §15 Migration Rules | Trigger conditions: MVP 14+ days production, service showing >80% CPU/RAM, or >1 developer. |
| §15 Migration Order | Go Gateway first → Quest Service → User Service → Gamification → ai-services last. |
| §15 Migration Rules | Each service gets own Dockerfile, Railway service, env config. Deploy ONE at a time. |
| §15 Migration Rules | Services communicate only via HTTP/gRPC. Never shared DB access across service boundaries. |
| §06 Backend Layers | Router/Service/Engine/Repository/Adapter boundaries remain identical within each new service. |

---

## Trigger Conditions (Must Be Met Before Starting)

> ⚠️ **Do NOT start Phase 7 until ALL conditions are true:**

- [ ] MVP has been running in production for at least **14 days** without critical failures
- [ ] GitHub Actions CI is green on `main` for 7+ consecutive days
- [ ] At least one service shows > 50% sustained CPU or approaching 400MB memory on Railway
- [ ] Day 10 MVP gate has been fully validated and documented

---

## Task Breakdown (Checklist)

### Step 1: Go API Gateway

- [ ] **T1.1** Create `apps/gateway/` directory:
  ```
  apps/gateway/
  ├── main.go
  ├── middleware/
  │   ├── auth.go          # JWT validation (Supabase secret)
  │   ├── ratelimit.go     # Redis-backed rate limiter
  │   └── cors.go          # CORS configuration
  ├── routes/
  │   └── router.go        # Route registration + upstream proxy map
  ├── config/
  │   └── config.go        # Env var loading
  ├── go.mod
  └── Dockerfile
  ```

- [ ] **T1.2** Implement `apps/gateway/middleware/auth.go`:
  ```go
  package middleware

  import (
    "github.com/gin-gonic/gin"
    "github.com/golang-jwt/jwt/v5"
    "net/http"
    "strings"
  )

  func JWTAuthMiddleware(jwtSecret string) gin.HandlerFunc {
    return func(c *gin.Context) {
      authHeader := c.GetHeader("Authorization")
      if !strings.HasPrefix(authHeader, "Bearer ") {
        c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "missing token"})
        return
      }
      tokenStr := strings.TrimPrefix(authHeader, "Bearer ")
      token, err := jwt.Parse(tokenStr, func(t *jwt.Token) (interface{}, error) {
        return []byte(jwtSecret), nil
      })
      if err != nil || !token.Valid {
        c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "invalid token"})
        return
      }
      claims := token.Claims.(jwt.MapClaims)
      c.Set("user_id", claims["sub"])
      c.Next()
    }
  }
  ```

- [ ] **T1.3** Implement `apps/gateway/middleware/ratelimit.go` — Redis-backed sliding window:
  - `quest_generation`: 5/day/user → key `rl:quest_gen:{user_id}:{date}`
  - `evaluation`: 10/day/user → key `rl:evaluate:{user_id}:{date}`
  - `general`: 100/min/user → key `rl:general:{user_id}:{minute}`

- [ ] **T1.4** Implement `apps/gateway/routes/router.go` — reverse proxy to downstream services:
  ```go
  func SetupRouter(cfg *Config) *gin.Engine {
    r := gin.New()
    r.Use(middleware.Logger(), middleware.CORS(cfg.AllowedOrigins))

    v1 := r.Group("/api/v1")
    v1.Use(middleware.JWTAuthMiddleware(cfg.JWTSecret))
    v1.Use(middleware.RateLimiter(cfg.Redis))

    // Route to downstream services
    v1.Any("/quests/*path",        ReverseProxy(cfg.QuestServiceURL))
    v1.Any("/progress/*path",      ReverseProxy(cfg.QuestServiceURL))  // MVP: same service
    v1.Any("/gamification/*path",  ReverseProxy(cfg.GamificationServiceURL))
    v1.Any("/users/*path",         ReverseProxy(cfg.UserServiceURL))
    v1.Any("/ai/*path",            ReverseProxy(cfg.QuestServiceURL))

    r.GET("/health", healthHandler)
    return r
  }
  ```

- [ ] **T1.5** Write `apps/gateway/Dockerfile`:
  ```dockerfile
  FROM golang:1.21-alpine AS builder
  WORKDIR /app
  COPY go.mod go.sum ./
  RUN go mod download
  COPY . .
  RUN go build -o gateway ./main.go

  FROM alpine:latest
  WORKDIR /app
  COPY --from=builder /app/gateway .
  EXPOSE 8000
  CMD ["./gateway"]
  ```

- [ ] **T1.6** Deploy `apps/gateway/` as new Railway service `cognarc-gateway`
- [ ] **T1.7** Update `NEXT_PUBLIC_API_URL` in Vercel to point to gateway URL
- [ ] **T1.8** Keep FastAPI monolith running; gateway proxies to it initially (transparent migration)
- [ ] **T1.9** **GATE:** `curl -H "Authorization: Bearer <jwt>" https://<gateway-url>/api/v1/quests/today` → same result as direct FastAPI call

### Step 2: Extract Quest Service

- [ ] **T2.1** Create `apps/quest-service/` as standalone FastAPI application
  - Copy only quest-related routes, services, repositories from `apps/api/`
  - Routes: `/quests/*`, `/progress/*`, `/ai/*`
  - Own `requirements.txt`, own `Dockerfile`, own `.env` template
  - Remove all gamification, user, auth route logic

- [ ] **T2.2** Update Gateway route map: `QuestServiceURL` → new Quest Service Railway URL
- [ ] **T2.3** Validate: quest generation still works end-to-end through gateway → quest service
- [ ] **T2.4** Monitor for 48h before next extraction

### Step 3: Extract User Service (Go/Fiber)

- [ ] **T3.1** Create `apps/user-service/` in Go using Fiber framework
  - Routes: `GET /users/me`, `PATCH /users/me`, `GET /users/{id}/profile`, `POST /auth/login`
  - Communicates directly with MongoDB Atlas
  - Uses same JWT validation logic as gateway

- [ ] **T3.2** Update Gateway route map: `UserServiceURL` → new User Service Railway URL
- [ ] **T3.3** Remove user routes from FastAPI monolith
- [ ] **T3.4** Validate: user profile reads correctly through gateway → user service

### Step 4: Extract Gamification Service

- [ ] **T4.1** Create `apps/gamification-service/` as standalone FastAPI application
  - Routes: `/gamification/*`
  - Engines: `gamification_engine.py`, `streak_engine.py`
  - Own Redis connection, own MongoDB connection

- [ ] **T4.2** Update Gateway route map
- [ ] **T4.3** Remove gamification routes from FastAPI monolith

### Inter-Service Communication Contracts

- [ ] **T5.1** Document all service contracts in `docs/api/SERVICE_CONTRACTS.md`
- [ ] **T5.2** Create `packages/shared-types/` additions for inter-service request/response schemas
- [ ] **T5.3** Implement `gsd-integration-checker` validation: verify all gateway → service routes return expected schemas
- [ ] **T5.4** Add circuit breaker to gateway: if a service is down, return 503 with `{"error": "service_unavailable", "service": "quest"}`

### Service Configuration Matrix

| Service | Port | Railway Service Name | Owns Collections |
|---|---|---|---|
| `cognarc-gateway` (Go/Gin) | 8000 | `cognarc-gateway` | None (stateless) |
| `cognarc-quest` (FastAPI) | 8001 | `cognarc-quest` | `quests`, `progress_logs` |
| `cognarc-user` (Go/Fiber) | 8003 | `cognarc-user` | `users` |
| `cognarc-gamification` (FastAPI) | 8004 | `cognarc-gamification` | `streaks` |

### BGE-small Deduplication (Phase 2 AI Feature)

- [ ] **T6.1** Add `bge-small-en-v1.5` model download to `ai-services/embeddings/`
- [ ] **T6.2** Implement `ai-services/embeddings/bge_embedder.py`:
  ```python
  from sentence_transformers import SentenceTransformer
  import numpy as np

  class BGEEmbedder:
      def __init__(self):
          self.model = SentenceTransformer("BAAI/bge-small-en-v1.5")

      def embed(self, text: str) -> list[float]:
          return self.model.encode(text, normalize_embeddings=True).tolist()

      def cosine_similarity(self, a: list[float], b: list[float]) -> float:
          return float(np.dot(a, b))  # normalized vectors → dot = cosine
  ```

- [ ] **T6.3** Add deduplication check in Quest Service before calling Groq:
  - Fetch embeddings of last 7 days of quests for user
  - If `cosine_similarity(new_quest_embedding, existing) > 0.85` → regenerate (max 1 retry)
- [ ] **T6.4** Store `embedding` field in `quests` collection (384-dim vector)

---

## Data Flow & Dependencies

```
[Browser / Mobile]
       │ HTTPS
       ▼
[Go/Gin API Gateway :8000]
  ├── middleware/auth.go     (JWT decode)
  ├── middleware/ratelimit.go (Redis sliding window)
  └── routes/router.go       (reverse proxy)
       │
  ┌────┼────────────────────┐
  ▼    ▼                    ▼
[Quest Service  [User Service   [Gamification Service
  FastAPI :8001]  Go/Fiber :8003]  FastAPI :8004]
       │              │                  │
  [MongoDB: quests]  [MongoDB: users]  [MongoDB: streaks]
  [Upstash Redis]                      [Upstash Redis]
       │
  [ai-services/ — BGE + Groq]
```

**Dependency Order:**
1. Phase 6 MVP deployment must be stable 14+ days
2. Go/Gin gateway deployed first → routes to existing FastAPI monolith (zero user impact)
3. Each service extracted one at a time; gateway route map updated atomically
4. BGE deduplication added to Quest Service after gateway stabilizes

---

## Testing & Observability

### Required Tests

| Test | Tool | File | Target |
|---|---|---|---|
| Gateway JWT middleware rejects invalid token | Go test | `apps/gateway/middleware/auth_test.go` | 100% |
| Gateway rate limiter enforces 5/day | Go test | `apps/gateway/middleware/ratelimit_test.go` | 100% |
| Gateway proxies correctly to Quest Service | Go test (mock) | `apps/gateway/routes/router_test.go` | 100% |
| BGE cosine_similarity correct | pytest | `ai-services/tests/test_bge_embedder.py` | 100% |
| Dedup rejects similar quest (similarity > 0.85) | pytest | `tests/integration/test_quest_dedup.py` | 100% |
| All service health endpoints return 200 | CI smoke test | `.github/workflows/smoke.yml` | 100% |

### Integration Validation

- [ ] Run `gsd-integration-checker` agent against all service contracts after each extraction
- [ ] Measure gateway latency overhead (should be < 5ms added latency)
- [ ] Monitor Railway memory per service post-extraction (each should use less than monolith)

### Observability

- [ ] Gateway: log every proxied request with `target_service`, `upstream_latency_ms`, `status_code`
- [ ] Distributed trace: propagate `X-Request-ID` header through gateway → all services
- [ ] Alert: if any service health check fails for > 60s → Slack notification

---

## Validation Gate

**Phase 7 is DONE when ALL pass:**

```bash
# 1. Gateway health
curl https://<gateway-url>/health  # 200

# 2. Auth through gateway
curl -H "Authorization: Bearer <jwt>" https://<gateway-url>/api/v1/quests/today
# Same response as direct FastAPI call

# 3. Rate limit enforcement
for i in $(seq 1 6); do
  curl -X POST -H "Authorization: Bearer <jwt>" https://<gateway-url>/api/v1/quests/generate
done
# First 5: 200. Sixth: 429 {"error": "rate_limit_exceeded"}

# 4. Service health checks
curl https://cognarc-quest.railway.app/health    # 200
curl https://cognarc-user.railway.app/health     # 200
curl https://cognarc-gamification.railway.app/health  # 200

# 5. BGE deduplication
# Generate quests → check quests collection has embedding field
# Re-generate → verify no duplicate quest titles in 7-day window

# 6. Go tests
cd apps/gateway && go test ./... -v  # All pass

# 7. E2E still passes
cd apps/web && npx playwright test  # No regressions
```

---

## Absolute 'Do-Not-Do' List for Phase 7

| Forbidden | Reason |
|---|---|
| ❌ Start Phase 7 before 14 days of stable MVP | §15 migration trigger conditions |
| ❌ Extract all services simultaneously | Deploy ONE at a time and validate §15 |
| ❌ Shared DB access across service boundaries | Services own their collections §15 |
| ❌ Business logic in the Go Gateway | Gateway = routing + auth + rate limit ONLY §15 |
| ❌ Extract `ai-services/` before other services | ai-services is the last and most complex §15 |
| ❌ Add LangGraph or agent state | Phase 4 (COGNARC Phase 10) |
| ❌ Add boss battles or leaderboard | Phase 3 (COGNARC Phases 8–9) |
| ❌ Use `exec()` or `eval()` in Go services | Security rules still apply |
| ❌ Let gateway hold session state | Gateway is stateless; state in services/DB |
| ❌ Skip integration tests between service extractions | Data contract validation is mandatory §15 |

---

*Phase 7 Target: Days 11–25 (COGNARC Phase 2)*
*Owner: `backend-architect` (design) · `backend-developer` (Go gateway + service extraction)*
*Next: [PHASE_08_OFFLINE_AND_EVALUATION.md](./PHASE_08_OFFLINE_AND_EVALUATION.md)*
