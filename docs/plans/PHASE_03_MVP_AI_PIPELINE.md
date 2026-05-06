# PHASE 03 — MVP AI PIPELINE
> **COGNARC Engineering Governance | Phase 3 of 10**
> Agents: `ai-engineer` · `backend-architect` · `backend-developer` · `gsd-planner`
> Skills: `senior-architect` · `gepetto` · `prompt-engineer` · `senior-prompt-engineer`

---

## Phase Goal

Implement a single synchronous Groq API adapter, one versioned prompt template, and the end-to-end quest generation pipeline (`POST /quests/generate`) — producing exactly 3 valid Pydantic-validated quest objects from real user context, with zero agents, zero orchestration frameworks, and zero LLM abstractions beyond a direct HTTP call.

---

## Architectural Rules Addressed

| Rule (CLAUDE.md) | Constraint |
|---|---|
| §07 AI Isolation | ALL AI logic lives exclusively in `ai-services/`. Never in `apps/api/services/`. |
| §07 MVP Phase | Single Groq prompt call only. Agents, LangGraph, BGE forbidden in this phase. |
| §07 Quest Pipeline | Context build ~50ms → Groq call ~700–900ms → Parse → Validate → Store. |
| §13 Non-Negotiable MVP | AI Adapter = single synchronous Groq call, one prompt template. |
| §16 AI Safety | Never trust AI output. All outputs pass through Pydantic validators before storage. |
| §16 AI Safety | Prompt injection mitigated: sanitize all user strings before injection. |
| §16 AI Safety | AI failure is non-fatal: fallback to cached quests on any error. |
| §19 Observability | Log all Groq API calls: tokens, latency, success/failure. |

---

## Task Breakdown (Checklist)

### AI Services Directory Scaffold

- [ ] **T1.1** Create `ai-services/` directory structure:
  ```
  ai-services/
  ├── adapters/
  │   └── groq_adapter.py        # Direct Groq API client
  ├── prompts/
  │   └── quest_generation_v1.py # Versioned prompt template
  ├── parsers/
  │   └── quest_output_parser.py # Pydantic output validator
  ├── validation/
  │   └── quest_validator.py     # Schema + business logic validation
  ├── __init__.py
  └── requirements.txt           # groq, pydantic, tenacity
  ```
- [ ] **T1.2** Create `ai-services/requirements.txt`: `groq`, `pydantic>=2.0`, `tenacity`, `httpx`
- [ ] **T1.3** Create `ai-services/__init__.py` — expose `generate_quests()` as the only public interface

### Groq Adapter

- [ ] **T2.1** Implement `ai-services/adapters/groq_adapter.py`
  ```python
  import os
  from groq import Groq
  from tenacity import retry, stop_after_attempt, wait_exponential

  class GroqAdapter:
      def __init__(self):
          self.client = Groq(api_key=os.environ["GROQ_API_KEY"])
          self.model = "mixtral-8x7b-32768"

      @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=4))
      def complete(self, system_prompt: str, user_prompt: str,
                   max_tokens: int = 1500) -> str:
          response = self.client.chat.completions.create(
              model=self.model,
              messages=[
                  {"role": "system", "content": system_prompt},
                  {"role": "user", "content": user_prompt},
              ],
              max_tokens=max_tokens,
              temperature=0.7,
          )
          return response.choices[0].message.content
  ```
- [ ] **T2.2** Add key rotation support: read `GROQ_API_KEYS` (comma-separated), round-robin per request
- [ ] **T2.3** Add timeout wrapper: `httpx.Timeout(connect=5.0, read=15.0)`
- [ ] **T2.4** Add Langfuse trace logging for every Groq call (tokens in, tokens out, latency_ms, success)

### Prompt Template (Versioned)

- [ ] **T3.1** Implement `ai-services/prompts/quest_generation_v1.py`

  **System Prompt:**
  ```python
  SYSTEM_PROMPT_V1 = """You are Cognarc, an expert skill development engine for developers.
  Generate exactly 3 learning quests as valid JSON matching the provided schema.
  Rules:
    - Vary quest types across the 3 quests (no repeated type)
    - Match difficulty to user level and difficulty_modifier
    - Quests must be completable in estimated_minutes on a laptop
    - Do not generate quests similar to recent_quest_summaries
    - Every quest must map to exactly one skill_node
    - Output ONLY valid JSON. No explanation, no markdown fences.

  Output schema (array of 3 objects):
  [
    {
      "title": string,
      "type": "theory"|"coding"|"debug"|"research"|"build",
      "difficulty": "easy"|"medium"|"hard",
      "estimated_minutes": integer,
      "xp_reward": integer,
      "skill_node": string,
      "hints": [string]
    }
  ]"""
  ```

  **User Prompt Template:**
  ```python
  USER_PROMPT_TEMPLATE_V1 = """USER CONTEXT:
  - Level: {user_level} | Skill Focus: {skill_node_current} ({node_progress_pct}% complete)
  - Streak: {streak_count} days | Difficulty modifier: {difficulty_modifier}
  - 7-day completion rate: {completion_rate_7d_pct}%
  - Recent quest types: {recent_quest_types}
  - Recent quest summaries (do NOT repeat): {recent_quest_summaries}

  Generate today's 3 quests."""
  ```

- [ ] **T3.2** Create a second stub file `quest_generation_v2.py` (empty) — enforce versioning convention from day one
- [ ] **T3.3** Add prompt registry: `PROMPT_VERSIONS = {"v1": quest_generation_v1}` — never edit deployed version in-place

### Output Parser + Validator

- [ ] **T4.1** Implement `ai-services/parsers/quest_output_parser.py`
  ```python
  import json
  from pydantic import BaseModel, ValidationError

  class ParsedQuest(BaseModel):
      title: str
      type: str
      difficulty: str
      estimated_minutes: int
      xp_reward: int
      skill_node: str
      hints: list[str] = []

  def parse_quest_output(raw: str) -> list[ParsedQuest]:
      """Parse and validate Groq JSON output. Raises ValueError on failure."""
      try:
          data = json.loads(raw)
          return [ParsedQuest(**q) for q in data]
      except (json.JSONDecodeError, ValidationError, KeyError) as e:
          raise ValueError(f"Quest parse failure: {e}") from e
  ```

- [ ] **T4.2** Implement `ai-services/validation/quest_validator.py`
  - Validate quest type is one of 5 allowed values
  - Validate difficulty matches user level range (no "hard" for level 1–3 users)
  - Validate `xp_reward` is in expected range for difficulty
  - Validate all 3 quests have distinct `type` values
  - Sanitize `title` and `hints` strings (strip control chars, max length enforcement)

### Quest Generation Service (in `apps/api/`)

- [ ] **T5.1** Implement `apps/api/app/services/quest_service.py`
  ```python
  async def generate_quests_for_user(user_id: str, db) -> list[Quest]:
      # 1. Fetch user context (~50ms MongoDB + Redis)
      user = await user_repository.get_user_by_id(user_id, db)
      streak = await redis_cache.get_streak_counter(user_id)
      recent = await progress_repository.get_logs_for_user(user_id, limit=7)

      # 2. Check cache first
      cached = await redis_cache.get_cached_quests(user_id)
      if cached:
          return cached

      # 3. Build prompt context
      context = build_quest_context(user, streak, recent)

      # 4. Call AI (through adapter interface only)
      try:
          raw = groq_adapter.complete(SYSTEM_PROMPT_V1, format_user_prompt(context))
          quests = parse_quest_output(raw)
          validated = [quest_validator.validate(q, user) for q in quests]
      except (ValueError, Exception) as e:
          logger.error("Quest generation failed", error=str(e), user_id=user_id)
          return await get_fallback_quests(user_id, db)   # yesterday's cache

      # 5. Persist + cache
      quest_docs = [build_quest_doc(q, user) for q in validated]
      await quest_repository.create_many(quest_docs, db)
      await redis_cache.cache_quests(user_id, quest_docs)
      return quest_docs
  ```

- [ ] **T5.2** Implement `apps/api/app/api/v1/quests.py`:
  - `POST /quests/generate` — rate limited 5/day/user; idempotent (returns cache if already generated)
  - `GET /quests/today` — returns today's quests (cache-first)
  - `POST /quests/{id}/skip` — mark skipped, record behavioral signal

- [ ] **T5.3** Implement `apps/api/app/engines/gamification_engine.py` — `calculate_xp()` pure function per §21 formula:
  ```python
  BASE_XP = {"easy": 50, "medium": 100, "hard": 200, "boss": 500}
  STREAK_MULTIPLIER = {range(1,7): 1.00, range(7,14): 1.25, range(14,30): 1.50}
  TYPE_MULTIPLIER = {"theory": 0.8, "coding": 1.0, "debug": 1.1, "build": 1.3}

  def calculate_xp(difficulty, streak_count, time_bonus, quest_type, difficulty_modifier) -> int:
      base = BASE_XP[difficulty]
      streak_mult = get_streak_multiplier(streak_count)
      type_mult = TYPE_MULTIPLIER[quest_type]
      time_mult = 1.2 if time_bonus else 1.0
      return int(base * difficulty_modifier * streak_mult * time_mult * type_mult)
  ```

- [ ] **T5.4** Implement `apps/api/app/api/v1/quests.py`: `POST /quests/{id}/evaluate`
  - MVP: self-report only (user confirms completion)
  - Call `gamification_engine.calculate_xp()`
  - Write `ProgressLog` to MongoDB
  - Update `users.total_xp` via `user_repository.update_user()`
  - Fire `QuestCompletedEvent` → background task for streak update

### Context Builder

- [ ] **T6.1** Implement `apps/api/app/services/quest_context_builder.py`
  - Pulls user.level, skill_state.current_node, node_progress from MongoDB
  - Pulls streak_count from Redis
  - Fetches last 7 progress_logs for `recent_quest_types` and `recent_quest_summaries`
  - Computes `completion_rate_7d` from progress_logs
  - Sanitizes all user-controlled strings (username, skill node names) before injection

---

## Data Flow & Dependencies

```
POST /quests/generate
       │
[quests.py router]  — validates JWT, rate limit check
       │
[quest_service.py]  — orchestrates the pipeline
       │
  ┌────┴───────────────────┐
  │                        │
[user_repository]    [redis_cache]
[progress_repository]       │
  │                  ┌─────▼──────┐
  │                  │ Cache HIT? │──YES──▶ return cached quests
  │                  └─────┬──────┘
  │                        │ MISS
  └────────────────────────┘
       │
[quest_context_builder.py]  — assemble prompt payload
       │
[ai-services/adapters/groq_adapter.py]
       │─ POST https://api.groq.com/openai/v1/chat/completions
       │  (system_prompt_v1 + user_prompt with context)
       │◀── raw JSON string (~700-900ms)
       │
[ai-services/parsers/quest_output_parser.py]
       │─ json.loads → ParsedQuest × 3
       │
[ai-services/validation/quest_validator.py]
       │─ type/difficulty/xp range checks
       │─ distinct types enforced
       │
[quest_repository.create_many()]  → [MongoDB: quests collection]
[redis_cache.cache_quests()]      → [Upstash Redis: TTL 24h]
       │
HTTP 200 → [3 Quest objects JSON]
```

**Dependency Order:**
1. Phase 1 (Foundation) complete → Auth + MongoDB connected
2. Phase 2 (Data Modeling) complete → all models + repos exist
3. `GROQ_API_KEY` env var set → before any AI call
4. `ai-services/` imported via adapter interface → NEVER directly in services

---

## Testing & Observability

### Required Tests

| Test | Tool | File | Target |
|---|---|---|---|
| Groq adapter returns string on success | pytest | `tests/unit/test_groq_adapter.py` | 100% |
| Groq adapter retries on 429 | pytest (mock) | `tests/unit/test_groq_adapter.py` | 100% |
| `parse_quest_output()` accepts valid JSON | pytest | `tests/unit/test_quest_parser.py` | 100% |
| `parse_quest_output()` raises on malformed JSON | pytest | `tests/unit/test_quest_parser.py` | 100% |
| `calculate_xp()` correct for all difficulty × streak combos | pytest | `tests/unit/test_gamification_engine.py` | 100% |
| `POST /quests/generate` returns 3 quests | pytest + TestClient | `tests/integration/test_quests.py` | 100% |
| `POST /quests/generate` is idempotent (cached) | pytest + TestClient | `tests/integration/test_quests.py` | 100% |
| `POST /quests/generate` rate limits at 5/day | pytest + TestClient | `tests/integration/test_quests.py` | 100% |
| AI failure → fallback to cached quests | pytest (mock Groq) | `tests/integration/test_quests.py` | 100% |

### Observability Requirements

- [ ] Every Groq call logged: `provider="groq"`, `prompt_tokens`, `completion_tokens`, `latency_ms`, `success`
- [ ] Parse failures logged to Sentry with truncated raw output (max 500 chars)
- [ ] Quest generation event logged: `quest_generated` with `user_id`, `generated_by`, `latency_ms`
- [ ] Langfuse trace created for every Groq invocation

### SLO Targets

| Metric | Target |
|---|---|
| Quest generation latency (p95 cold) | < 1500ms |
| Quest fetch from Redis cache (p95) | < 100ms |
| Groq parse success rate | > 95% |
| Fallback activation rate | < 5% |

---

## Validation Gate

**Phase 3 is DONE when ALL pass:**

```bash
# 1. Hardcoded context test (Day 4 gate)
curl -X POST localhost:8000/ai/generate \
  -H "Authorization: Bearer <jwt>" \
  -H "Content-Type: application/json" \
  -d '{"user_level": 5, "skill_node": "RAG Systems"}'
# → {"quests": [3 valid objects with distinct types]}

# 2. Real user context test (Day 5 gate)
curl -X POST localhost:8000/quests/generate \
  -H "Authorization: Bearer <jwt>"
# → 3 quests stored in MongoDB, 200 response < 1500ms

# 3. Idempotency
# Call /quests/generate twice → same 3 quests returned, no duplicate DB entries

# 4. Unit tests
cd apps/api && pytest tests/unit/ tests/integration/ -v -k "quest or groq or xp"
# All green

# 5. Prompt version exists
cat ai-services/prompts/quest_generation_v1.py  # exists and is non-empty
```

---

## Absolute 'Do-Not-Do' List for Phase 3

| Forbidden | Reason |
|---|---|
| ❌ LangChain / LlamaIndex / any LLM framework | Raw Groq call only in MVP §07 |
| ❌ LangGraph or any agent state machine | Phase 4 ONLY §07 |
| ❌ BGE-small embeddings for deduplication | Phase 2 (COGNARC Phase 2) §07 |
| ❌ Phi-2 local fallback | Phase 2 (COGNARC Phase 2) §07 |
| ❌ Multi-step / chain-of-thought prompting | Single prompt template only |
| ❌ `exec()` / `eval()` on any AI output | AI safety §16 |
| ❌ AI awarding XP directly | XP calculation is deterministic engine only §16 |
| ❌ Importing `ai-services/` in service layer directly | Must go through adapter interface §07 |
| ❌ Editing deployed prompt template in-place | Create new version file §16 |
| ❌ Logging full prompt or completion (> 500 chars) | Log pollution + potential secret exposure |
| ❌ AI-only code evaluation (no test cases) | Hybrid model required — AI is advisory only §07 |

---

*Phase 3 Target: Days 4–6 (within MVP window)*
*Owner: `ai-engineer` (prompt + adapter) · `backend-developer` (service + routes)*
*Next: [PHASE_04_FRONTEND_UI.md](./PHASE_04_FRONTEND_UI.md)*
