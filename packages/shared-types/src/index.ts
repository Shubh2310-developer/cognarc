// =============================================================
// COGNARC — Shared TypeScript Type Definitions
// packages/shared-types/src/index.ts
// ALL canonical types live here. NEVER duplicate in apps/.
// Phase 02 — DATA MODELING: synced with Python Pydantic schemas.
// =============================================================

// ── Identity ─────────────────────────────────────────────────

export type UserId = string;
export type QuestId = string;
export type SkillNodeId = string;

// ── Enums ────────────────────────────────────────────────────

export type QuestDifficulty = "easy" | "medium" | "hard" | "boss";
export type QuestType = "theory" | "coding" | "debug" | "build" | "research";
export type QuestStatus = "pending" | "completed" | "skipped" | "failed";
export type SkillStatus = "locked" | "available" | "in_progress" | "mastered";
export type BehavioralMode = "normal" | "comeback" | "boredom" | "frustration";
export type EvaluationMethod = "code_submission" | "self_report" | "theory_qa";
export type QuestProvider = "groq" | "phi2" | "cached";

// ── User — Skill State ────────────────────────────────────────

/**
 * T1.1 mirror: SkillState (Python: app.models.user.SkillState)
 * Progress state for a single skill tree node set.
 */
export interface SkillState {
  current_node: SkillNodeId;
  node_progress: number; // 0.0–1.0
  mastered_nodes: SkillNodeId[];
  unlocked_nodes: SkillNodeId[];
  locked_nodes: SkillNodeId[];
}

// ── User — Behavioral Profile ────────────────────────────────

/**
 * T1.1 mirror: BehavioralProfile (Python: app.models.user.BehavioralProfile)
 * Adaptive difficulty signals updated by the Adaptation engine.
 */
export interface BehavioralProfile {
  difficulty_modifier: number; // 0.5–2.0 adaptive multiplier
  preferred_quest_types: QuestType[];
  completion_rate_7d: number; // 0.0–1.0
  mode: BehavioralMode;
  avg_time_per_quest_min: number;
  boredom_signal: number; // 0–10
  frustration_signal: number; // 0–10
}

// ── User — Settings ───────────────────────────────────────────

/**
 * T1.1 mirror: UserSettings (Python: app.models.user.UserSettings)
 */
export interface UserSettings {
  timezone: string;
  theme: "dark" | "light";
  daily_goal_quests: number;
  notifications_enabled: boolean;
}

// ── User — Full Profile ───────────────────────────────────────

/**
 * T2.1 mirror: UserResponse (Python: app.schemas.user_schemas.UserResponse)
 * GET /users/me response shape.
 */
export interface UserProfile {
  id: UserId; // MongoDB _id as string
  auth_id: string; // Supabase auth.users UUID
  username: string;
  email: string;
  avatar_url: string | null;
  level: number;
  total_xp: number; // Cumulative, never decreases
  active_skill_tree: string;
  skill_state: Record<string, SkillState>; // skill_tree_id → SkillState
  behavioral_profile: BehavioralProfile;
  settings: UserSettings;
  created_at: string; // ISO 8601
  updated_at: string; // ISO 8601
}

/**
 * T2.1 mirror: UserProfileResponse (Python: app.schemas.user_schemas.UserProfileResponse)
 * Minimal public profile for leaderboard/social viewing.
 */
export interface UserProfilePublic {
  id: UserId;
  username: string;
  avatar_url: string | null;
  level: number;
  total_xp: number;
  active_skill_tree: string;
}

// ── User — Request Shapes ─────────────────────────────────────

export interface UserCreateRequest {
  auth_id: string;
  username: string;
  email: string;
  active_skill_tree?: string;
  timezone?: string;
}

export interface UserUpdateRequest {
  username?: string;
  avatar_url?: string;
  settings?: Partial<UserSettings>;
  active_skill_tree?: string;
}

// ── Quest — Evaluation Criteria ───────────────────────────────

/**
 * T1.2 mirror: EvaluationCriteria (Python: app.models.quest.EvaluationCriteria)
 */
export interface EvaluationCriteria {
  type: EvaluationMethod;
  test_cases: number; // count
  pass_threshold: number; // 0.0–1.0
}

// ── Quest ─────────────────────────────────────────────────────

/**
 * T1.2 / T2.2 mirror: Quest → QuestResponse
 * (Python: app.models.quest.Quest / app.schemas.quest_schemas.QuestResponse)
 */
export interface Quest {
  id: QuestId; // MongoDB _id as string
  quest_id: string; // q_<uuid4_short>
  user_id: UserId;
  date: string; // ISO 8601 datetime
  title: string;
  description: string;
  type: QuestType;
  difficulty: QuestDifficulty;
  estimated_minutes: number;
  xp_reward: number;
  skill_node: SkillNodeId;
  skill_tree: string;
  evaluation_criteria: EvaluationCriteria;
  hints: string[];
  status: QuestStatus;
  generated_by: QuestProvider;
  created_at: string;
  completed_at: string | null;
}

/**
 * T2.2 mirror: QuestListResponse
 */
export interface QuestListResponse {
  quests: Quest[];
  total: number;
  date: string; // YYYY-MM-DD
}

/**
 * T2.2 mirror: QuestStatusUpdateRequest
 */
export interface QuestStatusUpdateRequest {
  status: "completed" | "skipped" | "failed";
  time_taken_min: number;
  evaluation_score?: number | null;
  self_reported: boolean;
}

/**
 * T2.2 mirror: QuestGenerateRequest
 */
export interface QuestGenerateRequest {
  skill_tree?: string;
  count?: number;
}

// ── Progress ─────────────────────────────────────────────────

/**
 * T1.3 / T2.3 mirror: ProgressLog → ProgressLogResponse
 * (Python: app.models.progress_log.ProgressLog / app.schemas.progress_schemas.ProgressLogResponse)
 */
export interface ProgressLog {
  id: string; // MongoDB _id as string
  user_id: UserId;
  quest_id: QuestId;
  completed_at: string; // ISO 8601
  xp_earned: number;
  time_taken_min: number;
  evaluation_score: number | null; // 0–100
  evaluation_method: string;
  created_at: string;
}

// ── Streak ────────────────────────────────────────────────────

/**
 * T1.4 / T2.3 mirror: Streak → StreakResponse
 * (Python: app.models.streak.Streak / app.schemas.progress_schemas.StreakResponse)
 */
export interface StreakState {
  user_id: UserId;
  current_streak: number;
  longest_streak: number;
  last_completion_date: string | null; // YYYY-MM-DD
  shield_count: number;
}

// ── Gamification ─────────────────────────────────────────────

export interface GamificationState {
  user_id: UserId;
  level: number;
  total_xp: number;
  xp_for_current_level: number;
  xp_for_next_level: number;
  xp_progress_pct: number; // 0–100
  streak: StreakState;
}

// ── API Response Wrappers ─────────────────────────────────────

export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface ApiError {
  detail: string;
  code?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  has_next: boolean;
}

// ── Supabase Tables (Phase 3) ─────────────────────────────────

/**
 * Supabase public.leaderboard row shape.
 * T5.1 mirror: infrastructure/supabase/migrations/001_initial_schema.sql
 */
export interface LeaderboardEntry {
  user_id: string; // UUID
  username: string;
  total_xp: number;
  current_level: number;
  streak: number;
  updated_at: string;
}

/**
 * Supabase public.achievements row shape.
 * Insert-only table — NEVER update or delete.
 */
export interface Achievement {
  id: string; // UUID
  user_id: string; // UUID
  badge_id: string;
  badge_name: string;
  earned_at: string;
  xp_bonus: number;
}

/**
 * Supabase public.boss_battles row shape.
 */
export interface BossBattle {
  id: string;
  user_id: string;
  week_of: string; // YYYY-MM-DD
  status: "in_progress" | "passed" | "failed";
  score: number | null;
  time_taken_min: number | null;
  xp_awarded: number;
  created_at: string;
}
