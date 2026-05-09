"use client";

// =============================================================
// COGNARC — QuestCard Component (Tactical IDE)
// src/features/quests/components/QuestCard.tsx
//
// Industrial quest display: difficulty badge, XP reward,
// type icon, objectives, and mechanical complete/skip actions.
// =============================================================

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Code2, Bug, BookOpen, Wrench,
  CheckCircle2, Clock, Zap, ChevronRight, SkipForward,
} from "lucide-react";
import { clsx } from "clsx";

export type QuestType = "coding" | "debug" | "theory" | "build";
export type QuestDifficulty = "easy" | "medium" | "hard" | "boss";
export type QuestStatus = "pending" | "active" | "completed" | "skipped";

export interface QuestData {
  id: string;
  title: string;
  description: string;
  type: QuestType;
  difficulty: QuestDifficulty;
  xpReward: number;
  estimatedMinutes: number;
  skillNode: string;
  status: QuestStatus;
  objectives?: string[];
}

interface QuestCardProps {
  quest: QuestData;
  onComplete?: (id: string) => void;
  onSkip?: (id: string) => void;
  index?: number;
}

const TYPE_CONFIG: Record<QuestType, { icon: React.ElementType; label: string; color: string }> = {
  coding: { icon: Code2,    label: "CODE",   color: "text-forge" },
  debug:  { icon: Bug,      label: "DEBUG",  color: "text-[#FF4444]" },
  theory: { icon: BookOpen, label: "THEORY", color: "text-muted" },
  build:  { icon: Wrench,   label: "BUILD",  color: "text-volt" },
};

const DIFF_CONFIG: Record<QuestDifficulty, { label: string; border: string; text: string }> = {
  easy:   { label: "EASY", border: "border-tactical",  text: "text-muted"  },
  medium: { label: "MED",  border: "border-forge",  text: "text-forge"  },
  hard:   { label: "HARD", border: "border-forge",  text: "text-forge"  },
  boss:   { label: "BOSS", border: "border-volt",  text: "text-volt"  },
};

export function QuestCard({ quest, onComplete, onSkip, index = 0 }: QuestCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [completing, setCompleting] = useState(false);

  const typeConfig = TYPE_CONFIG[quest.type];
  const diffConfig = DIFF_CONFIG[quest.difficulty];
  const Icon = typeConfig.icon;

  const isCompleted = quest.status === "completed";
  const isSkipped   = quest.status === "skipped";
  const isActive    = quest.status === "active";

  function handleComplete() {
    if (isCompleted || completing) return;
    setCompleting(true);
    setTimeout(() => { onComplete?.(quest.id); setCompleting(false); }, 300);
  }

  return (
    <motion.article
      initial={{ opacity: 0, x: -6 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, scale: 0.95, height: 0, overflow: "hidden" }}
      transition={{ type: "spring", stiffness: 300, damping: 30, delay: index * 0.06 }}
      aria-label={`Quest: ${quest.title}`}
      className={clsx(
        "group relative bg-gunmetal border rounded-none transition-colors duration-100 overflow-hidden",
        isActive    && "border-l-2 border-forge",
        isCompleted && "border-tactical opacity-60",
        isSkipped   && "border-tactical opacity-30",
        !isActive && !isCompleted && !isSkipped && "border-tactical hover:border-forge",
        completing && "border-volt animate-tactical-pulse"
      )}
    >
      {/* Target locking scan line */}
      {!isCompleted && !completing && (
        <div className="absolute top-0 bottom-0 left-0 w-[2px] bg-forge opacity-0 group-hover:opacity-100 group-hover:translate-x-[500px] transition-all duration-[800ms] ease-linear pointer-events-none" aria-hidden="true" />
      )}
      {/* Active / completed stripe */}
      {isActive    && <div className="absolute left-0 top-0 bottom-0 w-[2px] bg-forge" aria-hidden="true" />}
      {isCompleted && <div className="absolute left-0 top-0 bottom-0 w-[2px] bg-volt" aria-hidden="true" />}

      <div className="p-4 pl-5">
        <div className="flex items-start gap-3">
          {/* Type icon box */}
          <div className="mt-0.5 shrink-0 bg-obsidian border border-tactical p-1.5" aria-hidden="true">
            <Icon size={13} className={typeConfig.color} />
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <span className={clsx("font-mono text-[9px] font-600 tracking-[0.10em] uppercase border px-1.5 py-0.5", diffConfig.border, diffConfig.text)}>
                {diffConfig.label}
              </span>
              <span className="font-mono text-[9px] tracking-[0.08em] uppercase text-muted">
                {typeConfig.label}
              </span>
              {isCompleted && (
                <span className="font-mono text-[9px] tracking-[0.08em] uppercase text-volt border border-volt px-1.5 py-0.5">
                  DONE
                </span>
              )}
            </div>

            <h3 className={clsx(
              "font-space-grotesk text-[14px] font-600 leading-tight",
              isCompleted ? "text-muted line-through" : "text-bright",
            )}>
              {quest.title}
            </h3>

            <div className="flex items-center gap-3 mt-1.5 flex-wrap">
              <span className="font-mono text-[10px] text-muted">{quest.skillNode}</span>
              <span className="text-tactical font-mono">|</span>
              <div className="flex items-center gap-1">
                <Clock size={9} className="text-muted" aria-hidden="true" />
                <span className="font-mono text-[10px] text-muted">{quest.estimatedMinutes}m</span>
              </div>
              <span className="text-tactical font-mono">|</span>
              <div className="flex items-center gap-1">
                <Zap size={9} className="text-forge" aria-hidden="true" />
                <span className="font-mono text-[10px] text-forge font-600">+{quest.xpReward} XP</span>
              </div>
            </div>
          </div>

          {/* Expand toggle */}
          <button
            onClick={() => setExpanded(p => !p)}
            aria-label={expanded ? "Collapse quest" : "Expand quest"}
            aria-expanded={expanded}
            className="p-1.5 text-muted hover:text-bright border border-transparent hover:border-tactical transition-colors duration-100"
          >
            <motion.div animate={{ rotate: expanded ? 90 : 0 }} transition={{ type: "spring", stiffness: 400, damping: 30 }}>
              <ChevronRight size={13} />
            </motion.div>
          </button>
        </div>

        {/* Expandable details */}
        <AnimatePresence>
          {expanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ type: "spring", stiffness: 350, damping: 35 }}
              className="overflow-hidden"
            >
              <div className="pt-3 pl-8 border-t border-tactical mt-3">
                <p className="font-sans text-[12px] text-muted leading-relaxed mb-3">
                  {quest.description}
                </p>
                {quest.objectives && quest.objectives.length > 0 && (
                  <>
                    <p className="font-mono text-[9px] tracking-[0.10em] uppercase text-muted mb-2">
                      Objectives
                    </p>
                    <ul className="space-y-1.5">
                      {quest.objectives.map((obj, i) => (
                        <li key={i} className="flex items-start gap-2">
                          <span className="font-mono text-[10px] text-tactical mt-0.5 shrink-0">
                            {String(i + 1).padStart(2, "0")}
                          </span>
                          <span className="font-sans text-[12px] text-muted">{obj}</span>
                        </li>
                      ))}
                    </ul>
                  </>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Action bar */}
        {!isCompleted && !isSkipped && (
          <div className="flex flex-col mt-3 pt-3 border-t border-tactical relative">
            <div className="flex gap-2 relative z-10">
              <motion.button
                onClick={handleComplete}
                disabled={completing}
                whileTap={{ scale: 0.98 }}
                transition={{ type: "spring", stiffness: 400, damping: 30 }}
                className={clsx(
                  "group/btn relative flex-1 flex items-center justify-center gap-2 text-[10px] font-mono font-700 tracking-[0.10em] uppercase py-2 px-3 overflow-hidden transition-colors duration-100",
                  completing
                    ? "bg-obsidian text-volt border border-volt"
                    : "bg-forge text-obsidian border border-forge hover:bg-[#E55F00]"
                )}
                aria-label={`Complete quest: ${quest.title}`}
              >
                {completing && (
                  <motion.div
                    initial={{ width: "0%" }}
                    animate={{ width: "100%" }}
                    transition={{ duration: 0.3, ease: "linear" }}
                    className="absolute top-0 left-0 bottom-0 bg-volt/20"
                  />
                )}
                {completing ? (
                  <span className="relative z-10">[ RUNNING_PR0CESS<span className="animate-blink">_</span> ]</span>
                ) : (
                  <span className="relative z-10 flex items-center gap-1 group-hover/btn:gap-2">
                    <span className="hidden group-hover:inline-block font-mono">&gt;</span> 
                    EXECUTE
                    <span className="hidden group-hover:inline-block animate-blink font-mono">_</span>
                  </span>
                )}
              </motion.button>
              <motion.button
                onClick={() => onSkip?.(quest.id)}
                disabled={completing}
                whileTap={{ scale: 0.98 }}
                transition={{ type: "spring", stiffness: 400, damping: 30 }}
                className="flex items-center gap-1.5 bg-transparent text-muted border border-tactical font-mono text-[10px] tracking-[0.08em] uppercase py-2 px-3 hover:border-forge hover:text-forge transition-colors duration-100"
                aria-label={`Skip quest: ${quest.title}`}
              >
                <SkipForward size={11} aria-hidden="true" /> Skip
              </motion.button>
            </div>
            
            {/* Terminal log stream (visible during completion) */}
            <AnimatePresence>
              {completing && (
                <motion.div
                  initial={{ opacity: 0, height: 0, marginTop: 0 }}
                  animate={{ opacity: 1, height: "auto", marginTop: 8 }}
                  className="font-mono text-[10px] text-volt tracking-widest uppercase"
                >
                  &gt; +{quest.xpReward} XP SECURED. NODE ADVANCED.
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}
      </div>
    </motion.article>
  );
}
