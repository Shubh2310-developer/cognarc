"use client";

// =============================================================
// COGNARC — Dashboard Page (Tactical IDE Bento Layout)
// apps/web/app/dashboard/page.tsx
//
// Full HUD: XP bar, today's quests, skill node, streak stats.
// Bento grid. No glassmorphism. No shadows. Forge + Volt only.
// =============================================================

import { useState } from "react";
import { motion } from "framer-motion";
import {
  Zap, Flame, Target, Code2,
  TrendingUp, Activity, AlertTriangle, RefreshCw,
  Map, Trophy,
} from "lucide-react";
import { Navbar } from "@/shared/components/layout/Navbar";
import { Sidebar } from "@/shared/components/layout/Sidebar";
import { XPBar } from "@/features/gamification/components/XPBar";
import { QuestCard, type QuestData } from "@/features/quests/components/QuestCard";
import { Odometer } from "@/shared/components/ui/Odometer";

// ── Mock data — replace with React Query hooks ─────────────────

const MOCK_USER = {
  name: "APEX",
  level: 7,
  currentXP: 1_840,
  levelXP: 1_256,
  nextLevelXP: 2_401,
  totalXP: 12_840,
  streak: 14,
};

const MOCK_QUESTS: QuestData[] = [
  {
    id: "q1",
    title: "Implement a Binary Search Tree with Deletion",
    description: "Build a complete BST implementation with insert, search, and delete operations. The deletion must handle all three cases: leaf node, one child, and two children.",
    type: "coding",
    difficulty: "hard",
    xpReward: 220,
    estimatedMinutes: 45,
    skillNode: "Data Structures > Trees",
    status: "active",
    objectives: [
      "Implement BSTNode class with left, right, value",
      "insert(value) with duplicate handling",
      "search(value) returns node or null",
      "delete(value) handles all three deletion cases",
      "inorder(), preorder(), postorder() traversals",
    ],
  },
  {
    id: "q2",
    title: "Debug: O(n²) Sorting Algorithm Hidden in Production",
    description: "A critical production path has a performance regression. Your task is to identify and replace the hidden bubble sort with an efficient O(n log n) algorithm.",
    type: "debug",
    difficulty: "medium",
    xpReward: 110,
    estimatedMinutes: 25,
    skillNode: "Algorithms > Sorting",
    status: "pending",
    objectives: [
      "Identify the O(n² algorithm in the provided codebase",
      "Prove the issue using Big-O analysis",
      "Replace with O(n log n) solution",
      "Maintain original API interface",
    ],
  },
  {
    id: "q3",
    title: "Study: Dynamic Programming — Memoization vs Tabulation",
    description: "Understand the two primary DP approaches with concrete examples. Complete the comparison analysis and implement Fibonacci using both techniques.",
    type: "theory",
    difficulty: "easy",
    xpReward: 50,
    estimatedMinutes: 20,
    skillNode: "Algorithms > Dynamic Programming",
    status: "pending",
    objectives: [
      "Define memoization (top-down) with an example",
      "Define tabulation (bottom-up) with an example",
      "Implement Fibonacci with memoization",
      "Implement Fibonacci with tabulation",
      "Compare space/time complexity of both",
    ],
  },
];

const MOCK_STATS = [
  { label: "Quests Today",   value: 3,     sub: "0 / 3 done",   color: "text-bright", icon: Target   },
  { label: "Weekly XP",      value: 840,   sub: "+120 today",   color: "text-forge", icon: Zap      },
  { label: "Day Streak",     value: 14,    sub: "Best: 21",     color: "text-forge", icon: Flame    },
  { label: "Skill Mastery",  value: 68,    suffix: "%",         sub: "DSA Core",     color: "text-volt", icon: TrendingUp },
];

// ── Component ──────────────────────────────────────────────────

export default function DashboardPage() {
  const [quests, setQuests] = useState<QuestData[]>(MOCK_QUESTS);
  const [generating, setGenerating] = useState(false);

  function handleComplete(id: string) {
    setQuests(prev =>
      prev.map(q => q.id === id ? { ...q, status: "completed" } : q)
    );
  }

  function handleSkip(id: string) {
    setQuests(prev =>
      prev.map(q => q.id === id ? { ...q, status: "skipped" } : q)
    );
  }

  function handleGenerate() {
    setGenerating(true);
    setTimeout(() => setGenerating(false), 1500);
  }

  const completedCount = quests.filter(q => q.status === "completed").length;
  const pendingCount   = quests.filter(q => q.status !== "completed" && q.status !== "skipped").length;

  return (
    <div className="flex h-screen bg-obsidian overflow-hidden">
      {/* ── Sidebar ────────────────────────────────── */}
      <Sidebar
        userLevel={MOCK_USER.level}
        streakCount={MOCK_USER.streak}
      />

      {/* ── Main ───────────────────────────────────── */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <Navbar pageName="Dashboard / HQ" userName={MOCK_USER.name} />

        <main className="flex-1 overflow-y-auto p-4" role="main" id="main-content">
          {/* ── System Status Banner ──────────────── */}
          <motion.div
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
            className="flex items-center gap-3 mb-4 px-3 py-2 bg-gunmetal border border-tactical"
            role="status"
            aria-label="Daily mission status"
          >
            <div className="w-1.5 h-1.5 bg-volt" aria-hidden="true" />
            <span className="font-mono text-[10px] tracking-[0.10em] uppercase text-muted">
              SYSTEM ACTIVE
            </span>
            <span className="text-tactical">|</span>
            <span className="font-mono text-[10px] text-muted flex gap-1">
              Daily missions loaded —{" "}
              <span className="text-bright flex gap-1"><Odometer value={completedCount} />/<Odometer value={quests.length} /> complete</span>
            </span>
            <div className="ml-auto flex items-center gap-1">
              <Activity size={10} className="text-volt" aria-hidden="true" />
              <span className="font-mono text-[10px] text-volt">API CONNECTED</span>
            </div>
          </motion.div>

          {/* ── Bento Grid ───────────────────────── */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

            {/* ── LEFT COLUMN (2/3) ────────────── */}
            <div className="lg:col-span-2 flex flex-col gap-4">

              {/* XP Bar */}
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ type: "spring", stiffness: 300, damping: 30, delay: 0.05 }}
              >
                <XPBar
                  currentXP={MOCK_USER.currentXP}
                  levelXP={MOCK_USER.levelXP}
                  nextLevelXP={MOCK_USER.nextLevelXP}
                  level={MOCK_USER.level}
                  streak={MOCK_USER.streak}
                  totalXP={MOCK_USER.totalXP}
                />
              </motion.div>

              {/* Today's Quests */}
              <motion.section
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ type: "spring", stiffness: 300, damping: 30, delay: 0.1 }}
                aria-labelledby="quests-heading"
                className="bg-gunmetal border border-tactical"
              >
                {/* Section header */}
                <div className="flex items-center justify-between px-4 py-3 border-b border-tactical">
                  <div className="flex items-center gap-2">
                    <Code2 size={12} className="text-forge" aria-hidden="true" />
                    <h2
                      id="quests-heading"
                      className="font-mono text-[10px] tracking-[0.10em] uppercase text-muted"
                    >
                      Today&apos;s Mission Queue
                    </h2>
                    <span className="font-mono text-[10px] text-muted border border-tactical px-1.5">
                      {pendingCount} pending
                    </span>
                  </div>
                  <motion.button
                    onClick={handleGenerate}
                    disabled={generating}
                    whileTap={{ scale: 0.98 }}
                    transition={{ type: "spring", stiffness: 400, damping: 30 }}
                    className="flex items-center gap-1.5 font-mono text-[10px] tracking-[0.08em] uppercase text-muted border border-tactical px-2.5 py-1.5 hover:border-forge hover:text-forge disabled:opacity-40 transition-colors duration-100"
                    aria-label="Generate new quests"
                  >
                    <RefreshCw size={10} className={generating ? "animate-spin" : ""} aria-hidden="true" />
                    {generating ? "Generating…" : "Regen"}
                  </motion.button>
                </div>

                {/* Quest list */}
                <div className="divide-y divide-tactical">
                  {quests.map((quest, i) => (
                    <QuestCard
                      key={quest.id}
                      quest={quest}
                      onComplete={handleComplete}
                      onSkip={handleSkip}
                      index={i}
                    />
                  ))}
                </div>

                {/* Footer */}
                <div className="px-4 py-2 border-t border-tactical flex items-center gap-2">
                  <AlertTriangle size={10} className="text-muted" aria-hidden="true" />
                  <span className="font-mono text-[10px] text-muted">
                    Quests regenerate daily at 00:00 UTC
                  </span>
                </div>
              </motion.section>
            </div>

            {/* ── RIGHT COLUMN (1/3) ───────────── */}
            <div className="flex flex-col gap-4">

              {/* Stats Grid — 2×2 */}
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ type: "spring", stiffness: 300, damping: 30, delay: 0.12 }}
                className="grid grid-cols-2 gap-px bg-tactical border border-tactical"
                aria-label="Performance stats"
              >
                {MOCK_STATS.map((stat) => {
                  const Icon = stat.icon;
                  return (
                    <div key={stat.label} className="bg-gunmetal p-4 flex flex-col gap-2">
                      <div className="flex items-center gap-1.5">
                        <Icon size={10} className={stat.color} aria-hidden="true" />
                        <span className="font-mono text-[9px] tracking-[0.10em] uppercase text-muted">
                          {stat.label}
                        </span>
                      </div>
                      <span className={`font-mono text-[22px] font-700 leading-none ${stat.color} flex items-baseline gap-0.5`}>
                        <Odometer value={stat.value} format="locale" />
                        {stat.suffix && <span className="text-[14px]">{stat.suffix}</span>}
                      </span>
                      <span className="font-mono text-[10px] text-muted">{stat.sub}</span>
                    </div>
                  );
                })}
              </motion.div>

              {/* Active Skill Node */}
              <motion.section
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ type: "spring", stiffness: 300, damping: 30, delay: 0.16 }}
                className="bg-gunmetal border border-tactical"
                aria-labelledby="skill-heading"
              >
                <div className="flex items-center gap-2 px-4 py-3 border-b border-tactical">
                  <Map size={11} className="text-forge" aria-hidden="true" />
                  <h2 id="skill-heading" className="font-mono text-[10px] tracking-[0.10em] uppercase text-muted">
                    Active Skill Node
                  </h2>
                </div>
                <div className="p-4">
                  <div className="mb-3">
                    <p className="font-mono text-[9px] tracking-[0.10em] uppercase text-muted mb-1">
                      Tree
                    </p>
                    <p className="font-space-grotesk text-[13px] font-600 text-bright">
                      Data Structures & Algorithms
                    </p>
                  </div>
                  <div className="mb-3">
                    <p className="font-mono text-[9px] tracking-[0.10em] uppercase text-muted mb-1">
                      Current Node
                    </p>
                    <div className="flex items-center gap-2 border border-forge px-3 py-2 border-l-2">
                      <div className="w-1.5 h-1.5 bg-forge" aria-hidden="true" />
                      <span className="font-mono text-[12px] text-forge font-600">
                        Binary Trees
                      </span>
                    </div>
                  </div>
                  {/* Node progress */}
                  <div>
                    <div className="flex justify-between mb-1.5">
                      <span className="font-mono text-[9px] tracking-[0.08em] uppercase text-muted">
                        Mastery
                      </span>
                      <span className="font-mono text-[10px] text-forge flex gap-0.5"><Odometer value={68} />%</span>
                    </div>
                    <div className="h-[2px] bg-tactical relative" role="progressbar" aria-valuenow={68} aria-valuemin={0} aria-valuemax={100}>
                      <div className="absolute left-0 top-0 h-full bg-forge transition-all duration-[400ms]" style={{ width: "68%" }} />
                    </div>
                    <p className="font-mono text-[10px] text-muted mt-2">
                      Next: <span className="text-bright">Graph Theory</span>
                    </p>
                  </div>
                </div>
              </motion.section>

              {/* Phase lock notice for battles */}
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ type: "spring", stiffness: 300, damping: 30, delay: 0.2 }}
                className="bg-gunmetal border border-tactical p-4 opacity-40"
                role="note"
                aria-label="Boss Battles coming in Phase 3"
              >
                <div className="flex items-center gap-2 mb-2">
                  <Trophy size={11} className="text-muted" aria-hidden="true" />
                  <span className="font-mono text-[10px] tracking-[0.10em] uppercase text-muted">
                    Boss Battles
                  </span>
                  <span className="font-mono text-[9px] tracking-[0.06em] uppercase text-muted border border-tactical px-1">
                    Phase 3
                  </span>
                </div>
                <p className="font-sans text-[11px] text-muted">
                  Weekly boss battles unlock at Phase 3. Keep grinding.
                </p>
              </motion.div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
