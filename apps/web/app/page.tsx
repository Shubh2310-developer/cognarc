import { redirect } from "next/navigation";

/**
 * Root page — redirects to dashboard if authenticated.
 * Unauthenticated users are caught by middleware.ts and redirected to /login.
 */
export default function HomePage() {
  redirect("/dashboard");
}
