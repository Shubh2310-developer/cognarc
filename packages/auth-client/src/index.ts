// =============================================================
// COGNARC — Supabase Auth Client Wrapper
// packages/auth-client/src/index.ts
//
// T2.7: Next.js Supabase client wrapper (magic link flow).
// §14: MVP auth = Supabase magic link only. No OAuth in Phase 1.
// §17: Never make raw fetch from components. Use this wrapper.
// =============================================================

import { createClient, SupabaseClient, Session, User } from "@supabase/supabase-js";

// ── Client Factory ────────────────────────────────────────────

let _client: SupabaseClient | null = null;

/**
 * Return a singleton Supabase browser client.
 * Uses NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY.
 * Call this in Client Components only.
 */
export function getSupabaseClient(): SupabaseClient {
  if (_client) return _client;

  const supabaseUrl = process.env["NEXT_PUBLIC_SUPABASE_URL"];
  const supabaseAnonKey = process.env["NEXT_PUBLIC_SUPABASE_ANON_KEY"];

  if (!supabaseUrl || !supabaseAnonKey) {
    throw new Error(
      "Missing NEXT_PUBLIC_SUPABASE_URL or NEXT_PUBLIC_SUPABASE_ANON_KEY environment variables"
    );
  }

  _client = createClient(supabaseUrl, supabaseAnonKey, {
    auth: {
      autoRefreshToken: true,
      persistSession: true,
      detectSessionInUrl: true,
    },
  });

  return _client;
}

// ── Auth Actions ──────────────────────────────────────────────

/**
 * Send a magic link email to the user.
 * §14: MVP auth method — magic link only.
 */
export async function sendMagicLink(email: string): Promise<{ error: Error | null }> {
  const client = getSupabaseClient();
  const { error } = await client.auth.signInWithOtp({
    email,
    options: {
      shouldCreateUser: true,
      emailRedirectTo: `${window.location.origin}/auth/callback`,
    },
  });
  return { error: error as Error | null };
}

/**
 * Sign out the current user.
 * Clears the session from local storage.
 */
export async function signOut(): Promise<{ error: Error | null }> {
  const client = getSupabaseClient();
  const { error } = await client.auth.signOut();
  return { error: error as Error | null };
}

/**
 * Get the current active session.
 * Returns null if no session exists.
 */
export async function getSession(): Promise<Session | null> {
  const client = getSupabaseClient();
  const { data } = await client.auth.getSession();
  return data.session;
}

/**
 * Get the current authenticated user.
 * Returns null if not authenticated.
 */
export async function getCurrentUser(): Promise<User | null> {
  const session = await getSession();
  return session?.user ?? null;
}

/**
 * Get the current access token (JWT).
 * Returns null if not authenticated.
 */
export async function getAccessToken(): Promise<string | null> {
  const session = await getSession();
  return session?.access_token ?? null;
}

/**
 * Subscribe to auth state changes.
 * Use in layout components to react to login/logout.
 */
export function onAuthStateChange(
  callback: (event: string, session: Session | null) => void
): { unsubscribe: () => void } {
  const client = getSupabaseClient();
  const { data: subscription } = client.auth.onAuthStateChange(callback);
  return { unsubscribe: () => subscription.subscription.unsubscribe() };
}

// Re-export types for convenience
export type { Session, User, SupabaseClient };
