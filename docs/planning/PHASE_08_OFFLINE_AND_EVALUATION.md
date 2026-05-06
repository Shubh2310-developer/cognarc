# PHASE 08 — OFFLINE & HYBRID EVALUATION
> **COGNARC Engineering Governance | Phase 8 of 10**
> Agents: `ai-engineer` · `frontend-developer` · `backend-developer` · `gsd-planner`
> Skills: `senior-architect` · `gepetto` · `optimization-gguf` · `rag-engineer` · `qa-test-planner`

---

## Phase Goal

Implement full PWA offline support (next-pwa + Dexie.js background sync), the hybrid code evaluation engine (sandboxed subprocess test cases + AI quality feedback), and the Phi-2 local LLM fallback — so that quest delivery and progress tracking work without internet, and code submissions are evaluated with deterministic test cases as the primary pass/fail gate.

---

## Architectural Rules Addressed

| Rule (CLAUDE.md) | Constraint |
|---|---|
| §07 Hybrid Code Evaluation | Primary: sandboxed subprocess test cases. Secondary: Groq AI feedback. AI is advisory only. |
| §16 AI Safety | NEVER use `exec()` or `eval()` on user code. ALWAYS use `subprocess.run(timeout=10)`. |
| §16 AI Safety | Sandboxed subprocess: no network, no filesystem write, 64MB memory limit, 10s timeout. |
| §14 MVP Simplifications | Code evaluation was `self_report` in MVP. Now replaced with real hybrid model. |
| §13 Phase 2 | PWA offline, Dexie.js background sync, Phi-2 fallback, push notifications are Phase 2 features. |
| §07 AI Architecture | Phi-2 fallback only activates when Groq fails. Groq is always primary. |

---

## Task Breakdown (Checklist)

### PWA Setup (next-pwa + Workbox)

- [ ] **T1.1** Install next-pwa: `pnpm add next-pwa` in `apps/web/`
- [ ] **T1.2** Configure `apps/web/next.config.js`:
  ```javascript
  const withPWA = require('next-pwa')({
    dest: 'public',
    register: true,
    skipWaiting: true,
    disable: process.env.NODE_ENV === 'development',
    runtimeCaching: [
      {
        urlPattern: /\/api\/v1\/quests\/today/,
        handler: 'NetworkFirst',
        options: {
          cacheName: 'quests-cache',
          expiration: { maxAgeSeconds: 86400 }, // 24h
        },
      },
      {
        urlPattern: /\/api\/v1\/users\/me/,
        handler: 'StaleWhileRevalidate',
        options: { cacheName: 'user-cache' },
      },
    ],
  })
  module.exports = withPWA({ reactStrictMode: true })
  ```

- [ ] **T1.3** Create `apps/web/public/manifest.json`:
  ```json
  {
    "name": "COGNARC — Gamified Skill Engine",
    "short_name": "COGNARC",
    "description": "AI-powered gamified learning quests",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#0F0F1A",
    "theme_color": "#6D28D9",
    "icons": [
      { "src": "/icon-192.png", "sizes": "192x192", "type": "image/png" },
      { "src": "/icon-512.png", "sizes": "512x512", "type": "image/png" }
    ]
  }
  ```

- [ ] **T1.4** Add `<link rel="manifest">` and theme-color meta tag to `apps/web/src/app/layout.tsx`
- [ ] **T1.5** Validate: Chrome DevTools → Application → Service Workers → active

### Dexie.js Background Sync

- [ ] **T2.1** Expand `apps/web/src/shared/utils/db.ts` to include pending sync table:
  ```typescript
  export interface PendingSync {
    id?: number
    action: 'complete_quest' | 'skip_quest' | 'update_progress'
    payload: Record<string, unknown>
    createdAt: Date
    retryCount: number
  }

  class CognarcDB extends Dexie {
    quests!: Table<CachedQuest>
    pendingSync!: Table<PendingSync>
    userProfile!: Table<{ id: number; data: object; cachedAt: Date }>

    constructor() {
      super('CognarcDB')
      this.version(2).stores({
        quests: '++id, questId, date, cachedAt',
        pendingSync: '++id, action, createdAt, retryCount',
        userProfile: '++id, cachedAt'
      })
    }
  }
  ```

- [ ] **T2.2** Implement `apps/web/src/shared/utils/syncManager.ts`:
  ```typescript
  export async function queueOfflineAction(action: PendingSync['action'], payload: object) {
    await db.pendingSync.add({ action, payload, createdAt: new Date(), retryCount: 0 })
  }

  export async function flushPendingSync(apiClient: ApiClient) {
    const pending = await db.pendingSync.orderBy('createdAt').toArray()
    for (const item of pending) {
      try {
        if (item.action === 'complete_quest') {
          await apiClient.completeQuest(item.payload as CompleteQuestPayload)
        }
        await db.pendingSync.delete(item.id!)
      } catch {
        await db.pendingSync.update(item.id!, { retryCount: item.retryCount + 1 })
        if (item.retryCount >= 3) await db.pendingSync.delete(item.id!)
      }
    }
  }
  ```

- [ ] **T2.3** Register `online` event listener in `apps/web/src/app/providers.tsx`:
  ```typescript
  useEffect(() => {
    window.addEventListener('online', () => flushPendingSync(apiClient))
    return () => window.removeEventListener('online', () => {})
  }, [])
  ```

- [ ] **T2.4** Update `QuestCard.tsx` — detect offline state:
  ```typescript
  const isOnline = useOnlineStatus()  // custom hook wrapping navigator.onLine

  const handleComplete = async () => {
    if (isOnline) {
      await completeQuest(questId)
    } else {
      await queueOfflineAction('complete_quest', { questId, selfReport: true, timestamp: Date.now() })
      useGamificationStore.getState().awardXp(estimatedXp)  // Optimistic update
      toast.info('Saved offline. Will sync when connected.')
    }
  }
  ```

### Push Notifications (Streak Warnings)

- [ ] **T3.1** Implement Supabase Edge Function `apps/worker/push_notification.ts`:
  - Triggers at 8:00 PM user local time if no quest completed
  - Triggers at 10:30 PM if still no completion (final warning)
  - Uses Web Push API with VAPID keys

- [ ] **T3.2** Implement `POST /notifications/subscribe` in FastAPI:
  - Accept Web Push subscription object
  - Store in MongoDB `users.push_subscription`
  - Return 201 Created

- [ ] **T3.3** Implement frontend subscription in `features/notifications/hooks/usePushNotifications.ts`:
  ```typescript
  export function usePushNotifications() {
    const subscribe = async () => {
      const registration = await navigator.serviceWorker.ready
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY
      })
      await notificationsApi.subscribe(subscription)
    }
    return { subscribe }
  }
  ```

### Hybrid Code Evaluation Engine

- [ ] **T4.1** Implement `ai-services/evaluators/sandbox_runner.py`:
  ```python
  import subprocess
  import json
  import resource

  MAX_TIMEOUT = 10        # seconds
  MAX_MEMORY_BYTES = 64 * 1024 * 1024  # 64 MB

  def run_sandboxed(code: str, test_cases: list[dict], timeout: int = MAX_TIMEOUT) -> dict:
      results = []
      for tc in test_cases:
          full_code = f"{code}\nprint({tc['call']})"
          try:
              proc = subprocess.run(
                  ["python3", "-c", full_code],
                  capture_output=True,
                  text=True,
                  timeout=timeout,
                  # No network access (container-level via Docker)
              )
              passed = proc.stdout.strip() == str(tc["expected"])
              results.append({
                  "passed": passed,
                  "output": proc.stdout.strip()[:200],  # Truncate output
                  "error": proc.stderr.strip()[:200] if proc.stderr else None,
              })
          except subprocess.TimeoutExpired:
              results.append({"passed": False, "output": "TIMEOUT", "error": None})
          except Exception as e:
              results.append({"passed": False, "output": "ERROR", "error": str(e)[:200]})

      pass_count = sum(1 for r in results if r["passed"])
      pass_rate = pass_count / len(results) if results else 0.0
      return {
          "pass_rate": pass_rate,
          "pass_count": pass_count,
          "total_cases": len(results),
          "results": results,
          "passed": pass_rate >= 0.67,  # Default threshold
      }
  ```

- [ ] **T4.2** Implement `ai-services/evaluators/ai_feedback.py` — Groq AI quality review:
  ```python
  def get_ai_code_feedback(code: str, quest_title: str, groq_adapter: GroqAdapter) -> str:
      """AI feedback is ADVISORY ONLY. Does not affect XP award."""
      prompt = f"""Review this code submission for the quest: "{quest_title}"
  Code:
  ```python
  {code[:2000]}  # Truncate at 2000 chars
  ```
  Provide brief feedback on: code quality, edge cases, efficiency (max 150 words)."""
      try:
          return groq_adapter.complete(EVALUATOR_SYSTEM_PROMPT, prompt, max_tokens=200)
      except Exception:
          return "Feedback unavailable. Your solution has been recorded."
  ```

- [ ] **T4.3** Update `POST /quests/{id}/evaluate` in Quest Service:
  ```python
  @router.post("/{quest_id}/evaluate")
  async def evaluate_quest(
      quest_id: str,
      body: EvaluateQuestRequest,  # {code: str | None, self_report: bool, time_taken_min: float}
      current_user: User = Depends(get_current_user),
      db = Depends(get_db),
  ) -> EvaluateQuestResponse:
      quest = await quest_repository.get_quest_by_id(quest_id, db)

      if body.code and quest.evaluation_criteria.type == "code_submission":
          # Primary: sandboxed test cases
          sandbox_result = run_sandboxed(body.code, quest.test_cases)
          passed = sandbox_result["passed"]
          xp_modifier = 1.0 if passed else 0.5  # Partial XP on failure

          # Secondary: AI feedback (async, advisory only)
          background_tasks.add_task(
              store_ai_feedback, quest_id, body.code, quest.title
          )
      else:
          # Self-report for theory/research quests
          passed = body.self_report
          xp_modifier = 1.0

      xp_result = await gamification_service.award_quest_xp(
          current_user.id, quest, body.time_taken_min, xp_modifier, db
      )
      return EvaluateQuestResponse(
          passed=passed,
          xp_awarded=xp_result.xp_awarded,
          new_level=xp_result.new_level,
          sandbox_result=sandbox_result if body.code else None,
      )
  ```

- [ ] **T4.4** Write test cases storage in `quests` collection:
  ```json
  "test_cases": [
    {"call": "binary_search([1,3,5,7], 5)", "expected": 2},
    {"call": "binary_search([1,3,5,7], 9)", "expected": -1}
  ]
  ```

### Phi-2 Local Fallback (Offline AI)

- [ ] **T5.1** Download Phi-2 Q4_K_M GGUF model (~2GB):
  ```bash
  huggingface-cli download microsoft/phi-2-gguf phi-2.Q4_K_M.gguf \
    --local-dir ai-services/models/phi2/
  ```

- [ ] **T5.2** Implement `ai-services/adapters/phi2_adapter.py` using llama-cpp-python:
  ```python
  from llama_cpp import Llama

  class Phi2Adapter:
      def __init__(self, model_path: str):
          self.llm = Llama(
              model_path=model_path,
              n_ctx=2048,
              n_threads=2,
              verbose=False,
          )

      def complete(self, prompt: str, max_tokens: int = 512) -> str:
          result = self.llm(prompt, max_tokens=max_tokens, temperature=0.7)
          return result["choices"][0]["text"]
  ```

- [ ] **T5.3** Update `ai-services/orchestration/fallback.py`:
  ```python
  def generate_with_fallback(context: dict, groq: GroqAdapter, phi2: Phi2Adapter | None) -> tuple[list, str]:
      try:
          raw = groq.complete(SYSTEM_PROMPT_V1, format_user_prompt(context))
          quests = parse_quest_output(raw)
          return quests, "groq"
      except Exception as e:
          logger.warning("Groq failed, activating fallback", error=str(e))
          if phi2:
              raw = phi2.complete(format_phi2_prompt(context))
              quests = parse_quest_output(raw)
              # Tag offline quests clearly
              for q in quests:
                  q.title = f"[Offline] {q.title}"
              return quests, "phi2"
          # Final fallback: yesterday's cached quests
          raise FallbackExhaustedError("No AI provider available")
  ```

- [ ] **T5.4** Add "Offline Quest (Basic Mode)" visual badge to `QuestCard.tsx` when `generated_by === "phi2"`

### Anti-Boredom Engine Integration

- [ ] **T6.1** Implement `apps/api/app/engines/behavioral_engine.py`:
  ```python
  def detect_boredom(recent_sessions: list[Session]) -> bool:
      """Completion time < 50% of estimate for 2+ consecutive quests."""
      if len(recent_sessions) < 2:
          return False
      return all(
          s.time_taken_min < 0.5 * s.estimated_minutes
          for s in recent_sessions[-2:]
      )

  def detect_frustration(recent_quests: list[Quest]) -> bool:
      """Fail rate > 60% across last 5 quests."""
      if len(recent_quests) < 5:
          return False
      failed = sum(1 for q in recent_quests[-5:] if q.status == "failed")
      return failed / 5 > 0.60

  def calculate_difficulty_modifier(current: float, signal: str) -> float:
      adjustments = {
          "boredom": min(2.0, current + 0.2),
          "frustration": max(0.5, current - 0.2),
          "plateau": min(2.0, current + 0.3),
          "normal": current,
      }
      return adjustments.get(signal, current)
  ```

- [ ] **T6.2** Wire behavioral engine: run as background task 10 min after quest completion
- [ ] **T6.3** Update `users.behavioral_profile.difficulty_modifier` via `user_repository.update_user()`

---

## Data Flow & Dependencies

```
[Quest Submission — POST /quests/{id}/evaluate]
       │
  ┌────▼───────────────────────────────────┐
  │         Evaluation Router               │
  │  code_submission? → sandbox_runner.py  │
  │  theory/research? → self_report        │
  └────┬──────────────────────────────────┘
       │
  [sandbox_runner.py]
    └── subprocess.run(["python3", "-c", code])
          timeout=10, no network, no fs write
          → {pass_rate, results, passed}
       │
  [gamification_service.award_quest_xp()]
    └── xp = base * modifier * streak * type * time_bonus
    └── xp_modifier = 1.0 if passed else 0.5
       │
  [BackgroundTasks]
    ├── ai_feedback.py (Groq, advisory, non-blocking)
    └── behavioral_engine.detect_signal() → update difficulty_modifier

[Offline Completion — navigator.onLine === false]
  → queueOfflineAction('complete_quest', payload) → Dexie pendingSync
  → Optimistic XP update in Zustand
  → On reconnect: flushPendingSync() → POST /quests/{id}/evaluate
  → Reconcile XP with server authoritative value

[Phi-2 Fallback — Groq fails]
  → phi2_adapter.complete(prompt)
  → parse_quest_output(raw)
  → quests tagged generated_by="phi2"
  → "Offline Quest (Basic Mode)" badge in UI
```

---

## Testing & Observability

### Required Tests

| Test | Tool | File | Target |
|---|---|---|---|
| `run_sandboxed()` passes on correct code | pytest | `ai-services/tests/test_sandbox.py` | 100% |
| `run_sandboxed()` fails on wrong output | pytest | `ai-services/tests/test_sandbox.py` | 100% |
| `run_sandboxed()` times out on infinite loop | pytest | `ai-services/tests/test_sandbox.py` | 100% |
| `run_sandboxed()` handles malicious injection attempt | pytest | `ai-services/tests/test_sandbox.py` | 100% |
| Phi-2 adapter returns string output | pytest (mock) | `ai-services/tests/test_phi2.py` | 100% |
| `detect_boredom()` returns True on 2 fast completions | pytest | `tests/unit/test_behavioral_engine.py` | 100% |
| Dexie `queueOfflineAction()` stores to IndexedDB | Vitest | `shared/utils/db.test.ts` | 100% |
| `flushPendingSync()` calls API on reconnect | Vitest (mock) | `shared/utils/syncManager.test.ts` | 100% |
| PWA manifest accessible | Browser | Manual / Lighthouse | 100% |
| Quest completion works offline → syncs on reconnect | Playwright | `tests/e2e/offline.spec.ts` | 100% |

### Security Tests (Mandatory for Sandbox)

- [ ] Test: submit `import os; os.system('rm -rf /')` → timeout/error, no filesystem change
- [ ] Test: submit infinite loop `while True: pass` → TimeoutExpired after 10s
- [ ] Test: submit `import socket; socket.connect(...)` → ConnectionRefusedError (no network in container)

### Observability

- [ ] Log every sandbox execution: `user_id`, `quest_id`, `pass_rate`, `execution_time_ms`, `timeout_occurred`
- [ ] Alert: sandbox timeout rate > 10% → Slack (P2) — indicates malicious usage pattern
- [ ] Log Phi-2 activations: `fallback_activated`, reason, `phi2_latency_ms`

---

## Validation Gate

**Phase 8 is DONE when ALL pass:**

```bash
# 1. Sandbox safety tests
cd ai-services && pytest tests/test_sandbox.py -v
# All 8 safety scenarios pass

# 2. Hybrid evaluation end-to-end
curl -X POST .../quests/{id}/evaluate \
  -H "Authorization: Bearer <jwt>" \
  -d '{"code": "def binary_search(arr, t):\n  lo,hi=0,len(arr)-1\n  while lo<=hi:\n    mid=(lo+hi)//2\n    if arr[mid]==t: return mid\n    elif arr[mid]<t: lo=mid+1\n    else: hi=mid-1\n  return -1", "time_taken_min": 15}'
# → {"passed": true, "xp_awarded": 125, "pass_rate": 1.0}

# 3. Phi-2 fallback
# Temporarily set invalid GROQ_API_KEY → generate quests
# → Phi-2 activates → quests returned with "[Offline]" prefix

# 4. PWA offline
# Chrome DevTools → Application → Service Workers → check registered
# Go offline → refresh → quests still visible from cache

# 5. Background sync
# Go offline → mark quest complete → "Saved offline" toast
# Go online → verify POST /evaluate was called → XP updated in MongoDB
```

---

## Absolute 'Do-Not-Do' List for Phase 8

| Forbidden | Reason |
|---|---|
| ❌ `exec()` or `eval()` on user code | RCE risk — subprocess ONLY §16 |
| ❌ AI evaluation as primary pass/fail gate | AI is advisory; test cases are the gate §07 |
| ❌ Give full XP on sandbox failure | Only 50% partial XP on test case failure |
| ❌ Network access in sandbox subprocess | Security — no network in container |
| ❌ Phi-2 generating quests in online mode | Phi-2 is ONLY a fallback — Groq is always primary §07 |
| ❌ Logging user code content beyond 500 chars | Privacy + log size |
| ❌ LangGraph or agent orchestration | Phase 4 (COGNARC Phase 10) |
| ❌ Boss battle implementation | Phase 3 (COGNARC Phase 9) |
| ❌ Full Framer Motion animations | Phase 3 (COGNARC Phase 9) |
| ❌ Run Phi-2 in Railway without RAM check | Phi-2 Q4_K_M needs ~2GB RAM — verify before deploying |

---

*Phase 8 Target: Days 11–25 (COGNARC Phase 2 Core Engine)*
*Owner: `ai-engineer` (sandbox + Phi-2) · `frontend-developer` (PWA + offline sync)*
*Next: [PHASE_09_ADVANCED_GAMIFICATION.md](./PHASE_09_ADVANCED_GAMIFICATION.md)*
