# PHASE 09 — ADVANCED GAMIFICATION
> **COGNARC Engineering Governance | Phase 9 of 10**
> Agents: `frontend-developer` · `backend-developer` · `database-architect` · `gsd-planner`
> Skills: `senior-architect` · `gepetto` · `ui-design-system` · `ui-ux-pro-max` · `ux-researcher-designer`

---

## Phase Goal

Implement the complete Phase 3 gamification layer — Boss Battle system with 60-minute timer, 30+ achievement badges with automatic trigger logic, Supabase materialized view leaderboard, Framer Motion UI animations (XP bar spring, level-up full-screen ceremony, quest card flip), and streak shields — producing a visually premium, psychologically engaging experience.

---

## Architectural Rules Addressed

| Rule (CLAUDE.md) | Constraint |
|---|---|
| §05 Design System | Framer Motion for ALL interactive animations. No CSS-only transitions. |
| §05 State Management | Boss battle timer state in `useState` (component-local). XP state in Zustand. |
| §08 Supabase Rules | `achievements` is insert-only. Never UPDATE or DELETE achievement records. |
| §08 Supabase Rules | `leaderboard` is a materialized view. Refresh every 15 minutes. |
| §09 Event System | `BossBattleCompletedEvent` → background tasks: Achievement, Leaderboard. |
| §13 Phase 3 | Boss battles, badges, Supabase leaderboard, Framer Motion are Phase 3 features. |
| §31 Animation Specs | All animations defined with exact triggers, durations, and library. |

---

## Task Breakdown (Checklist)

### Boss Battle System — Backend

- [ ] **T1.1** Implement `apps/api/app/engines/battle_engine.py`:
  ```python
  BOSS_XP_RANGE = (500, 1500)
  BOSS_TIME_LIMIT_MINUTES = 60
  BOSS_UNLOCK_AFTER_FAILURE_DAYS = 3

  def calculate_boss_xp(score: float, streak_count: int) -> int:
      base = int(BOSS_XP_RANGE[0] + (BOSS_XP_RANGE[1] - BOSS_XP_RANGE[0]) * score)
      streak_mult = 1.0 if streak_count < 7 else 1.25
      return int(base * streak_mult)

  def score_boss_battle(theory_scores: list[float], code_passed: bool,
                         debug_passed: bool) -> float:
      theory_avg = sum(theory_scores) / len(theory_scores) if theory_scores else 0
      code_score = 1.0 if code_passed else 0.0
      debug_score = 1.0 if debug_passed else 0.0
      # Weighted: theory 30%, code 50%, debug 20%
      return round(theory_avg * 0.3 + code_score * 0.5 + debug_score * 0.2, 3)
  ```

- [ ] **T1.2** Implement `apps/api/app/services/battle_service.py`:
  - `get_weekly_boss(user_id) → BossBattle | None` — generates weekly boss tied to current skill node
  - `start_boss(user_id, boss_id) → BossBattleSession` — creates timed session in Redis (TTL 3600s)
  - `submit_boss_part(session_id, part, content) → PartResult` — evaluates each part
  - `finalize_boss(session_id) → BossBattleResult` — awards XP, stores in Supabase `boss_battles`

- [ ] **T1.3** Implement `apps/api/app/api/v1/battles.py`:
  - `GET /battles/weekly` — returns current week's boss battle definition
  - `POST /battles/{id}/start` — starts timed session
  - `POST /battles/{id}/submit` — submits all 3 parts, returns final score + XP
  - Rate limit: 1 boss battle attempt per boss per 3-day cooldown

- [ ] **T1.4** Boss battle session stored in Redis: key `boss:{user_id}:{boss_id}`, TTL 3600s
  - Contains: start time, parts submitted, current scores

- [ ] **T1.5** On boss completion: fire `BossBattleCompletedEvent` → background tasks:
  - Award XP via `gamification_service`
  - Insert boss result to Supabase `boss_battles`
  - Check achievement triggers
  - Update leaderboard position

### Achievement Badge System

- [ ] **T2.1** Define all 30+ badge triggers in `apps/api/app/engines/achievement_engine.py`:
  ```python
  BADGE_TRIGGERS = {
      "first_quest": lambda stats: stats["total_quests_completed"] >= 1,
      "streak_7": lambda stats: stats["current_streak"] >= 7,
      "streak_30": lambda stats: stats["current_streak"] >= 30,
      "streak_100": lambda stats: stats["current_streak"] >= 100,
      "boss_slayer": lambda stats: stats["bosses_passed"] >= 1,
      "boss_legend": lambda stats: stats["bosses_passed"] >= 10,
      "speed_demon": lambda stats: stats["speed_completions_count"] >= 5,
      "night_owl": lambda stats: stats["late_night_completions"] >= 3,
      "early_bird": lambda stats: stats["before_8am_completions"] >= 5,
      "century": lambda stats: stats["total_quests_completed"] >= 100,
      "coding_guru": lambda stats: stats["coding_quests_completed"] >= 50,
      "debug_wizard": lambda stats: stats["debug_quests_completed"] >= 25,
      "level_10": lambda stats: stats["level"] >= 10,
      "level_25": lambda stats: stats["level"] >= 25,
      "level_50": lambda stats: stats["level"] >= 50,
      "comeback_kid": lambda stats: stats["comeback_mode_completed"] >= 1,
      "perfect_week": lambda stats: stats["weekly_completion_rate"] == 1.0,
      # ... 13 more triggers
  }

  def check_achievements(stats: dict, already_earned: set[str]) -> list[str]:
      """Returns list of newly earned badge_ids."""
      return [
          badge_id for badge_id, trigger in BADGE_TRIGGERS.items()
          if badge_id not in already_earned and trigger(stats)
      ]
  ```

- [ ] **T2.2** Implement achievement check as background task (non-blocking):
  ```python
  async def process_achievement_check(user_id: str, db, supabase):
      stats = await build_user_stats(user_id, db)
      earned = await get_earned_badge_ids(user_id, supabase)
      new_badges = achievement_engine.check_achievements(stats, set(earned))
      for badge_id in new_badges:
          await supabase.table("achievements").insert({
              "user_id": user_id,
              "badge_id": badge_id,
              "badge_name": BADGE_NAMES[badge_id],
              "xp_bonus": BADGE_XP_BONUS[badge_id],
          }).execute()
  ```

- [ ] **T2.3** Create `apps/web/src/features/gamification/components/BadgeDisplay.tsx`
  - Grid of earned badges with icons and names
  - Locked badges shown as greyed-out silhouettes with hint text

- [ ] **T2.4** Create `apps/web/src/features/gamification/components/BadgeEarnedToast.tsx`
  - Animated toast (Framer Motion slide-in) on badge earned
  - Shows badge icon, name, XP bonus

### Supabase Leaderboard (Materialized View)

- [ ] **T3.1** Write `infrastructure/supabase/migrations/002_leaderboard_view.sql`:
  ```sql
  -- Leaderboard materialized view (refreshed every 15 min via cron)
  CREATE MATERIALIZED VIEW IF NOT EXISTS public.leaderboard_view AS
  SELECT
    lb.user_id,
    lb.username,
    lb.total_xp,
    lb.current_level,
    lb.streak,
    lb.updated_at,
    RANK() OVER (ORDER BY lb.total_xp DESC) as rank
  FROM public.leaderboard lb
  WITH DATA;

  CREATE UNIQUE INDEX IF NOT EXISTS leaderboard_view_user_id
    ON public.leaderboard_view(user_id);

  -- Refresh function
  CREATE OR REPLACE FUNCTION refresh_leaderboard()
  RETURNS void AS $$
    REFRESH MATERIALIZED VIEW CONCURRENTLY public.leaderboard_view;
  $$ LANGUAGE SQL;
  ```

- [ ] **T3.2** Schedule leaderboard refresh via Supabase Cron (pg_cron):
  ```sql
  SELECT cron.schedule('refresh-leaderboard', '*/15 * * * *',
    'SELECT refresh_leaderboard();');
  ```

- [ ] **T3.3** Implement `GET /leaderboard` in FastAPI:
  ```python
  @router.get("/leaderboard")
  async def get_leaderboard(limit: int = 100) -> list[LeaderboardEntry]:
      result = await supabase.table("leaderboard_view")\
          .select("*").order("rank").limit(limit).execute()
      return [LeaderboardEntry(**row) for row in result.data]
  ```

- [ ] **T3.4** Update leaderboard after every XP award (background task):
  ```python
  async def sync_leaderboard_entry(user_id: str, username: str, total_xp: int, level: int, streak: int, supabase):
      await supabase.table("leaderboard").upsert({
          "user_id": user_id,
          "username": username,
          "total_xp": total_xp,
          "current_level": level,
          "streak": streak,
          "updated_at": datetime.utcnow().isoformat(),
      }).execute()
  ```

- [ ] **T3.5** Implement `apps/web/src/features/leaderboard/` feature:
  - `LeaderboardPage.tsx` — top 100, user's own rank highlighted
  - `LeaderboardRow.tsx` — rank, avatar, username, level, XP, streak
  - React Query: 15-minute stale time (matches materialized view refresh)

### Framer Motion Animations

- [ ] **T4.1** Install Framer Motion: `pnpm add framer-motion` in `apps/web/`
- [ ] **T4.2** Configure dynamic import for Framer Motion (performance rule §21):
  ```typescript
  const MotionDiv = dynamic(() => import('framer-motion').then(m => m.motion.div), { ssr: false })
  ```

- [ ] **T4.3** Implement XP Bar spring animation (§31 spec: 0.8s ease-out):
  ```typescript
  // XpBar.tsx
  import { motion } from 'framer-motion'

  export function XpBar({ progressPct }: { progressPct: number }) {
    return (
      <div className="xp-bar-track">
        <motion.div
          className="xp-bar-fill"
          initial={{ width: '0%' }}
          animate={{ width: `${progressPct * 100}%` }}
          transition={{ type: 'spring', stiffness: 100, damping: 20, duration: 0.8 }}
        />
      </div>
    )
  }
  ```

- [ ] **T4.4** Implement Level-Up Ceremony (§31 spec: 3.5s, full-screen, unskippable):
  ```typescript
  // LevelUpCeremony.tsx
  export function LevelUpCeremony({ newLevel, tierName }: { newLevel: number; tierName: string }) {
    return (
      <AnimatePresence>
        <motion.div
          className="level-up-overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.5 }}
        >
          <motion.div
            initial={{ scale: 0, rotate: -180 }}
            animate={{ scale: 1, rotate: 0 }}
            transition={{ type: 'spring', stiffness: 200, delay: 0.3, duration: 1.0 }}
          >
            <h1>LEVEL {newLevel}</h1>
            <p>{tierName}</p>
          </motion.div>
          {/* Particle burst at 3.5s auto-dismiss */}
        </motion.div>
      </AnimatePresence>
    )
  }
  ```

- [ ] **T4.5** Implement Quest Completion Card Flip (§31 spec: 0.4s):
  - Card face flips to success state with green glow + checkmark on "Mark Complete"

- [ ] **T4.6** Implement Streak Extension Pulse (§31 spec: 0.6s):
  - Flame emoji pulses + streak number increments with bounce

- [ ] **T4.7** Implement Boss Battle Entry Animation (§31 spec: 2.0s):
  - Screen dims → dramatic title card → countdown timer appears

- [ ] **T4.8** Implement Skill Node Unlock Animation (§31 spec: 1.5s):
  - Node pulses gold → connection lines draw to next node

### 90-Day Activity Heatmap

- [ ] **T5.1** Implement `GET /analytics/activity` in FastAPI:
  - Returns array of `{date: ISO string, quests_completed: int}` for last 90 days
  - Aggregation from `progress_logs` MongoDB collection

- [ ] **T5.2** Implement `apps/web/src/features/analytics/components/ActivityHeatmap.tsx`:
  - GitHub-style contribution graph in purple tones
  - 13 columns × 7 rows (91 days)
  - Intensity based on quests_completed (0=surface-dark, 4+=primary-purple)
  - Tooltip on hover: date + count

### Streak Shield System

- [ ] **T6.1** Update `apps/api/app/engines/streak_engine.py`:
  ```python
  def earn_shield(streak: Streak) -> Streak:
      """Earn 1 shield per 7-day streak. Max 2 stacked."""
      new_shields = min(2, streak.shield_count + 1)
      return Streak(**streak.dict(), shield_count=new_shields)

  def check_shield_earn(streak_count: int, previous_streak_count: int,
                         current_shields: int) -> bool:
      """Check if new 7-day multiple crossed."""
      return (streak_count > 0 and streak_count % 7 == 0 and
              previous_streak_count % 7 != 0 and current_shields < 2)
  ```

- [ ] **T6.2** Update `StreakDisplay.tsx` to show shield icons (🛡 × shield_count)
- [ ] **T6.3** Shield activation notification: "Your streak shield protected your 12-day streak!"

---

## Data Flow & Dependencies

```
[Boss Battle Submit — POST /battles/{id}/submit]
       │
[battle_engine.score_boss_battle()]  ← PURE FUNCTION
       │
[gamification_service.award_quest_xp()]
       │ synchronous (in-request)
       │
[BackgroundTasks] (non-blocking)
  ├── achievement_engine.check_achievements() → Supabase achievements INSERT
  ├── sync_leaderboard_entry() → Supabase leaderboard UPSERT
  └── push_notification: "Boss Defeated! +1200 XP"

[Frontend: QuestCard "Mark Complete"]
  → motion.div spring animation (0.4s card flip)
  → useGamificationStore.awardXp() → Zustand
    → XpBar motion.div spring (0.8s)
    → LevelUpCeremony if level_up (3.5s, AnimatePresence)
    → StreakDisplay pulse (0.6s)

[Supabase Leaderboard Refresh]
  pg_cron every 15min → REFRESH MATERIALIZED VIEW CONCURRENTLY
```

---

## Testing & Observability

### Required Tests

| Test | Tool | File | Target |
|---|---|---|---|
| `calculate_boss_xp()` correct range | pytest | `tests/unit/test_battle_engine.py` | 100% |
| `score_boss_battle()` weighted correctly | pytest | `tests/unit/test_battle_engine.py` | 100% |
| `check_achievements()` triggers correctly | pytest | `tests/unit/test_achievement_engine.py` | 100% |
| Achievement is NOT re-awarded if already earned | pytest | `tests/unit/test_achievement_engine.py` | 100% |
| `achievements` table is insert-only (no UPDATE) | pytest | `tests/integration/test_supabase.py` | 100% |
| Leaderboard endpoint returns ranked list | pytest + TestClient | `tests/integration/test_leaderboard.py` | 100% |
| `XpBar` animates to correct width | Vitest | `gamification/tests/XpBar.test.tsx` | 90% |
| Boss battle timer expires in 60 min | pytest | `tests/integration/test_battles.py` | 100% |
| E2E: complete boss → see XP + badge | Playwright | `tests/e2e/boss_battle.spec.ts` | 100% |

### Observability

- [ ] Log every badge earned: `user_id`, `badge_id`, `trigger_event`, `xp_bonus`
- [ ] Log every boss battle: `user_id`, `boss_id`, `score`, `passed`, `time_taken_min`, `xp_awarded`
- [ ] Track leaderboard refresh time: alert if > 5 seconds
- [ ] Framer Motion: measure animation frame drops via `PerformanceObserver` in production

### Performance Targets

| Animation | Budget |
|---|---|
| XP bar frame rate | 60fps (no jank) |
| Level-up ceremony initial render | < 100ms |
| Leaderboard page load | < 800ms (React Query cache + materialized view) |
| Badge check background task | < 200ms |

---

## Validation Gate

**Phase 9 is DONE when ALL pass:**

```bash
# 1. Boss battle complete loop
# Start boss → submit all 3 parts → see XP + badge awarded
# POST /battles/{id}/start → POST /battles/{id}/submit → {passed, xp_awarded, badge}

# 2. Achievement triggers
# Complete 1 quest → check Supabase achievements table → "first_quest" badge inserted
# Reach 7-day streak → "streak_7" badge inserted

# 3. Leaderboard live
# GET /leaderboard → [{rank:1, username:..., total_xp:..., level:..., streak:...}]
# Wait 15 min → check leaderboard_view refreshed (timestamps updated)

# 4. Framer Motion animations
# Dashboard → complete quest → card flips + XP bar springs (60fps in DevTools Performance)
# Level up → full-screen ceremony appears → auto-dismisses in 3.5s

# 5. Activity heatmap
# GET /analytics/activity → 90 days of data
# UI shows heatmap in purple tones with correct density

# 6. Streak shield
# Build 7-day streak → shield icon appears in dashboard (🛡 x1)

# 7. Unit + E2E tests
cd apps/api && pytest tests/ -v -k "battle or achievement or leaderboard"  # All green
cd apps/web && npx playwright test  # No regressions
```

---

## Absolute 'Do-Not-Do' List for Phase 9

| Forbidden | Reason |
|---|---|
| ❌ UPDATE or DELETE `achievements` rows | Insert-only immutability rule §08 |
| ❌ Compute leaderboard rank in application code | Use Supabase materialized view RANK() §08 |
| ❌ Inline CSS transitions for interactive elements | Framer Motion for ALL animations §05 |
| ❌ Global leaderboard (1M+ users) | Top 100 only — Supabase free tier constraint |
| ❌ LangGraph / agent state machine | Phase 4 (COGNARC Phase 10) — never before this |
| ❌ Boss battle XP from AI output directly | XP from `battle_engine.calculate_boss_xp()` only §16 |
| ❌ Blocking HTTP response for achievement check | Must be `BackgroundTasks` (non-blocking) §09 |
| ❌ Raw `<img>` tags in badge display | `next/image` only §05 |
| ❌ Achievement check in request path | Background task only — performance impact §09 |
| ❌ Hardcode hex colors in animation components | Use CSS variable tokens §05 |

---

*Phase 9 Target: Days 26–45 (COGNARC Phase 3)*
*Owner: `frontend-developer` (animations + leaderboard UI) · `backend-developer` (boss + achievements)*
*Next: [PHASE_10_AGENTIC_ORCHESTRATION.md](./PHASE_10_AGENTIC_ORCHESTRATION.md)*
