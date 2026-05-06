# PHASE 02 — DATA MODELING
> **COGNARC Engineering Governance | Phase 2 of 10**
> Agents: `database-architect` · `backend-developer` · `gsd-planner`
> Skills: `senior-architect` · `gepetto` · `backend-dev-guidelines`

---

## Phase Goal

Define and apply all MongoDB collections (`users`, `quests`, `progress_logs`, `streaks`), all Supabase PostgreSQL tables, all indexes, and all Pydantic/ODM models with working CRUD operations through the repository layer — before any AI pipeline is wired.

---

## Architectural Rules Addressed

| Rule (CLAUDE.md) | Constraint |
|---|---|
| §06 Backend Rules | No DB queries in service layer. Only in `repositories/`. |
| §08 Database Rules | MongoDB = primary doc store. Supabase = auth + relational. Redis = cache only. |
| §08 Index Requirements | All required compound and TTL indexes must exist before first query. |
| §08 Data Access Rules | Motor async driver only. Never synchronous pymongo. |
| §17 Code Quality | Pydantic models with `extra="forbid"`. One class per file. |
| §23 Documentation | Schema changes require ADR entry in `docs/decisions/`. |

---

## Task Breakdown (Checklist)

### MongoDB Collections — Schema & Models

- [ ] **T1.1** Create `apps/api/app/models/user.py` — full `User` Pydantic model
  ```python
  class SkillState(BaseModel):
      current_node: str
      node_progress: float = 0.0
      mastered_nodes: list[str] = []
      unlocked_nodes: list[str] = []
      locked_nodes: list[str] = []

  class BehavioralProfile(BaseModel):
      difficulty_modifier: float = 1.0
      preferred_quest_types: list[str] = []
      completion_rate_7d: float = 0.0
      mode: Literal["normal","comeback","boredom","frustration"] = "normal"

  class UserSettings(BaseModel):
      timezone: str = "UTC"
      theme: Literal["dark","light"] = "dark"

  class User(BaseModel):
      model_config = ConfigDict(extra="forbid")
      auth_id: str                    # FK → Supabase auth.users.id
      username: str
      email: str
      created_at: datetime
      level: int = 1
      total_xp: int = 0              # Cumulative, never decreases
      active_skill_tree: str = "AI Engineering"
      skill_state: dict[str, SkillState] = {}
      behavioral_profile: BehavioralProfile = BehavioralProfile()
      settings: UserSettings = UserSettings()
  ```

- [ ] **T1.2** Create `apps/api/app/models/quest.py` — full `Quest` Pydantic model
  ```python
  class EvaluationCriteria(BaseModel):
      type: Literal["code_submission","self_report","theory_qa"]
      test_cases: int = 0
      pass_threshold: float = 0.67

  class Quest(BaseModel):
      model_config = ConfigDict(extra="forbid")
      quest_id: str                   # q_<uuid4_short>
      user_id: str                    # ObjectId as str
      date: datetime
      title: str
      type: Literal["theory","coding","debug","research","build"]
      difficulty: Literal["easy","medium","hard","boss"]
      estimated_minutes: int
      xp_reward: int
      skill_node: str
      skill_tree: str
      evaluation_criteria: EvaluationCriteria
      hints: list[str] = []
      embedding: list[float] = []    # BGE-small 384-dim (Phase 2+)
      status: Literal["pending","completed","skipped","failed"] = "pending"
      generated_by: Literal["groq","phi2","cached"] = "groq"
      created_at: datetime
  ```

- [ ] **T1.3** Create `apps/api/app/models/progress_log.py` — `ProgressLog` model
  - Fields: `user_id`, `quest_id`, `completed_at`, `xp_earned`, `time_taken_min`, `evaluation_score`

- [ ] **T1.4** Create `apps/api/app/models/streak.py` — `Streak` model
  - Fields: `user_id`, `current_streak`, `longest_streak`, `last_completion_date`, `shield_count`

### MongoDB Schemas (Schemas Layer — Request/Response)

- [ ] **T2.1** Create `apps/api/app/schemas/user_schemas.py`
  - `UserCreateRequest`, `UserUpdateRequest`, `UserResponse`, `UserProfileResponse`
- [ ] **T2.2** Create `apps/api/app/schemas/quest_schemas.py`
  - `QuestResponse`, `QuestListResponse`, `QuestStatusUpdateRequest`
- [ ] **T2.3** Create `apps/api/app/schemas/progress_schemas.py`
  - `ProgressLogRequest`, `ProgressLogResponse`
- [ ] **T2.4** Export all types from `packages/shared-types/src/index.ts` (TypeScript mirror of Pydantic schemas)

### MongoDB Indexes

- [ ] **T3.1** Apply all required indexes on `users` collection:
  ```python
  await db.users.create_index("auth_id", unique=True)
  await db.users.create_index("level")
  ```
- [ ] **T3.2** Apply all required indexes on `quests` collection:
  ```python
  await db.quests.create_index([("user_id", 1), ("date", -1)])
  await db.quests.create_index("status")
  await db.quests.create_index("created_at", expireAfterSeconds=2592000)  # TTL 30d embeddings
  ```
- [ ] **T3.3** Apply all required indexes on `progress_logs` collection:
  ```python
  await db.progress_logs.create_index([("user_id", 1), ("completed_at", -1)])
  ```
- [ ] **T3.4** Apply TTL index on `progress_logs` for archive (90d)
- [ ] **T3.5** Write `scripts/apply_indexes.py` — idempotent index application script

### Repository Layer

- [ ] **T4.1** Create `apps/api/app/repositories/mongo/user_repository.py`
  - `create_user(user: User) → User`
  - `get_user_by_auth_id(auth_id: str) → User | None`
  - `get_user_by_id(user_id: str) → User | None`
  - `update_user(user_id: str, updates: dict) → User`
  - `update_skill_state(user_id: str, tree: str, state: SkillState) → None`

- [ ] **T4.2** Create `apps/api/app/repositories/mongo/quest_repository.py`
  - `create_quest(quest: Quest) → Quest`
  - `get_quests_for_user_today(user_id: str, date: date) → list[Quest]`
  - `get_quest_by_id(quest_id: str) → Quest | None`
  - `update_quest_status(quest_id: str, status: str) → None`
  - `get_recent_quests(user_id: str, days: int) → list[Quest]`

- [ ] **T4.3** Create `apps/api/app/repositories/mongo/progress_repository.py`
  - `create_log(log: ProgressLog) → ProgressLog`
  - `get_logs_for_user(user_id: str, limit: int) → list[ProgressLog]`
  - `get_completion_rate_7d(user_id: str) → float`

- [ ] **T4.4** Create `apps/api/app/repositories/mongo/streak_repository.py`
  - `get_streak(user_id: str) → Streak | None`
  - `upsert_streak(user_id: str, streak: Streak) → Streak`

- [ ] **T4.5** Create `apps/api/app/repositories/cache/redis_cache.py`
  - `cache_quests(user_id: str, quests: list[Quest], ttl: int = 86400) → None`
  - `get_cached_quests(user_id: str) → list[Quest] | None`
  - `get_streak_counter(user_id: str) → int`
  - `set_streak_counter(user_id: str, count: int) → None`

### Supabase SQL Migrations

- [ ] **T5.1** Write `infrastructure/supabase/migrations/001_initial_schema.sql`
  ```sql
  -- Leaderboard (materialized view pattern)
  CREATE TABLE IF NOT EXISTS public.leaderboard (
    user_id UUID PRIMARY KEY,
    username TEXT NOT NULL,
    total_xp INTEGER DEFAULT 0,
    current_level INTEGER DEFAULT 1,
    streak INTEGER DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT NOW()
  );

  -- Achievements (insert-only, immutable)
  CREATE TABLE IF NOT EXISTS public.achievements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    badge_id TEXT NOT NULL,
    badge_name TEXT NOT NULL,
    earned_at TIMESTAMPTZ DEFAULT NOW(),
    xp_bonus INTEGER DEFAULT 0
  );

  -- Boss Battles
  CREATE TABLE IF NOT EXISTS public.boss_battles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    week_of DATE NOT NULL,
    status TEXT CHECK (status IN ('in_progress','passed','failed')),
    score NUMERIC(5,2),
    time_taken_min INTEGER,
    xp_awarded INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
  );
  ```

- [ ] **T5.2** Configure Supabase RLS policies on all public tables (users can only read/write their own rows)
- [ ] **T5.3** Validate migration runs on Supabase project without errors

### Data Seeding

- [ ] **T6.1** Create `data/seed/skill_trees.json` — full DAG node definitions for all 4 skill trees
- [ ] **T6.2** Create `data/seed/seed_user.py` — script to seed a test user with skill state in MongoDB
- [ ] **T6.3** Create `data/seed/seed_quests.py` — script to seed sample quests for frontend dev

---

## Data Flow & Dependencies

```
[API Request]
     │
[Router Layer]  api/v1/*.py
     │ Pydantic schema validation (extra="forbid")
     │
[Service Layer] services/*.py
     │ Calls repositories — NEVER accesses DB directly
     │
[Repository Layer]
  ├── mongo/user_repository.py ──▶ [MongoDB Atlas: users]
  ├── mongo/quest_repository.py ──▶ [MongoDB Atlas: quests]
  ├── mongo/progress_repository.py ──▶ [MongoDB Atlas: progress_logs]
  ├── mongo/streak_repository.py ──▶ [MongoDB Atlas: streaks]
  └── cache/redis_cache.py ──▶ [Upstash Redis: quest TTL cache]
                                [Supabase Postgres: leaderboard, achievements, boss_battles]
```

**Dependency Order:**
1. Phase 1 (Foundation) must complete → MongoDB Atlas connection must exist
2. Pydantic models must be defined → before repositories use them
3. Indexes must be applied → before quest generation queries run
4. `packages/shared-types/` TypeScript exports → before frontend consumes any data

---

## Testing & Observability

### Required Tests

| Test | Tool | File | Target |
|---|---|---|---|
| `create_user()` inserts and returns | pytest | `tests/integration/test_user_repo.py` | 100% |
| `get_user_by_auth_id()` returns correct doc | pytest | `tests/integration/test_user_repo.py` | 100% |
| Quest compound index `{user_id, date}` used | pytest | `tests/integration/test_quest_repo.py` | 100% |
| `get_completion_rate_7d()` correct aggregation | pytest | `tests/unit/test_progress_repo.py` | 100% |
| Redis cache set/get round-trip | pytest | `tests/unit/test_redis_cache.py` | 100% |
| Pydantic `User` rejects extra fields | pytest | `tests/unit/test_models.py` | 100% |
| Supabase SQL migration is reversible | SQL | manual in dev Supabase project | one-time |

### Observability

- [ ] Log all repository calls (collection, operation, duration_ms)
- [ ] Log MongoDB query plans for slow queries (> 100ms) to structured logger
- [ ] Track `progress_logs` TTL expiry in monitoring

### Metrics

| Metric | Target |
|---|---|
| MongoDB write latency (p95) | < 50ms |
| MongoDB read latency (p95) | < 30ms |
| Redis cache hit rate (quests) | > 95% after first generation |

---

## Validation Gate

**Phase 2 is DONE when ALL pass:**

```bash
# 1. All indexes exist in Atlas
# Atlas UI → cognarc DB → each collection → Indexes tab → verify all compound indexes

# 2. Repository tests pass
cd apps/api && pytest tests/integration/ tests/unit/ -v -k "repo or model or cache"
# All green

# 3. Seeding works
python data/seed/seed_user.py   # → user inserted
python data/seed/seed_quests.py # → 3 quests inserted

# 4. End-to-end read
curl -H "Authorization: Bearer <jwt>" localhost:8000/users/me
# → Full user document with skill_state and behavioral_profile

# 5. Supabase migration
# Supabase Studio → SQL Editor → run 001_initial_schema.sql → no errors
# Supabase Studio → leaderboard, achievements, boss_battles tables exist
```

---

## Absolute 'Do-Not-Do' List for Phase 2

| Forbidden | Reason |
|---|---|
| ❌ DB queries in `services/*.py` | Layer violation §06 — only repos touch the DB |
| ❌ Synchronous `pymongo` calls | Must use Motor async driver §08 |
| ❌ Store auth tokens in MongoDB | Supabase manages auth — never duplicate §08 |
| ❌ Add `embedding` field to quests now | BGE-small is Phase 2 (COGNARC Phase 2). Scaffold the field, leave empty. |
| ❌ Modify `auth.users` Supabase table | Supabase manages this. Forbidden in §08. |
| ❌ UPDATE or DELETE `achievements` rows | Insert-only table §08 |
| ❌ Let Redis diverge from MongoDB on XP/streak | Redis is cache-only §08 |
| ❌ Duplicate type definitions outside `packages/shared-types/` | Type drift §17 |
| ❌ Create schemas in `services/` layer | Schemas only in `app/schemas/` and `packages/shared-types/` |

---

*Phase 2 Target: Days 3–5 (within MVP window)*
*Owner: `database-architect` (schema design) · `backend-developer` (implementation)*
*Next: [PHASE_03_MVP_AI_PIPELINE.md](./PHASE_03_MVP_AI_PIPELINE.md)*
