-- VIRTUS FIT Stage 1: shared workout ledger
-- Safe additive migration. Existing workouts_strength rows are preserved as legacy aggregates.
-- New tables are intentionally restricted to the server-side service_role until Mini App
-- requests are routed through a Telegram initData-verifying backend.

BEGIN;

CREATE TABLE IF NOT EXISTS public.workout_sessions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id bigint NOT NULL REFERENCES public.users(user_id) ON DELETE CASCADE,
    started_at timestamptz NOT NULL DEFAULT now(),
    finished_at timestamptz,
    source text NOT NULL CHECK (source IN ('bot', 'miniapp')),
    program_id bigint REFERENCES public.saved_programs(id) ON DELETE SET NULL,
    status text NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'completed', 'abandoned')),
    CONSTRAINT workout_sessions_finished_after_start
        CHECK (finished_at IS NULL OR finished_at >= started_at)
);

CREATE INDEX IF NOT EXISTS workout_sessions_user_started_idx
    ON public.workout_sessions (user_id, started_at DESC);

CREATE INDEX IF NOT EXISTS workout_sessions_status_idx
    ON public.workout_sessions (status, started_at DESC);

CREATE TABLE IF NOT EXISTS public.workout_sets (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id uuid NOT NULL
        REFERENCES public.workout_sessions(id) ON DELETE CASCADE,
    exercise_order integer NOT NULL CHECK (exercise_order >= 0),
    set_index integer NOT NULL CHECK (set_index >= 1),
    exercise_key text NOT NULL CHECK (length(trim(exercise_key)) > 0),
    exercise_name text NOT NULL CHECK (length(trim(exercise_name)) > 0),
    muscle_group text NOT NULL DEFAULT 'core',
    set_type text NOT NULL DEFAULT 'working'
        CHECK (set_type IN ('warmup', 'working', 'drop')),
    reps integer NOT NULL CHECK (reps > 0),
    weight_kg numeric(8,2) NOT NULL DEFAULT 0 CHECK (weight_kg >= 0),
    rir smallint CHECK (rir IS NULL OR rir BETWEEN 0 AND 5),
    completed boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT workout_sets_one_row_per_set
        UNIQUE (session_id, exercise_order, set_index)
);

CREATE INDEX IF NOT EXISTS workout_sets_session_idx
    ON public.workout_sets (session_id, exercise_order, set_index);

CREATE INDEX IF NOT EXISTS workout_sets_exercise_created_idx
    ON public.workout_sets (exercise_key, created_at DESC);

-- Add an idempotent legacy aggregate link so retrying session finalization
-- updates the same dashboard row instead of creating duplicate aggregates.
ALTER TABLE public.workouts_strength
    ADD COLUMN IF NOT EXISTS session_id uuid
        REFERENCES public.workout_sessions(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS exercise_order integer;

DO $migration$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'public.workouts_strength'::regclass
          AND conname = 'workouts_strength_session_exercise_unique'
    ) THEN
        ALTER TABLE public.workouts_strength
            ADD CONSTRAINT workouts_strength_session_exercise_unique
            UNIQUE (session_id, exercise_order);
    END IF;
END;
$migration$;

CREATE INDEX IF NOT EXISTS workouts_strength_user_created_idx
    ON public.workouts_strength (user_id, created_at DESC);

CREATE TABLE IF NOT EXISTS public.exercise_progression (
    user_id bigint NOT NULL REFERENCES public.users(user_id) ON DELETE CASCADE,
    exercise_key text NOT NULL CHECK (length(trim(exercise_key)) > 0),
    exercise_name text NOT NULL,
    muscle_group text NOT NULL DEFAULT 'core',
    last_session_id uuid REFERENCES public.workout_sessions(id) ON DELETE SET NULL,
    last_weight numeric(8,2) CHECK (last_weight IS NULL OR last_weight >= 0),
    target_reps_min integer NOT NULL DEFAULT 8 CHECK (target_reps_min > 0),
    target_reps_max integer NOT NULL DEFAULT 12
        CHECK (target_reps_max >= target_reps_min),
    increment_kg numeric(6,2) NOT NULL DEFAULT 2.50
        CHECK (increment_kg > 0),
    next_suggested_weight numeric(8,2)
        CHECK (next_suggested_weight IS NULL OR next_suggested_weight >= 0),
    failed_sessions_streak integer NOT NULL DEFAULT 0
        CHECK (failed_sessions_streak >= 0),
    updated_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, exercise_key)
);

CREATE INDEX IF NOT EXISTS exercise_progression_user_idx
    ON public.exercise_progression (user_id);

-- New workout data is never exposed through the public/publishable client.
-- The Telegram bot uses the server-side Supabase secret key.
ALTER TABLE public.workout_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.workout_sets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.exercise_progression ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE
    public.workout_sessions,
    public.workout_sets,
    public.exercise_progression
FROM PUBLIC, anon, authenticated;

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE
    public.workout_sessions,
    public.workout_sets,
    public.exercise_progression
TO service_role;

COMMENT ON TABLE public.workout_sessions IS
    'Canonical workout sessions shared by Telegram bot and Mini App.';
COMMENT ON TABLE public.workout_sets IS
    'One row per actually completed set; source of truth for strength history.';
COMMENT ON TABLE public.exercise_progression IS
    'Deterministic per-user exercise progression state; no AI inference.';

COMMIT;
