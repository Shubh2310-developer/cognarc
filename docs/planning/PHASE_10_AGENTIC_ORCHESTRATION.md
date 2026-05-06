# PHASE 10 — AGENTIC ORCHESTRATION
> **COGNARC Engineering Governance | Phase 10 of 10**
> Agents: `ai-engineer` · `backend-architect` · `gsd-planner` · `gsd-roadmapper` · `performance-monitor`
> Skills: `senior-architect` · `gepetto` · `langgraph` · `autonomous-agents` · `ai-agents-architect` · `observability-langsmith`

---

## Phase Goal

Implement the complete LangGraph multi-agent state machine — Planner → TaskGenerator → Evaluator → Adaptation — with all agent state persisted in MongoDB, Sunday-night Planner cron jobs, daily 5:00 AM TaskGenerator runs, async Adaptation signals, and full Langfuse observability tracing — creating a system that continuously adapts the learning journey without human intervention.

---

## Architectural Rules Addressed

| Rule (CLAUDE.md) | Constraint |
|---|---|
| §07 Phase Gate | Do NOT implement LangGraph before Phases 1–3 (COGNARC Phases 6–9) are stable in production. |
| §07 LangGraph | All agent state in `users.agent_state` MongoDB. Never in memory. |
| §07 Agent Models | Planner: Mixtral-8x7B. TaskGenerator: Llama-3-70B. Evaluator: Mixtral-8x7B. Adaptation: pure Python (no LLM). |
| §07 AI Isolation | ALL LangGraph code lives in `ai-services/`. NEVER imported in `apps/api/services/`. |
| §07 Adaptation | Adaptation Agent is ALWAYS async. It NEVER blocks HTTP response. |
| §16 AI Safety | AI output always passes through Pydantic validators before storage. |
| §19 Observability | All agent invocations logged to Langfuse with full input/output trace. |
| §30 LangGraph Rules | LangGraph graph must complete in < 30s for synchronous paths. |

---

## Trigger Conditions (Must Be Met Before Starting)

> ⚠️ **Do NOT start Phase 10 until ALL conditions are true:**

- [ ] COGNARC Phases 6–9 complete and stable in production for at least **30 days**
- [ ] Single-pipeline Groq quest generation has > 95% success rate over last 30 days
- [ ] A/B test plan ready: single-pipeline vs multi-agent quest quality comparison metric defined
- [ ] All 4 agent specifications reviewed and signed off by `senior-architect`
- [ ] Langfuse project created and API keys configured

---

## Task Breakdown (Checklist)

### LangGraph State Machine Foundation

- [ ] **T1.1** Install LangGraph in `ai-services/requirements.txt`:
  ```
  langgraph>=0.2.0
  langchain-core>=0.3.0
  langfuse>=2.0.0
  ```

- [ ] **T1.2** Define `CognarcAgentState` TypedDict in `ai-services/orchestration/state.py`:
  ```python
  from typing import TypedDict, Annotated
  from langgraph.graph.message import add_messages

  class CognarcAgentState(TypedDict):
      user_id: str
      skill_state: dict          # From MongoDB users.skill_state
      behavioral_profile: dict   # From MongoDB users.behavioral_profile
      weekly_plan: list[dict]    # Planner output: 7-day schedule
      today_quests: list[dict]   # TaskGenerator output: 3 quest objects
      evaluation_results: list[dict]  # Evaluator output
      adaptation_signals: dict   # Adaptation output: difficulty_modifier update
      error: str | None          # Propagated error state
      retry_count: int           # Retry counter for fault tolerance
  ```

- [ ] **T1.3** Build LangGraph graph in `ai-services/orchestration/graph.py`:
  ```python
  from langgraph.graph import StateGraph, END
  from .state import CognarcAgentState
  from ..agents.planner_agent import planner_node
  from ..agents.task_generator_agent import task_generator_node
  from ..agents.evaluator_agent import evaluator_node
  from ..agents.adaptation_agent import adaptation_node

  def build_cognarc_graph() -> StateGraph:
      graph = StateGraph(CognarcAgentState)

      graph.add_node("planner", planner_node)
      graph.add_node("task_generator", task_generator_node)
      graph.add_node("evaluator", evaluator_node)
      graph.add_node("adaptation", adaptation_node)

      graph.set_entry_point("planner")
      graph.add_edge("planner", "task_generator")
      graph.add_conditional_edges(
          "task_generator",
          route_after_generation,
          {"evaluator": "evaluator", "end": END},
      )
      graph.add_edge("evaluator", "adaptation")
      graph.add_edge("adaptation", END)

      return graph.compile()

  def route_after_generation(state: CognarcAgentState) -> str:
      if state.get("error") or not state.get("today_quests"):
          return "end"
      return "evaluator"
  ```

### Planner Agent

- [ ] **T2.1** Implement `ai-services/agents/planner_agent/planner.py`:
  ```python
  from groq import Groq
  from ..state import CognarcAgentState

  PLANNER_SYSTEM_PROMPT = """You are the COGNARC Planner Agent.
  Your job: generate a 7-day learning schedule anchored to the user's skill tree.
  Rules:
  - Schedule must respect DAG topology: no child node before parent is mastered
  - Each day: 1 skill focus, 1 difficulty level target, 1 quest type preference
  - Sunday: boss battle review day
  - Account for behavioral signals: if mode=comeback, reduce difficulty
  Output: JSON array of 7 day objects with {day, skill_node, difficulty_target, quest_type_preference}
  Output ONLY valid JSON."""

  async def planner_node(state: CognarcAgentState) -> CognarcAgentState:
      client = Groq()
      context = build_planner_context(state)
      try:
          response = client.chat.completions.create(
              model="mixtral-8x7b-32768",
              messages=[
                  {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
                  {"role": "user", "content": context},
              ],
              max_tokens=1000,
              temperature=0.5,
          )
          weekly_plan = parse_weekly_plan(response.choices[0].message.content)
          return {**state, "weekly_plan": weekly_plan, "error": None}
      except Exception as e:
          return {**state, "error": f"Planner failed: {e}",
                  "retry_count": state.get("retry_count", 0) + 1}
  ```

- [ ] **T2.2** Planner trigger conditions (background cron via Railway):
  - **Sunday night at 11:00 PM user local time** — weekly plan generation
  - **After every boss battle completion** — replan based on mastery confirmation

- [ ] **T2.3** Store planner output: `await mongo.users.update_one({"_id": user_id}, {"$set": {"agent_state.weekly_plan": weekly_plan}})`

### TaskGenerator Agent

- [ ] **T3.1** Implement `ai-services/agents/task_generator_agent/generator.py`:
  ```python
  TASK_GENERATOR_SYSTEM_PROMPT = """You are the COGNARC TaskGenerator Agent.
  Given today's plan from the Planner, generate exactly 3 specific, actionable quest objects.
  Each quest must:
  - Map to the specified skill_node for today
  - Match the difficulty_target from the plan
  - Include real, concrete evaluation_criteria (test cases for coding, rubric for theory)
  - Be unique from recent_quest_summaries (last 7 days)
  Output schema: array of 3 quest objects in full production schema.
  Output ONLY valid JSON."""

  async def task_generator_node(state: CognarcAgentState) -> CognarcAgentState:
      if not state.get("weekly_plan"):
          return {**state, "error": "No weekly plan available"}
      today_plan = get_today_from_plan(state["weekly_plan"])
      context = build_task_context(state, today_plan)
      # Uses Llama-3-70B for richer, more creative quest content
      response = groq_client.chat.completions.create(
          model="llama3-70b-8192",
          messages=[...],
          max_tokens=2000,
      )
      quests = parse_quest_output(response.choices[0].message.content)
      validated_quests = [quest_validator.validate(q, state["skill_state"]) for q in quests]
      return {**state, "today_quests": [q.dict() for q in validated_quests]}
  ```

- [ ] **T3.2** TaskGenerator trigger: **Daily 05:00 AM user local time** (Railway cron job)
- [ ] **T3.3** Output stored in MongoDB: `users.agent_state.today_quests` (TTL 24h via TTL index)
- [ ] **T3.4** Quest Service reads from `users.agent_state.today_quests` first; falls back to single-pipeline Groq if not found

### Evaluator Agent

- [ ] **T4.1** Implement `ai-services/agents/evaluator_agent/evaluator.py`:
  ```python
  EVALUATOR_SYSTEM_PROMPT = """You are the COGNARC Evaluator Agent.
  Review the user's quest submission. Provide structured feedback.
  Note: Pass/fail decision is already determined by test cases. You provide QUALITY FEEDBACK only.
  Evaluate on: approach quality, code elegance, edge case handling, learning depth.
  Output: JSON with {score: float 0-1, feedback: str, hints: list[str], strengths: list[str]}
  Be encouraging but honest. Max 200 words for feedback."""

  async def evaluator_node(state: CognarcAgentState) -> CognarcAgentState:
      # Evaluator only called when there are quest submissions to evaluate
      if not state.get("today_quests"):
          return {**state}

      evaluation_results = []
      for quest in state["today_quests"]:
          if quest.get("submission"):
              result = await evaluate_single_quest(quest, state)
              evaluation_results.append(result)
      return {**state, "evaluation_results": evaluation_results}
  ```

- [ ] **T4.2** Evaluator trigger: `POST /quests/{id}/evaluate` fires evaluation as background task (non-blocking)
- [ ] **T4.3** Evaluator output stored in `progress_logs.ai_evaluation` field (advisory — does not affect XP)

### Adaptation Agent (Pure Python — No LLM)

- [ ] **T5.1** Implement `ai-services/agents/adaptation_agent/adaptation.py`:
  ```python
  def adaptation_node(state: CognarcAgentState) -> CognarcAgentState:
      """
      Pure Python adaptation logic — NO LLM CALL.
      Runs 10 minutes after session end (background task).
      Updates difficulty_modifier and behavioral_profile.
      """
      profile = state["behavioral_profile"]
      signals = analyze_session_signals(state)

      new_modifier = calculate_difficulty_modifier(
          current=profile["difficulty_modifier"],
          signal=signals["primary_signal"],  # boredom|frustration|plateau|normal
      )

      new_profile = {
          **profile,
          "difficulty_modifier": new_modifier,
          "mode": signals["primary_signal"],
          "completion_rate_7d": signals["completion_rate_7d"],
          "preferred_quest_types": signals["emerging_preferences"],
      }

      return {**state, "adaptation_signals": {
          "new_modifier": new_modifier,
          "signal": signals["primary_signal"],
          "profile": new_profile,
      }}

  def analyze_session_signals(state: CognarcAgentState) -> dict:
      """Analyze quest completion patterns to detect behavioral state."""
      recent = state.get("evaluation_results", [])
      if not recent:
          return {"primary_signal": "normal", "completion_rate_7d": 0.0, "emerging_preferences": []}

      avg_time_ratio = mean([r.get("time_ratio", 1.0) for r in recent])
      fail_rate = sum(1 for r in recent if not r.get("passed", True)) / len(recent)

      if avg_time_ratio < 0.5 and len(recent) >= 2:
          signal = "boredom"
      elif fail_rate > 0.6 and len(recent) >= 5:
          signal = "frustration"
      else:
          signal = "normal"

      return {"primary_signal": signal, ...}
  ```

- [ ] **T5.2** Adaptation trigger: background task fired 10 minutes after any session that has > 0 quest completions
- [ ] **T5.3** Adaptation output persisted: `await mongo.users.update_one({"_id": user_id}, {"$set": {"behavioral_profile": new_profile}})`
- [ ] **T5.4** Adaptation NEVER blocks HTTP response. It is always async.

### Agent State Management

- [ ] **T6.1** Add `agent_state` field to MongoDB `users` collection schema:
  ```python
  class AgentState(BaseModel):
      weekly_plan: list[dict] = []
      today_quests: list[dict] = []
      last_planner_run: datetime | None = None
      last_adaptation_run: datetime | None = None
      planner_version: str = "v1"
  ```

- [ ] **T6.2** Create `apps/api/app/repositories/mongo/agent_state_repository.py`:
  - `get_agent_state(user_id) → AgentState`
  - `save_weekly_plan(user_id, plan) → None`
  - `save_today_quests(user_id, quests) → None`
  - `save_behavioral_profile(user_id, profile) → None`

- [ ] **T6.3** Create Railway cron jobs:
  ```yaml
  # railway.json
  {
    "crons": [
      {
        "schedule": "0 23 * * 0",          # Sunday 11PM UTC
        "command": "python -m ai_services.workers.run_planner"
      },
      {
        "schedule": "0 5 * * *",            # Daily 5AM UTC (adjust per user timezone)
        "command": "python -m ai_services.workers.run_task_generator"
      }
    ]
  }
  ```

### Langfuse Observability

- [ ] **T7.1** Initialize Langfuse in all agent nodes:
  ```python
  from langfuse import Langfuse

  langfuse = Langfuse(
      public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
      secret_key=os.environ["LANGFUSE_SECRET_KEY"],
  )

  def traced_planner_node(state: CognarcAgentState) -> CognarcAgentState:
      trace = langfuse.trace(name="planner_agent", user_id=state["user_id"])
      span = trace.span(name="groq_call", model="mixtral-8x7b-32768")
      result = planner_node(state)
      span.end(output={"weekly_plan_days": len(result.get("weekly_plan", []))})
      return result
  ```

- [ ] **T7.2** Log every agent invocation: input context (truncated), output (truncated at 500 chars), latency_ms, success
- [ ] **T7.3** Create Langfuse dashboard: agent latency, success rates, prompt quality scores
- [ ] **T7.4** Configure Langfuse alerts: Planner failure rate > 10% → Slack (P2)

### A/B Testing Framework

- [ ] **T8.1** Implement feature flag: `use_multi_agent_pipeline: bool` per user (10% rollout initially)
- [ ] **T8.2** Quest Service routes to multi-agent or single-pipeline based on flag:
  ```python
  if feature_flags.get("use_multi_agent_pipeline", user_id):
      quests = await agent_state_repository.get_today_quests(user_id, db)
  else:
      quests = await single_pipeline_generate(user_id, db)
  ```
- [ ] **T8.3** Track `user_satisfaction_score` (1–5 rating) per quest — store in `progress_logs`
- [ ] **T8.4** Weekly A/B report: compare mean satisfaction score per cohort in Langfuse

### Personalization Engine

- [ ] **T9.1** Implement `ai-services/behavioral_engine/personalization.py`:
  - Session timing analysis (morning vs evening learner detection)
  - Content style preference (more coding vs more theory)
  - Goal tracking: declared goal (from onboarding) → daily XP target back-calculation
  - Bridge quest generation for plateau detection (5+ days same node, 100% completion)

- [ ] **T9.2** Update onboarding flow to collect: `goal_type` (placement_prep, job_change, upskilling), `daily_time_available_min`
- [ ] **T9.3** Display daily XP target on dashboard: "Today's target: 250 XP (3 quests)"

---

## Data Flow & Dependencies

```
[Sunday 11PM UTC — Railway Cron]
       │
ai_services/workers/run_planner.py
       │
CognarcAgentState(user_id, skill_state, behavioral_profile)
       │
[LangGraph graph.invoke()]
  ├── planner_node()
  │   └── Groq Mixtral-8x7B
  │   └── → weekly_plan (7 days) → MongoDB users.agent_state
  │
  └── [END — Sunday run stops here]

[Daily 5AM UTC — Railway Cron]
       │
[LangGraph graph.invoke()]
  ├── planner_node() [reads existing weekly_plan if not Sunday]
  ├── task_generator_node()
  │   └── Groq Llama-3-70B
  │   └── → today_quests (3 quests) → MongoDB users.agent_state
  └── [END — Quest Service reads from agent_state.today_quests]

[Quest Completion — POST /quests/{id}/evaluate]
       │ (in-request — synchronous)
  XP award + streak update
       │
  BackgroundTasks (10 min delay)
       │
[LangGraph graph.invoke()] — partial run
  ├── evaluator_node() — Groq Mixtral (AI feedback only)
  │   → evaluation_results → progress_logs.ai_evaluation
  └── adaptation_node() — Pure Python
      → new difficulty_modifier → MongoDB users.behavioral_profile

[All nodes] → Langfuse trace → agent latency + quality dashboard
```

---

## Testing & Observability

### Required Tests

| Test | Tool | File | Target |
|---|---|---|---|
| Planner generates 7-day schedule JSON | pytest (mock Groq) | `ai-services/tests/test_planner.py` | 100% |
| TaskGenerator produces 3 valid quest objects | pytest (mock Groq) | `ai-services/tests/test_task_generator.py` | 100% |
| LangGraph graph transitions correctly | pytest | `ai-services/tests/test_graph.py` | 100% |
| `adaptation_node()` updates difficulty on boredom | pytest | `ai-services/tests/test_adaptation.py` | 100% |
| Agent state persists to MongoDB | pytest + TestClient | `tests/integration/test_agent_state.py` | 100% |
| Graph completes within 30s (sync paths) | pytest + timeout | `ai-services/tests/test_graph.py` | 100% |
| Adaptation NEVER blocks HTTP response | pytest | `tests/integration/test_adaptation.py` | 100% |
| A/B flag routes correctly per cohort | pytest | `tests/unit/test_feature_flags.py` | 100% |
| Langfuse trace created per agent run | pytest (langfuse mock) | `ai-services/tests/test_tracing.py` | 90% |

### Observability Stack (Phase 10)

- [ ] Langfuse: full trace for every agent run (planner, task_generator, evaluator, adaptation)
- [ ] Prometheus metrics: agent run count, success rate, latency by agent name
- [ ] Alert: Planner failure rate > 10% over 1h → Slack (P2)
- [ ] Alert: TaskGenerator produces < 3 quests → immediate re-run + fallback to single-pipeline
- [ ] Alert: Adaptation agent takes > 5s → investigate (pure Python should be < 100ms)
- [ ] Weekly Langfuse report: A/B satisfaction scores by cohort

### SLO Targets (Phase 10)

| Metric | Target |
|---|---|
| Planner success rate | > 95% |
| TaskGenerator success rate | > 98% (has single-pipeline fallback) |
| Adaptation latency | < 500ms (pure Python) |
| LangGraph sync path completion | < 30s p95 |
| Langfuse trace coverage | 100% of agent invocations |

---

## Validation Gate

**Phase 10 is DONE when ALL pass:**

```bash
# 1. Planner runs successfully
python -m ai_services.workers.run_planner --user_id=<test_user>
# → MongoDB users.agent_state.weekly_plan has 7 entries

# 2. TaskGenerator runs daily
python -m ai_services.workers.run_task_generator --user_id=<test_user>
# → MongoDB users.agent_state.today_quests has 3 entries

# 3. Quest Service reads from agent state
curl -H "Authorization: Bearer <jwt>" localhost:8000/api/v1/quests/today
# → 3 quests from agent_state (check "generated_by": "langgraph" in response)

# 4. Adaptation fires post-session
# Complete 2 quests in < 50% time each → wait 10 min
# → users.behavioral_profile.difficulty_modifier increased
# → users.behavioral_profile.mode = "boredom"

# 5. LangGraph < 30s
python -c "
import time, asyncio
from ai_services.orchestration.graph import build_cognarc_graph
graph = build_cognarc_graph()
state = {test_state}
start = time.time()
asyncio.run(graph.ainvoke(state))
print(f'Graph time: {time.time() - start:.2f}s')
assert time.time() - start < 30
"

# 6. Langfuse traces visible
# Langfuse dashboard → Traces → filter by last 24h → see planner + task_generator traces

# 7. A/B test data
# After 7 days: Langfuse → compare satisfaction scores per cohort
# Multi-agent cohort shows >= single-pipeline quality

# 8. Full integration test
cd apps/api && pytest tests/ -v  # All green (no regressions)
cd apps/web && npx playwright test  # All green
```

---

## Absolute 'Do-Not-Do' List for Phase 10

| Forbidden | Reason |
|---|---|
| ❌ Start Phase 10 before Phases 6–9 are stable for 30 days | The single biggest project-killer §07 |
| ❌ Import `ai-services/` directly in `apps/api/services/` | Architecture boundary §07 |
| ❌ Agent state stored in memory (not MongoDB) | State must survive restarts §30 |
| ❌ Adaptation Agent using an LLM call | Pure Python only — faster, cheaper, deterministic §07 |
| ❌ Adaptation Agent blocking the HTTP response | Always async + BackgroundTasks §07 |
| ❌ AI awarding XP directly | XP from deterministic engine only §16 |
| ❌ LangGraph graph exceeding 30s on sync paths | Performance SLO §30 |
| ❌ Skipping Langfuse tracing for any agent | All invocations must be traced §19 |
| ❌ Rollout to 100% of users without A/B validation | 10% rollout first, measure quality |
| ❌ Fine-tuning models | Future scope (P3) — not in Phase 4 timeline §30 |
| ❌ Agent bypassing Pydantic validation for quest output | All AI output validated before storage §16 |
| ❌ Prompt injection from user data | Sanitize all user-controlled strings before injection §16 |

---

## Post-Phase 10 Future Scope

| Feature | Priority | Notes |
|---|---|---|
| React Native mobile app (Expo) | P0 | Same API — add haptic feedback, native push |
| Guild/multiplayer system | P0 | 5–10 users, shared boss battles, guild XP |
| AI Tutor Mode | P1 | Per-quest conversational AI — streaming responses |
| Community Quest Marketplace | P1 | User-created quests with AI quality review gate |
| Phi-2 fine-tuning on quest data | P3 | After 100K+ quest completion records |
| Browser extension | P3 | XP goal status in browser toolbar |

---

*Phase 10 Target: Days 46–70 (COGNARC Phase 4 — Agentic AI)*
*Owner: `ai-engineer` (LangGraph + agents) · `backend-architect` (service integration)*
*Completion: Full COGNARC v2.0 Execution Edition delivered*
