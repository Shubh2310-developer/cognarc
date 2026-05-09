"use client";

// =============================================================
// COGNARC — Tactical Sidebar Navigation
// src/shared/components/layout/Sidebar.tsx
//
// Industrial Blueprint: sharp edges, icon+label nav, mono type.
// No glassmorphism. No shadows. 1px border separation.
// =============================================================

import { motion } from "framer-motion";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Swords,
  Map,
  Trophy,
  BarChart2,
  Settings,
  LogOut,
  Terminal,
  Cpu,
} from "lucide-react";
import { clsx } from "clsx";

interface NavItem {
  href: string;
  label: string;
  icon: React.ElementType;
  badge?: string | number;
  phase?: number;  // Phase required — dims if not yet available
}

const NAV_PRIMARY: NavItem[] = [
  { href: "/dashboard", label: "HQ",          icon: LayoutDashboard },
  { href: "/quests",    label: "Quests",       icon: Swords           },
  { href: "/skills",    label: "Skill Tree",   icon: Map              },
  { href: "/battles",   label: "Battles",      icon: Trophy, phase: 3 },
  { href: "/analytics", label: "Analytics",    icon: BarChart2        },
];

const NAV_SECONDARY: NavItem[] = [
  { href: "/settings",  label: "Settings",     icon: Settings         },
];

interface SidebarProps {
  userLevel?: number;
  streakCount?: number;
  onLogout?: () => void;
}

export function Sidebar({ userLevel = 1, streakCount = 0, onLogout }: SidebarProps) {
  const pathname = usePathname();

  return (
    <aside
      className="flex flex-col h-full w-[56px] bg-obsidian border-r border-tactical"
      aria-label="Primary navigation"
    >
      {/* ── Logo / Wordmark ─────────────────────── */}
      <div className="flex items-center justify-center h-[56px] border-b border-tactical">
        <div className="flex flex-col items-center gap-0.5">
          <Terminal size={16} className="text-forge" aria-hidden="true" />
          <span className="font-mono text-[8px] font-700 tracking-[0.12em] text-forge uppercase">
            CGN
          </span>
        </div>
      </div>

      {/* ── Primary Nav ─────────────────────────── */}
      <nav className="flex-1 flex flex-col items-center gap-1 py-4" aria-label="Main navigation">
        {NAV_PRIMARY.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
          const Icon = item.icon;
          const isLocked = !!item.phase;  // MVP: dim phase-gated items

          return (
            <Link
              key={item.href}
              href={isLocked ? "#" : item.href}
              aria-label={item.label + (isLocked ? " (Coming soon)" : "")}
              aria-current={isActive ? "page" : undefined}
              className={clsx(
                "relative group flex flex-col items-center justify-center",
                "w-10 h-10",
                "transition-colors duration-100",
                "border",
                isActive
                  ? "bg-gunmetal border-forge text-forge"
                  : "border-transparent text-muted hover:text-bright hover:border-tactical hover:bg-gunmetal",
                isLocked && "opacity-30 cursor-not-allowed",
              )}
              onClick={isLocked ? (e) => e.preventDefault() : undefined}
            >
              <Icon size={15} aria-hidden="true" />

              {/* Active indicator bar */}
              {isActive && (
                <motion.div
                  layoutId="sidebar-active"
                  className="absolute left-0 top-0 bottom-0 w-[2px] bg-forge"
                  transition={{ type: "spring", stiffness: 400, damping: 35 }}
                  aria-hidden="true"
                />
              )}

              {/* Tooltip */}
              <div
                className="absolute left-full ml-2 px-2 py-1 bg-gunmetal border border-tactical whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity duration-100 pointer-events-none z-50"
                role="tooltip"
              >
                <span className="font-mono text-[10px] tracking-[0.08em] text-bright">
                  {item.label}
                </span>
              </div>
            </Link>
          );
        })}
      </nav>

      {/* ── Bottom Section ───────────────────────── */}
      <div className="flex flex-col items-center gap-1 pb-4 border-t border-tactical pt-4">
        {/* Level indicator */}
        <div
          className="flex flex-col items-center justify-center w-10 h-10 border border-tactical bg-gunmetal"
          aria-label={`Level ${userLevel}`}
        >
          <Cpu size={10} className="text-muted mb-0.5" aria-hidden="true" />
          <span className="font-mono text-[10px] font-700 text-forge">
            {userLevel.toString().padStart(2, "0")}
          </span>
        </div>

        {/* Settings */}
        {NAV_SECONDARY.map((item) => {
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              aria-label={item.label}
              className="group relative flex items-center justify-center w-10 h-10 border border-transparent text-muted hover:text-bright hover:border-tactical hover:bg-gunmetal transition-colors duration-100"
            >
              <Icon size={15} aria-hidden="true" />
              <div
                className="absolute left-full ml-2 px-2 py-1 bg-gunmetal border border-tactical whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity duration-100 pointer-events-none z-50"
                role="tooltip"
              >
                <span className="font-mono text-[10px] tracking-[0.08em] text-bright">
                  {item.label}
                </span>
              </div>
            </Link>
          );
        })}

        {/* Logout */}
        <button
          onClick={onLogout}
          aria-label="Log out"
          className="group relative flex items-center justify-center w-10 h-10 border border-transparent text-muted hover:text-[#FF4444] hover:border-[#FF4444] transition-colors duration-100"
        >
          <LogOut size={14} aria-hidden="true" />
          <div
            className="absolute left-full ml-2 px-2 py-1 bg-gunmetal border border-tactical whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity duration-100 pointer-events-none z-50"
            role="tooltip"
          >
            <span className="font-mono text-[10px] tracking-[0.08em] text-bright">
              Logout
            </span>
          </div>
        </button>
      </div>
    </aside>
  );
}
