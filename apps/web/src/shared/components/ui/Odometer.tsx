"use client";

// =============================================================
// COGNARC — Tactical Odometer Display
// src/shared/components/ui/Odometer.tsx
//
// A terminal-style animated number component.
// Rapidly scrambles through random characters before locking
// into the final number, simulating a mechanical decode.
// =============================================================

import { useEffect, useState, useRef } from "react";
import { motion } from "framer-motion";
import { clsx } from "clsx";

interface OdometerProps {
  value: number;
  format?: "raw" | "padded2" | "padded3" | "locale";
  className?: string;
  durationMs?: number;
}

const CHARS = "0123456789";

export function Odometer({
  value,
  format = "raw",
  className,
  durationMs = 600,
}: OdometerProps) {
  const [display, setDisplay] = useState<string>("");
  const prevValue = useRef<number>(value);

  const formatValue = (v: number) => {
    switch (format) {
      case "padded2":
        return v.toString().padStart(2, "0");
      case "padded3":
        return v.toString().padStart(3, "0");
      case "locale":
        return v.toLocaleString();
      default:
        return v.toString();
    }
  };

  useEffect(() => {
    const finalStr = formatValue(value);
    
    // Initial render or no change -> just set it
    if (value === prevValue.current) {
      setDisplay(finalStr);
      return;
    }

    // Scramble sequence
    const start = Date.now();
    const interval = setInterval(() => {
      const elapsed = Date.now() - start;
      const progress = elapsed / durationMs;

      if (progress >= 1) {
        setDisplay(finalStr);
        prevValue.current = value;
        clearInterval(interval);
      } else {
        // Generate scramble string of same length (excluding commas for simplicity during scramble)
        const len = finalStr.length;
        let scrambled = "";
        for (let i = 0; i < len; i++) {
          if (finalStr[i] === "," || finalStr[i] === ".") {
            scrambled += finalStr[i];
          } else {
            // Lock in characters from left to right as time progresses
            if (i / len < progress) {
              scrambled += finalStr[i];
            } else {
              scrambled += CHARS[Math.floor(Math.random() * CHARS.length)];
            }
          }
        }
        setDisplay(scrambled);
      }
    }, 40); // 25fps scramble

    return () => clearInterval(interval);
  }, [value, format, durationMs]);

  // Handle SSR hydration mismatch by setting initial state correctly
  useEffect(() => {
    if (!display) {
      setDisplay(formatValue(value));
    }
  }, []);

  return (
    <motion.span
      className={clsx("font-mono tabular-nums inline-block", className)}
      aria-label={value.toString()}
    >
      {display || formatValue(value)}
    </motion.span>
  );
}
