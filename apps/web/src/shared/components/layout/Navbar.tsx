"use client";

// =============================================================
// COGNARC — Tactical Top Navbar
// src/shared/components/layout/Navbar.tsx
//
// Industrial: breadcrumb path, system clock, user telemetry.
// No glassmorphism. No shadows. Bottom border only.
// =============================================================

import { useEffect, useState } from "react";
import { Bell, Wifi, WifiOff, Activity } from "lucide-react";

interface NavbarProps {
  pageName?: string;
  userName?: string;
  online?: boolean;
  notificationCount?: number;
}

function SystemClock() {
  const [time, setTime] = useState("");

  useEffect(() => {
    const update = () =>
      setTime(new Date().toLocaleTimeString("en-US", {
        hour12: false,
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      }));
    update();
    const id = setInterval(update, 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <time
      dateTime={new Date().toISOString()}
      className="font-mono text-[12px] text-muted tracking-[0.06em]"
      aria-label="Current time"
    >
      {time}
    </time>
  );
}

export function Navbar({
  pageName = "Dashboard",
  userName = "OPERATOR",
  online = true,
  notificationCount = 0,
}: NavbarProps) {
  return (
    <header
      className="flex items-center justify-between h-[56px] px-4 bg-obsidian border-b border-tactical"
      role="banner"
    >
      {/* ── Left: breadcrumb ─────────────────── */}
      <div className="flex items-center gap-2">
        <span className="font-mono text-[11px] text-muted tracking-[0.06em]">
          COGNARC
        </span>
        <span className="text-tactical font-mono text-[11px]">/</span>
        <span className="font-space-grotesk text-[13px] font-600 text-bright tracking-[-0.01em]">
          {pageName}
        </span>
      </div>

      {/* ── Right: telemetry strip ───────────── */}
      <div className="flex items-center gap-4">
        {/* System status */}
        <div className="flex items-center gap-1.5" aria-label="System status">
          <Activity size={10} className="text-volt" aria-hidden="true" />
          <span className="font-mono text-[10px] tracking-[0.08em] uppercase text-volt">
            LIVE
          </span>
        </div>

        {/* Clock */}
        <SystemClock />

        {/* Connectivity */}
        <div
          className="flex items-center gap-1"
          aria-label={online ? "Online" : "Offline"}
          title={online ? "Connected" : "Offline mode"}
        >
          {online ? (
            <Wifi size={12} className="text-volt" aria-hidden="true" />
          ) : (
            <WifiOff size={12} className="text-[#FF4444]" aria-hidden="true" />
          )}
        </div>

        {/* Divider */}
        <div className="h-4 w-px bg-tactical" aria-hidden="true" />

        {/* Notifications */}
        <button
          className="relative flex items-center justify-center w-8 h-8 border border-transparent hover:border-tactical hover:bg-gunmetal transition-colors duration-100 text-muted hover:text-bright"
          aria-label={`Notifications${notificationCount > 0 ? ` (${notificationCount} unread)` : ""}`}
        >
          <Bell size={13} aria-hidden="true" />
          {notificationCount > 0 && (
            <span
              className="absolute top-1 right-1 w-1.5 h-1.5 bg-forge"
              aria-hidden="true"
            />
          )}
        </button>

        {/* User identity */}
        <div
          className="flex items-center gap-2 pl-3 border-l border-tactical"
          aria-label={`Logged in as ${userName}`}
        >
          <div className="w-6 h-6 bg-forge flex items-center justify-center" aria-hidden="true">
            <span className="font-mono text-[9px] font-700 text-obsidian">
              {userName.charAt(0).toUpperCase()}
            </span>
          </div>
          <span className="font-mono text-[11px] tracking-[0.06em] text-muted uppercase hidden sm:block">
            {userName}
          </span>
        </div>
      </div>
    </header>
  );
}
