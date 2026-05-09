"use client";

// =============================================================
// COGNARC — Tactical Button Component
// src/shared/components/ui/TacticalButton.tsx
//
// Tactical IDE Design: 0px radius, no shadows, spring physics.
// Variants: forge (amber CTA), volt (success), ghost (outline)
// =============================================================

import * as React from "react";
import { motion, HTMLMotionProps } from "framer-motion";
import { clsx } from "clsx";

type ButtonVariant = "forge" | "volt" | "ghost" | "danger";
type ButtonSize = "sm" | "md" | "lg";

interface TacticalButtonProps
  extends Omit<HTMLMotionProps<"button">, "children"> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  icon?: React.ReactNode;
  iconPosition?: "left" | "right";
  children: React.ReactNode;
  fullWidth?: boolean;
}

const VARIANT_CLASSES: Record<ButtonVariant, string> = {
  forge:
    "bg-transparent text-forge border border-tactical hover:bg-forge hover:text-obsidian hover:border-forge",
  volt:
    "bg-transparent text-volt border border-tactical hover:bg-volt hover:text-obsidian hover:border-volt",
  ghost:
    "bg-transparent text-muted border border-tactical hover:border-forge hover:text-forge hover:bg-forge",
  danger:
    "bg-transparent text-[#FF4444] border border-tactical hover:bg-[#FF4444] hover:text-obsidian hover:border-[#FF4444]",
};

const SIZE_CLASSES: Record<ButtonSize, string> = {
  sm: "px-3 py-1.5 text-[10px]",
  md: "px-4 py-2 text-[11px]",
  lg: "px-6 py-3 text-[12px]",
};

export function TacticalButton({
  variant = "forge",
  size = "md",
  loading = false,
  icon,
  iconPosition = "left",
  children,
  fullWidth = false,
  className,
  disabled,
  ...props
}: TacticalButtonProps) {
  const isDisabled = disabled || loading;

  return (
    <motion.button
      whileTap={{ scale: 0.98 }}
      transition={{ type: "spring", stiffness: 400, damping: 30 }}
      aria-busy={loading}
      aria-disabled={isDisabled}
      disabled={isDisabled}
      className={clsx(
        // Base — sharp, mono, uppercase
        "group relative inline-flex items-center justify-center gap-2",
        "font-mono font-700 uppercase tracking-[0.10em]",
        "rounded-none",          // CRITICAL: zero radius
        "cursor-pointer",
        "transition-colors duration-[100ms]",
        "select-none",
        "disabled:opacity-40 disabled:cursor-not-allowed",
        VARIANT_CLASSES[variant],
        SIZE_CLASSES[size],
        fullWidth && "w-full",
        className
      )}
      {...props}
    >
      {loading ? (
        <>
          <span className="opacity-100">[ RUNNING_PR0CESS<span className="animate-blink">_</span> ]</span>
        </>
      ) : (
        <>
          {icon && iconPosition === "left" && (
            <span className="shrink-0" aria-hidden="true">{icon}</span>
          )}
          <span className="flex items-center gap-1">
            <span className="hidden group-hover:inline-block text-current font-mono">&gt;</span>
            <span>{children}</span>
            <span className="hidden group-hover:inline-block text-current font-mono animate-blink">_</span>
          </span>
          {icon && iconPosition === "right" && (
            <span className="shrink-0" aria-hidden="true">{icon}</span>
          )}
        </>
      )}
    </motion.button>
  );
}

/** Mechanical loading dots — no spinner */
function LoadingDots() {
  return (
    <span className="flex gap-0.5" aria-label="Loading">
      {[0, 1, 2].map((i) => (
        <motion.span
          key={i}
          className="w-1 h-1 bg-current inline-block"
          animate={{ opacity: [0.3, 1, 0.3] }}
          transition={{
            repeat: Infinity,
            duration: 0.8,
            delay: i * 0.15,
            ease: "linear",
          }}
        />
      ))}
    </span>
  );
}
