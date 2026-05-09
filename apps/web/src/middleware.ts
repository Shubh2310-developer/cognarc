// =============================================================
// COGNARC — Next.js Route-Level Auth Guard
// apps/web/src/middleware.ts
//
// T2.8: Route-level auth guarding — redirect to /login if no session.
// §05: middleware.ts handles auth guard. NEVER replicate in page components.
// §14: MVP — check Supabase session cookie. No OAuth in Phase 1.
// =============================================================

import { NextRequest, NextResponse } from "next/server";
import { createServerClient, type CookieOptions } from "@supabase/ssr";

// ── Route Matchers ────────────────────────────────────────────

const PROTECTED_ROUTES = [
  "/dashboard",
  "/quests",
  "/profile",
  "/settings",
  "/skills",
  "/leaderboard",
  "/analytics",
];

const AUTH_ONLY_ROUTES = ["/login", "/auth/login"];

function isProtectedRoute(pathname: string): boolean {
  return PROTECTED_ROUTES.some((route) => pathname.startsWith(route));
}

function isAuthOnlyRoute(pathname: string): boolean {
  return AUTH_ONLY_ROUTES.some((route) => pathname.startsWith(route));
}

// ── Middleware ────────────────────────────────────────────────

export async function middleware(request: NextRequest): Promise<NextResponse> {
  const { pathname } = request.nextUrl;

  const supabaseUrl = process.env["NEXT_PUBLIC_SUPABASE_URL"] ?? "";
  const supabaseAnonKey = process.env["NEXT_PUBLIC_SUPABASE_ANON_KEY"] ?? "";

  let response = NextResponse.next({
    request: { headers: request.headers },
  });

  if (!isProtectedRoute(pathname) && !isAuthOnlyRoute(pathname)) {
    return response;
  }

  try {
    const supabase = createServerClient(supabaseUrl, supabaseAnonKey, {
      cookies: {
        get(name: string) {
          return request.cookies.get(name)?.value;
        },
        set(name: string, value: string, options: CookieOptions) {
          request.cookies.set(name, value);
          response = NextResponse.next({
            request: { headers: request.headers },
          });
          response.cookies.set(name, value, options);
        },
        remove(name: string, options: CookieOptions) {
          request.cookies.set(name, "");
          response = NextResponse.next({
            request: { headers: request.headers },
          });
          response.cookies.set(name, "", { ...options, maxAge: 0 });
        },
      },
    });

    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (!session && isProtectedRoute(pathname)) {
      const loginUrl = new URL("/login", request.url);
      loginUrl.searchParams.set("next", pathname);
      return NextResponse.redirect(loginUrl);
    }

    if (session && isAuthOnlyRoute(pathname)) {
      return NextResponse.redirect(new URL("/dashboard", request.url));
    }

    return response;
  } catch {
    if (isProtectedRoute(pathname)) {
      return NextResponse.redirect(new URL("/login", request.url));
    }
    return response;
  }
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|robots.txt).*)",
  ],
};
