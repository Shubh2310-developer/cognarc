"use client";

// =============================================================
// COGNARC — Login / Magic Link Auth Page
// apps/web/app/login/page.tsx
//
// Tactical IDE: terminal-style auth interface.
// Phase 1: Supabase magic link only. No OAuth.
// =============================================================

import { useState } from "react";
import { motion } from "framer-motion";
import { Terminal, Zap, ArrowRight, CheckCircle2, AlertCircle } from "lucide-react";

import { sendMagicLink } from "@cognarc/auth-client";

type AuthState = "idle" | "loading" | "sent" | "error";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [authState, setAuthState] = useState<AuthState>("idle");
  const [errorMsg, setErrorMsg] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email.trim() || !email.includes("@")) {
      setErrorMsg("INVALID EMAIL FORMAT");
      setAuthState("error");
      return;
    }

    setAuthState("loading");
    setErrorMsg("");

    const { error } = await sendMagicLink(email);
    if (error) {
      setErrorMsg(error.message.toUpperCase() || "AUTHENTICATION FAILED");
      setAuthState("error");
      return;
    }

    setAuthState("sent");
  }

  return (
    <div
      className="min-h-screen bg-obsidian flex flex-col items-center justify-center px-4 relative overflow-hidden"
      style={{
        backgroundImage: `
          linear-gradient(var(--border-tactical) 1px, transparent 1px),
          linear-gradient(90deg, var(--border-tactical) 1px, transparent 1px)
        `,
        backgroundSize: "32px 32px",
        backgroundPosition: "-1px -1px",
      }}
    >
      {/* ── Background dim overlay ─────────────── */}
      <div className="absolute inset-0 bg-obsidian/80 pointer-events-none" aria-hidden="true" />

      {/* ── Auth Panel ─────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ type: "spring", stiffness: 280, damping: 28 }}
        className="relative z-10 w-full max-w-sm"
        role="main"
        aria-labelledby="auth-heading"
      >
        {/* Top bar — system header */}
        <div className="flex items-center gap-2 bg-gunmetal border border-tactical border-b-0 px-4 py-2">
          <Terminal size={12} className="text-forge" aria-hidden="true" />
          <span className="font-mono text-[10px] tracking-[0.10em] uppercase text-muted">
            COGNARC AUTH — SESSION INIT
          </span>
          <div className="ml-auto flex items-center gap-1.5">
            <div className="w-2 h-2 bg-[#FF4444]" aria-hidden="true" />
            <div className="w-2 h-2 bg-[#FFB800]" aria-hidden="true" />
            <div className="w-2 h-2 bg-volt" aria-hidden="true" />
          </div>
        </div>

        {/* Main form panel */}
        <div className="bg-gunmetal border border-tactical p-8">

          {/* Wordmark */}
          <div className="flex flex-col items-center mb-8">
            <div className="flex items-center gap-2 mb-3">
              <Zap size={20} className="text-forge" aria-hidden="true" />
              <span className="font-space-grotesk text-[22px] font-700 tracking-[-0.03em] text-bright uppercase">
                COGNARC
              </span>
            </div>
            <p className="font-mono text-[10px] tracking-[0.12em] uppercase text-muted">
              Tactical Skill OS
            </p>

            {/* Divider */}
            <div className="w-full h-px bg-tactical mt-6" />
          </div>

          {authState !== "sent" ? (
            <>
              <div className="mb-6">
                <h1
                  id="auth-heading"
                  className="font-space-grotesk text-[18px] font-600 text-bright mb-1"
                >
                  Access Terminal
                </h1>
                <p className="font-sans text-[12px] text-muted">
                  Enter your operator email. A secure magic link will be dispatched.
                </p>
              </div>

              <form onSubmit={handleSubmit} noValidate>
                {/* Email input */}
                <div className="mb-4">
                  <label
                    htmlFor="email-input"
                    className="block font-mono text-[9px] tracking-[0.12em] uppercase text-muted mb-2"
                  >
                    Operator Email
                  </label>
                  <input
                    id="email-input"
                    type="email"
                    value={email}
                    onChange={e => { setEmail(e.target.value); setAuthState("idle"); }}
                    placeholder="operator@domain.io"
                    autoComplete="email"
                    autoFocus
                    className="w-full bg-obsidian border border-tactical text-bright font-mono text-[13px] px-3 py-2.5 outline-none placeholder:text-muted focus:border-forge transition-colors duration-100"
                    aria-describedby={authState === "error" ? "auth-error" : undefined}
                    aria-invalid={authState === "error"}
                  />
                </div>

                {/* Error message */}
                {authState === "error" && (
                  <motion.div
                    initial={{ opacity: 0, y: -4 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ type: "spring", stiffness: 400, damping: 30 }}
                    id="auth-error"
                    role="alert"
                    className="flex items-center gap-2 mb-4 px-3 py-2 bg-obsidian border border-[#FF4444]"
                  >
                    <AlertCircle size={11} className="text-[#FF4444] shrink-0" aria-hidden="true" />
                    <span className="font-mono text-[10px] tracking-[0.06em] text-[#FF4444]">
                      {errorMsg}
                    </span>
                  </motion.div>
                )}

                {/* Submit button */}
                <motion.button
                  type="submit"
                  disabled={authState === "loading" || !email.trim()}
                  whileTap={{ scale: 0.98 }}
                  transition={{ type: "spring", stiffness: 400, damping: 30 }}
                  className="w-full flex items-center justify-center gap-2 bg-forge text-obsidian border border-forge font-mono text-[11px] font-700 tracking-[0.10em] uppercase py-3 hover:bg-[#E55F00] hover:border-[#E55F00] disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-100"
                  aria-label="Request magic link"
                >
                  {authState === "loading" ? (
                    <>
                      <motion.span
                        animate={{ opacity: [1, 0.3, 1] }}
                        transition={{ repeat: Infinity, duration: 0.6, ease: "linear" }}
                        aria-hidden="true"
                      >
                        ▐
                      </motion.span>
                      Dispatching Link…
                    </>
                  ) : (
                    <>
                      <ArrowRight size={12} aria-hidden="true" />
                      Request Magic Link
                    </>
                  )}
                </motion.button>
              </form>
            </>
          ) : (
            /* ── Sent State ─────────────────────── */
            <motion.div
              initial={{ opacity: 0, scale: 0.97 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
              className="text-center"
              role="status"
              aria-label="Magic link sent"
            >
              <div className="flex justify-center mb-4">
                <div className="border-2 border-volt p-3">
                  <CheckCircle2 size={24} className="text-volt" aria-hidden="true" />
                </div>
              </div>
              <h2 className="font-space-grotesk text-[18px] font-600 text-volt mb-2">
                Link Dispatched
              </h2>
              <p className="font-sans text-[13px] text-muted mb-6 leading-relaxed">
                A secure link has been sent to{" "}
                <span className="font-mono text-bright text-[12px]">{email}</span>.
                <br />Check your inbox and click to authenticate.
              </p>
              <button
                onClick={() => { setAuthState("idle"); setEmail(""); }}
                className="font-mono text-[10px] tracking-[0.10em] uppercase text-muted border border-tactical px-4 py-2 hover:border-muted hover:text-bright transition-colors duration-100"
              >
                Use Different Email
              </button>
            </motion.div>
          )}
        </div>

        {/* Footer note */}
        <div className="bg-obsidian border border-tactical border-t-0 px-4 py-2 text-center">
          <span className="font-mono text-[10px] text-muted">
            No password. No OAuth. Just the link. Phase 1 auth.
          </span>
        </div>
      </motion.div>
    </div>
  );
}
