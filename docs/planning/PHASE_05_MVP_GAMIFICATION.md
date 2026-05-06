# PHASE 05 — MVP GAMIFICATION
> **COGNARC Engineering Governance | Phase 5 of 10**
> Agents: `backend-developer` · `frontend-developer` · `gsd-planner` · `gsd-verifier`
> Skills: `senior-architect` · `gepetto` · `backend-dev-guidelines` · `cc-skill-backend-patterns`

---

## Phase Goal

Implement the complete XP formula (with all multipliers), the level progression engine, and Redis-backed streak counters — fully wired end-to-end so that completing a quest correctly awards XP, updates the user's level, increments their streak, and reflects all changes in the frontend dashboard without a page reload.

---

## Architectural Rules Addressed

| Rule (CLAUDE.md) | Constraint |
|---|---|
| §06 Engine Layer | `gamification_engine.py` is pure functions — no I/O, no DB calls, no AI calls. |
| §06 Service Layer | `gamification_service.py` orchestrates: calls engines + repositories only. |
| §08 Redis Rules | Redis is cache-only. MongoDB is source of truth. Streak in Redis is synced to MongoDB. |
| §09 Event System | XP calculation and streak increment are synchronous in-request. Other events are background. |
| §16 AI Safety | AI NEVER awards XP directly. XP comes from deterministic `gamification_engine.calculate_xp()`. |
| §21 Performance | XP formula and level computation are pure Python — sub-millisecond. |

---

## Task Breakdown (Checklist)

### Gamification Engine (Pure Functions)

- [ ] **T1.1** Implement `apps/api/app/engines/gamification_engine.py` — complete XP formula:
  ```python
  from math import floor

  BASE_XP: dict[str, int] = {"easy": 50, "medium": 100, "hard": 200, "boss": 500}
  STREAK_MULTIPLIER_MAP = [
      (range(1, 7),  1.00),
      (range(7, 14), 1.25),
      (range(14, 30), 1.50),
      (range(30, 9999), 2.00),
  ]
  TYPE_MULTIPLIER: dict[str, float] = {
      "theory": 0.8, "coding": 1.0, "debug": 1.1, "build": 1.3
  }

  def get_streak_multiplier(streak_count: int) -> float:
      for rng, mult in STREAK_MULTIPLIER_MAP:
          if streak_count in rng:
              return mult
      return 1.0

  def calculate_xp(
      difficulty: str,
      streak_count: int,
      actual_time_min: float,
      estimated_time_min: float,
      quest_type: str,
      difficulty_modifier: float,
  ) -> int:
      base = BASE_XP[difficulty]
      streak_mult = get_streak_multiplier(streak_count)
      type_mult = TYPE_MULTIPLIER[quest_type]
      time_bonus = 1.2 if actual_time_min < 0.8 * estimated_time_min else 1.0
      return int(base * difficulty_modifier * streak_mult * time_bonus * type_mult)
  ```

- [ ] **T1.2** Implement `apps/api/app/engines/gamification_engine.py` — Level progression:
  ```python
  def xp_for_level(n: int) -> int:
      return int(100 * (n ** 1.8))

  def calculate_level(total_xp: int) -> int:
      return max(1, floor((total_xp / 100) ** (1 / 1.8)))

  def calculate_xp_progress_pct(total_xp: int) -> float:
      level = calculate_level(total_xp)
      current_threshold = xp_for_level(level)
      next_threshold = xp_for_level(level + 1)
      return (total_xp - current_threshold) / (next_threshold - current_threshold)
  ```

- [ ] **T1.3** Implement level tier lookup:
  ```python
  LEVEL_TIERS = [
      (range(1, 6),   "Apprentice"),
      (range(6, 16),  "Practitioner"),
      (range(16, 31), "Engineer"),
      (range(31, 51), "Architect"),
      (range(51, 76), "Grandmaster"),
      (range(76, 101), "Legend"),
  ]

  def get_level_tier(level: int) -> str:
      for rng, tier in LEVEL_TIERS:
          if level in rng:
              return tier
      return "Legend"
  ```

### Streak Engine

- [ ] **T2.1** Implement `apps/api/app/engines/streak_engine.py`
  ```python
  from datetime import date, timedelta

  def should_increment_streak(last_completion_date: date | None, today: date) -> bool:
      if last_completion_date is None:
          return True  # First ever completion
      delta = today - last_completion_date
      return delta.days == 1  # Completed yesterday

  def should_reset_streak(last_completion_date: date | None, today: date) -> bool:
      if last_completion_date is None:
          return False
      delta = today - last_completion_date
      return delta.days > 1  # Missed at least one day

  def apply_shield(streak: Streak) -> tuple[Streak, bool]:
      """Auto-activate shield if available on first missed day."""
      if streak.shield_count > 0:
          return Streak(
              **streak.dict(),
              shield_count=streak.shield_count - 1,
              last_completion_date=streak.last_completion_date
          ), True  # Shield consumed
      return streak, False
  ```

- [ ] **T2.2** Implement Redis-backed streak counters in `apps/api/app/repositories/cache/redis_cache.py`:
  ```python
  async def get_streak_counter(user_id: str) -> int:
      val = await redis.get(f"streak:{user_id}")
      return int(val) if val else 0

  async def set_streak_counter(user_id: str, count: int) -> None:
      await redis.set(f"streak:{user_id}", count, ex=86400 * 2)  # 2-day TTL

  async def get_last_completion_date(user_id: str) -> str | None:
      return await redis.get(f"streak_date:{user_id}")

  async def set_last_completion_date(user_id: str, date_str: str) -> None:
      await redis.set(f"streak_date:{user_id}", date_str, ex=86400 * 2)
  ```

- [ ] **T2.3** Create `apps/api/app/repositories/mongo/streak_repository.py` (source of truth):
  - `get_streak(user_id) → Streak`
  - `upsert_streak(user_id, streak) → Streak`
  - MongoDB `streaks` collection is AUTHORITATIVE; Redis is cache

### Gamification Service

- [ ] **T3.1** Implement `apps/api/app/services/gamification_service.py`
  ```python
  async def award_quest_xp(user_id: str, quest: Quest, time_taken_min: float, db) -> XpAwardResult:
      # 1. Get current user state
      user = await user_repository.get_user_by_id(user_id, db)
      streak_count = await redis_cache.get_streak_counter(user_id)

      # 2. Calculate XP (pure engine — no I/O)
      xp = calculate_xp(
          difficulty=quest.difficulty,
          streak_count=streak_count,
          actual_time_min=time_taken_min,
          estimated_time_min=quest.estimated_minutes,
          quest_type=quest.type,
          difficulty_modifier=user.behavioral_profile.difficulty_modifier,
      )

      # 3. Update total_xp in MongoDB
      new_total_xp = user.total_xp + xp
      new_level = calculate_level(new_total_xp)
      level_up = new_level > user.level

      await user_repository.update_user(user_id, {
          "total_xp": new_total_xp,
          "level": new_level
      }, db)

      return XpAwardResult(
          xp_awarded=xp,
          new_total_xp=new_total_xp,
          new_level=new_level,
          level_up=level_up,
          progress_pct=calculate_xp_progress_pct(new_total_xp)
      )

  async def update_streak(user_id: str, db) -> StreakUpdateResult:
      today = date.today()
      streak_doc = await streak_repository.get_streak(user_id, db)
      last_date_str = await redis_cache.get_last_completion_date(user_id)
      last_date = date.fromisoformat(last_date_str) if last_date_str else None

      if should_reset_streak(last_date, today):
          new_streak = 0
      elif should_increment_streak(last_date, today):
          new_streak = (streak_doc.current_streak if streak_doc else 0) + 1
      else:
          new_streak = streak_doc.current_streak if streak_doc else 0  # Same day

      longest = max(new_streak, streak_doc.longest_streak if streak_doc else 0)

      await redis_cache.set_streak_counter(user_id, new_streak)
      await redis_cache.set_last_completion_date(user_id, today.isoformat())
      await streak_repository.upsert_streak(user_id, Streak(
          user_id=user_id,
          current_streak=new_streak,
          longest_streak=longest,
          last_completion_date=today,
          shield_count=streak_doc.shield_count if streak_doc else 0
      ), db)

      return StreakUpdateResult(new_streak=new_streak, longest=longest)
  ```

- [ ] **T3.2** Wire `gamification_service.award_quest_xp()` and `update_streak()` into `POST /quests/{id}/evaluate`
- [ ] **T3.3** Implement `GET /gamification/dashboard` — returns `{total_xp, level, progress_pct, streak, tier_name, multiplier}`
- [ ] **T3.4** Implement `GET /gamification/xp` — returns XP history for bar chart (last 7 days)
- [ ] **T3.5** Implement `POST /gamification/level-check` — returns `{leveled_up: bool, new_level: int}` (called by frontend post-XP-award)

### Events System (MVP)

- [ ] **T4.1** Define event dataclasses in `apps/api/app/events/`:
  ```python
  # quest_events.py
  @dataclass
  class QuestCompletedEvent:
      user_id: str
      quest_id: str
      xp_awarded: int
      new_total_xp: int
      new_level: int
      streak_count: int
      level_up: bool

  @dataclass
  class StreakBrokenEvent:
      user_id: str
      previous_streak: int
      shield_consumed: bool
  ```

- [ ] **T4.2** Wire background tasks on `QuestCompletedEvent`:
  - Synchronous (in-request): XP award, streak increment
  - Background (`BackgroundTasks`): analytics log, leaderboard update (stub — active Phase 3)

### Frontend Gamification Integration

- [ ] **T5.1** Update `useGamificationStore.ts` — `awardXp()` action:
  ```typescript
  awardXp: (xp: number) => set((state) => {
    const newTotalXp = state.totalXp + xp
    const newLevel = Math.floor((newTotalXp / 100) ** (1 / 1.8))
    const levelUp = newLevel > state.level
    return {
      totalXp: newTotalXp,
      level: newLevel,
      levelUp,
      progressPct: computeProgressPct(newTotalXp, newLevel)
    }
  })
  ```

- [ ] **T5.2** Update `QuestCard.tsx` — on "Mark Complete":
  1. Call `completeQuest(questId)` via `features/quests/api/`
  2. On success: call `useGamificationStore.awardXp(xp_awarded)`
  3. Show success toast: "+{xp} XP" (ShadCN `Toast`)
  4. Mark card as completed (disable button, green checkmark state)

- [ ] **T5.3** Update `XpBar.tsx` — reads `progressPct` from Zustand, re-renders on XP change
- [ ] **T5.4** Update `StreakDisplay.tsx` — reads `streak` from Zustand, shows multiplier badge for streaks ≥ 7

---

## Data Flow & Dependencies

```
POST /quests/{id}/evaluate
       │ (synchronous, in-request)
       ├── quest_repository.get_quest_by_id()     → Quest doc
       ├── gamification_service.award_quest_xp()
       │       ├── user_repository.get_user_by_id()
       │       ├── redis_cache.get_streak_counter()
       │       ├── gamification_engine.calculate_xp()  ← PURE FUNCTION
       │       └── user_repository.update_user()       → MongoDB
       ├── gamification_service.update_streak()
       │       ├── redis_cache.get_last_completion_date()
       │       ├── streak_engine.should_increment_streak()  ← PURE FUNCTION
       │       ├── redis_cache.set_streak_counter()    → Redis (cache)
       │       └── streak_repository.upsert_streak()   → MongoDB (source of truth)
       ├── progress_repository.create_log()            → MongoDB
       └── BackgroundTasks: analytics log (async)
       │
HTTP 200 → XpAwardResult {xp_awarded, new_level, progress_pct, streak}
       │
[Frontend]
  useGamificationStore.awardXp(xp_awarded)
  → XP bar animates (CSS transition)
  → Level badge updates if level_up
  → Streak display updates
```

---

## Testing & Observability

### Required Tests

| Test | Tool | File | Target |
|---|---|---|---|
| `calculate_xp()` all difficulty × streak × type combos | pytest | `tests/unit/test_gamification_engine.py` | 100% |
| `calculate_level()` correct for known XP values | pytest | `tests/unit/test_gamification_engine.py` | 100% |
| `should_increment_streak()` edge cases | pytest | `tests/unit/test_streak_engine.py` | 100% |
| `should_reset_streak()` missed day | pytest | `tests/unit/test_streak_engine.py` | 100% |
| Streak shield auto-activates on miss | pytest | `tests/unit/test_streak_engine.py` | 100% |
| XP + streak update via `/evaluate` route | pytest + TestClient | `tests/integration/test_gamification.py` | 100% |
| Redis streak counter persists between calls | pytest | `tests/integration/test_streak_redis.py` | 100% |
| Frontend `awardXp()` updates Zustand level | Vitest | `stores/tests/gamification.test.ts` | 100% |

### Observability

- [ ] Log every XP award: `user_id`, `quest_id`, `xp_awarded`, `new_total_xp`, `new_level`, `level_up` (boolean)
- [ ] Log every streak update: `user_id`, `previous_streak`, `new_streak`, `shield_consumed`
- [ ] Alert (Slack/Sentry) if streak sync conflict detected (Redis vs MongoDB mismatch)

### Metrics

| Metric | Target |
|---|---|
| XP calculation latency | < 1ms (pure function) |
| Streak update latency (Redis) | < 10ms |
| Streak update latency (MongoDB) | < 50ms |
| XP formula accuracy | 100% (verified by unit tests vs manual calc) |

---

## Validation Gate

**Phase 5 is DONE when ALL pass:**

```bash
# 1. Formula verification
python -c "
from apps.api.app.engines.gamification_engine import calculate_xp, calculate_level
# Medium coding, 8-day streak, on time, modifier 1.0
xp = calculate_xp('medium', 8, 20, 25, 'coding', 1.0)
assert xp == int(100 * 1.0 * 1.25 * 1.0 * 1.0), f'Got {xp}'

# Level from XP
assert calculate_level(0) == 1
assert calculate_level(100) == 1
print('Formula verification: PASS')
"

# 2. End-to-end quest completion
curl -X POST localhost:8000/quests/{questId}/evaluate \
  -H "Authorization: Bearer <jwt>" \
  -d '{"self_report": true, "time_taken_min": 20}'
# → {"xp_awarded": 125, "new_level": 3, "progress_pct": 0.45, "streak": 8}

# 3. Streak persistence
# Day 1: complete quest → streak = 1 (Redis + MongoDB)
# Day 2: complete quest → streak = 2
# Wait until next day without completing → streak = 0

# 4. Unit tests
cd apps/api && pytest tests/unit/ -k "gamification or streak" -v
# All green

# 5. Frontend check
# Dashboard: mark quest complete → XP bar width changes → streak count increments
# No page reload required
```

---

## Absolute 'Do-Not-Do' List for Phase 5

| Forbidden | Reason |
|---|---|
| ❌ AI awarding XP directly | XP must come from deterministic engine only §16 |
| ❌ DB calls in gamification engine | Engine is pure functions — no I/O §06 |
| ❌ Streak logic in repository layer | Streak logic belongs in `streak_engine.py` §06 |
| ❌ Let Redis be source of truth for streak | MongoDB is authoritative; Redis is cache §08 |
| ❌ Add badge system | Phase 3 (COGNARC Phase 3) |
| ❌ Add streak shields UI | Phase 3 (COGNARC Phase 3) |
| ❌ Add boss battle XP logic | Phase 3 (COGNARC Phase 3) |
| ❌ Framer Motion level-up animation | Phase 3 — use toast only §14 |
| ❌ Leaderboard XP ranking | Phase 3 (Supabase materialized view) |
| ❌ XP multiplier for boss battles | Phase 3 (boss battles not built yet) |

---

*Phase 5 Target: Days 8–9 (within MVP window)*
*Owner: `backend-developer` (engine + service) · `frontend-developer` (store integration)*
*Next: [PHASE_06_MVP_DEPLOYMENT.md](./PHASE_06_MVP_DEPLOYMENT.md)*
