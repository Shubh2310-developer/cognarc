"use client";

// =============================================================
// COGNARC — XP Progress Bar & Level Display
// src/features/gamification/components/XPBar.tsx
//
// Tactical IDE: Sharp track, amber fill, mono readout.
// Spring-animated fill. No glow. No shadows.
// =============================================================

import { motion, useSpring, useTransform } from "framer-motion";
import { useEffect } from "react";
import { Zap, TrendingUp } from "lucide-react";
import { clsx } from "clsx";
import { Odometer } from "@/shared/components/ui/Odometer";

interface XPBarProps {
  currentXP: number;
  levelXP: number;        // XP threshold for current level
  nextLevelXP: number;    // XP threshold for next level
  level: number;
  streak: number;
  totalXP: number;
}

function calcProgress(current: number, levelStart: number, levelEnd: number): number {
  if (levelEnd <= levelStart) return 100;
  const progress = ((current - levelStart) / (levelEnd - levelStart)) * 100;
  return Math.min(Math.max(progress, 0), 100);
}

export function XPBar({
  currentXP,
  levelXP,
  nextLevelXP,
  level,
  streak,
  totalXP,
}: XPBarProps) {
  const progressPct = calcProgress(currentXP, levelXP, nextLevelXP);
  const xpToNext = nextLevelXP - currentXP;

  const springValue = useSpring(0, { stiffness: 280, damping: 32 });
  const barWidth = useTransform(springValue, (v) => `${v}%`);

  useEffect(() => {
    springValue.set(progressPct);
  }, [progressPct, springValue]);

  return (
    <div className="bg-gunmetal border border-tactical p-4" role="region" aria-label="XP Progress">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Zap size={12} className="text-forge" aria-hidden="true" />
          <span className="font-mono text-[10px] tracking-[0.10em] uppercase text-muted">
            Level Progress
          </span>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1">
            <span className="font-mono text-[10px] text-muted">STK</span>
            <Odometer
              value={streak}
              format="padded3"
              className="text-[13px] font-700 text-forge"
            />
          </div>
          <div className="flex items-center gap-1">
            <TrendingUp size={10} className="text-muted" aria-hidden="true" />
            <span className="font-mono text-[10px] text-muted flex gap-1">
              <Odometer value={totalXP} format="locale" /> XP
            </span>
          </div>
        </div>
      </div>

      <div className="flex items-end gap-3 mb-3">
        <div>
          <p className="font-mono text-[10px] tracking-[0.08em] uppercase text-muted mb-0.5">
            Current Level
          </p>
          <div className="flex items-baseline gap-1">
            <Odometer
              value={level}
              format="padded2"
              className="text-[40px] font-700 text-bright leading-none"
            />
            <span className="font-mono text-[11px] text-forge mb-1">LVL</span>
          </div>
        </div>

        <div className="flex-1 pb-1">
          <div className="flex justify-between items-center mb-1.5">
            <span className="font-mono text-[10px] text-muted flex gap-1">
              <Odometer value={currentXP} format="locale" /> / <Odometer value={nextLevelXP} format="locale" />
            </span>
            <span className="font-mono text-[10px] text-forge">
              {progressPct.toFixed(1)}%
            </span>
          </div>

          <div
            className="w-full flex gap-[2px] h-[6px]"
            role="progressbar"
            aria-valuenow={currentXP}
            aria-valuemin={levelXP}
            aria-valuemax={nextLevelXP}
            aria-label={`XP: ${currentXP} of ${nextLevelXP}`}
          >
            {Array.from({ length: 40 }).map((_, i) => {
              const isActive = (i / 40) * 100 < progressPct;
              return (
                <div
                  key={i}
                  className={clsx(
                    "flex-1 h-full transition-colors duration-75",
                    isActive ? "bg-forge" : "bg-tactical"
                  )}
                />
              );
            })}
          </div>

          <p className="font-mono text-[10px] text-muted mt-1.5">
            {xpToNext.toLocaleString()} XP to{" "}
            <span className="text-bright">Level {level + 1}</span>
          </p>
        </div>
      </div>
    </div>
  );
}
