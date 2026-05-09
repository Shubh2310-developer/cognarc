"use client";

// =============================================================
// COGNARC — Tactical Card / Bento Box
// src/shared/components/ui/TacticalCard.tsx
//
// Industrial Blueprint card. Variants: default, active (forge),
// success (volt). Corner bracket accent decorators included.
// =============================================================

import * as React from "react";
import { motion, HTMLMotionProps } from "framer-motion";
import { clsx } from "clsx";

type CardVariant = "default" | "active" | "success" | "warning";

interface TacticalCardProps extends Omit<HTMLMotionProps<"div">, "children"> {
  variant?: CardVariant;
  heading?: string;
  subheading?: string;
  label?: string;
  cornerAccent?: boolean;
  noPadding?: boolean;
  children: React.ReactNode;
  animate?: boolean;
}

const VARIANT_BORDER: Record<CardVariant, string> = {
  default: "border-[#2D3748]",
  active:  "border-[#FF6B00] border-2",
  success: "border-[#CCFF00] border-2",
  warning: "border-[#FFB800]",
};

export function TacticalCard({
  variant = "default",
  heading,
  subheading,
  label,
  cornerAccent = false,
  noPadding = false,
  children,
  animate = false,
  className,
  ...props
}: TacticalCardProps) {
  const content = (
    <div
      className={clsx(
        "relative",
        "bg-[#16181D]",         // Gunmetal surface
        "border",               // 1px tactical border
        "rounded-none",         // CRITICAL: zero radius
        VARIANT_BORDER[variant],
        !noPadding && "p-4",
        // Corner bracket decorators
        cornerAccent && "tactical-corner",
        className
      )}
    >
      {/* Card header if label/heading provided */}
      {(label || heading || subheading) && (
        <header className="mb-3">
          {label && (
            <p className="font-mono text-[10px] font-600 tracking-[0.10em] uppercase text-[#8B949E] mb-1">
              {label}
            </p>
          )}
          {heading && (
            <h3 className="font-space-grotesk text-[16px] font-600 text-[#F8FAFC] leading-tight">
              {heading}
            </h3>
          )}
          {subheading && (
            <p className="font-inter text-[12px] text-[#8B949E] mt-0.5">
              {subheading}
            </p>
          )}
        </header>
      )}

      {/* Active variant: Forge Amber top border accent */}
      {variant === "active" && (
        <div
          className="absolute top-0 left-0 right-0 h-[2px] bg-[#FF6B00]"
          aria-hidden="true"
        />
      )}

      {/* Success variant: Volt Lime top border accent */}
      {variant === "success" && (
        <div
          className="absolute top-0 left-0 right-0 h-[2px] bg-[#CCFF00]"
          aria-hidden="true"
        />
      )}

      {children}
    </div>
  );

  if (animate) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
        {...(props as HTMLMotionProps<"div">)}
      >
        {content}
      </motion.div>
    );
  }

  return content;
}

/** Horizontal divider within a card */
export function CardDivider({ label }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 my-3" role="separator">
      <div className="flex-1 h-px bg-[#2D3748]" />
      {label && (
        <span className="font-mono text-[9px] tracking-[0.12em] uppercase text-[#8B949E] shrink-0">
          {label}
        </span>
      )}
      <div className="flex-1 h-px bg-[#2D3748]" />
    </div>
  );
}
