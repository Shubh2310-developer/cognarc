-- =============================================================
-- COGNARC — Initial Supabase Schema Migration
-- infrastructure/supabase/migrations/001_initial_schema.sql
--
-- T5.1: Creates public.leaderboard, public.achievements, public.boss_battles
-- T5.2: Row Level Security (RLS) policies on all tables.
--
-- Rules:
--   • NEVER modify auth.users (managed by Supabase).
--   • public.achievements is INSERT-ONLY — no UPDATE or DELETE ever.
--   • public.leaderboard is refreshed as a materialized-view-like table.
--   • Run this in Supabase Studio → SQL Editor or via supabase db push.
-- =============================================================

-- ── Extensions ───────────────────────────────────────────────
-- gen_random_uuid() requires pgcrypto (enabled by default in Supabase)
-- No additional extensions needed for MVP.

-- ── 1. Leaderboard Table ─────────────────────────────────────
-- Materialized-view-like table refreshed every 15 minutes by background job.
-- Source of truth for top-100 XP ranking.
-- §08: Supabase table — do NOT write XP here directly; copy from MongoDB.

CREATE TABLE IF NOT EXISTS public.leaderboard (
    user_id     UUID        PRIMARY KEY,
    username    TEXT        NOT NULL,
    total_xp    INTEGER     NOT NULL DEFAULT 0,
    current_level INTEGER   NOT NULL DEFAULT 1,
    streak      INTEGER     NOT NULL DEFAULT 0,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS leaderboard_total_xp_idx
    ON public.leaderboard (total_xp DESC);

COMMENT ON TABLE public.leaderboard IS
    'Materialized-view-like table for top-100 XP leaderboard. Refreshed every 15 min.';

-- ── 2. Achievements Table ─────────────────────────────────────
-- Insert-only. NEVER UPDATE or DELETE achievement records (§08).
-- Immutable audit log of earned badges.

CREATE TABLE IF NOT EXISTS public.achievements (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID        NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    badge_id    TEXT        NOT NULL,
    badge_name  TEXT        NOT NULL,
    earned_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    xp_bonus    INTEGER     NOT NULL DEFAULT 0,

    -- Prevent duplicate badge awards per user
    CONSTRAINT achievements_user_badge_unique UNIQUE (user_id, badge_id)
);

CREATE INDEX IF NOT EXISTS achievements_user_id_idx
    ON public.achievements (user_id, earned_at DESC);

COMMENT ON TABLE public.achievements IS
    'Immutable achievement/badge records. INSERT-ONLY — never UPDATE or DELETE.';

-- ── 3. Boss Battles Table ─────────────────────────────────────
-- Records boss battle attempts per user per week.
-- Status enum: in_progress | passed | failed.

CREATE TABLE IF NOT EXISTS public.boss_battles (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID        NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    week_of         DATE        NOT NULL,
    status          TEXT        NOT NULL DEFAULT 'in_progress'
                                CHECK (status IN ('in_progress', 'passed', 'failed')),
    score           NUMERIC(5, 2),
    time_taken_min  INTEGER,
    xp_awarded      INTEGER     NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- One attempt per user per week (re-attempt creates new row for stats)
    CONSTRAINT boss_battles_user_week_unique UNIQUE (user_id, week_of)
);

CREATE INDEX IF NOT EXISTS boss_battles_user_id_idx
    ON public.boss_battles (user_id, week_of DESC);

CREATE INDEX IF NOT EXISTS boss_battles_status_idx
    ON public.boss_battles (status);

COMMENT ON TABLE public.boss_battles IS
    'Boss battle attempt log per user per week. Status: in_progress | passed | failed.';

-- =============================================================
-- T5.2: Row Level Security Policies
-- Rule: users can only read/write their own records.
-- Service role key bypasses RLS (used by backend API only).
-- =============================================================

-- ── Enable RLS on all tables ──────────────────────────────────
ALTER TABLE public.leaderboard  ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.achievements ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.boss_battles ENABLE ROW LEVEL SECURITY;

-- ── Leaderboard Policies ──────────────────────────────────────
-- Anyone authenticated can read the leaderboard (public ranking).
-- Only the service role (backend API) can write to leaderboard.

CREATE POLICY IF NOT EXISTS "leaderboard_select_authenticated"
    ON public.leaderboard
    FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY IF NOT EXISTS "leaderboard_all_service_role"
    ON public.leaderboard
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ── Achievements Policies ─────────────────────────────────────
-- Users can SELECT only their own achievements.
-- INSERT allowed for own rows (service role inserts on completion).
-- UPDATE and DELETE are NEVER allowed (enforced by no policy grant).

CREATE POLICY IF NOT EXISTS "achievements_select_own"
    ON public.achievements
    FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

CREATE POLICY IF NOT EXISTS "achievements_insert_service_role"
    ON public.achievements
    FOR INSERT
    TO service_role
    WITH CHECK (true);

-- ── Boss Battles Policies ─────────────────────────────────────
-- Users can SELECT their own battle records.
-- INSERT and UPDATE allowed for own records.

CREATE POLICY IF NOT EXISTS "boss_battles_select_own"
    ON public.boss_battles
    FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

CREATE POLICY IF NOT EXISTS "boss_battles_insert_own"
    ON public.boss_battles
    FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY IF NOT EXISTS "boss_battles_update_own"
    ON public.boss_battles
    FOR UPDATE
    TO authenticated
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY IF NOT EXISTS "boss_battles_all_service_role"
    ON public.boss_battles
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- =============================================================
-- Validation: After running this migration, verify in Supabase Studio:
--   • Tables: leaderboard, achievements, boss_battles exist in public schema
--   • RLS: Enabled on all three tables
--   • Policies: Listed in Auth → Policies for each table
-- =============================================================
