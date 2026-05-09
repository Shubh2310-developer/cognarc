// =============================================================
// COGNARC — Design Tokens (JS/TS exports)
// packages/design-tokens/src/index.ts
// JS mirror of tokens.css for use in theme configs (Tailwind, etc.)
// =============================================================

export const colors = {
  primary: "#6D28D9",
  primaryLight: "#7C3AED",
  primaryDark: "#5B21B6",
  accent: "#D97706",
  accentLight: "#F59E0B",
  accentDark: "#B45309",

  surface: {
    bg: "#0F0F1A",
    card: "#1A1A2E",
    elevated: "#16213E",
  },

  text: {
    primary: "#F8FAFC",
    secondary: "#94A3B8",
    muted: "#64748B",
    inverse: "#0F0F1A",
  },

  semantic: {
    success: "#10B981",
    warning: "#F59E0B",
    danger: "#EF4444",
    info: "#3B82F6",
  },
} as const;

export const fonts = {
  heading: "'Space Grotesk', system-ui, sans-serif",
  body: "'Inter', system-ui, sans-serif",
  mono: "'JetBrains Mono', 'Fira Code', monospace",
} as const;

export const spacing = {
  1: "0.25rem",
  2: "0.5rem",
  3: "0.75rem",
  4: "1rem",
  5: "1.25rem",
  6: "1.5rem",
  8: "2rem",
  10: "2.5rem",
  12: "3rem",
  16: "4rem",
} as const;

export const borderRadius = {
  sm: "0.375rem",
  md: "0.5rem",
  lg: "0.75rem",
  xl: "1rem",
  full: "9999px",
} as const;

export const transitions = {
  fast: "150ms ease",
  base: "250ms ease",
  slow: "400ms ease",
} as const;

// Tailwind-compatible extension object
export const tailwindThemeExtension = {
  colors: {
    primary: colors.primary,
    "primary-light": colors.primaryLight,
    "primary-dark": colors.primaryDark,
    accent: colors.accent,
    "surface-bg": colors.surface.bg,
    "surface-card": colors.surface.card,
    "surface-elevated": colors.surface.elevated,
    success: colors.semantic.success,
    warning: colors.semantic.warning,
    danger: colors.semantic.danger,
  },
  fontFamily: {
    heading: ["Space Grotesk", "system-ui", "sans-serif"],
    body: ["Inter", "system-ui", "sans-serif"],
    mono: ["JetBrains Mono", "Fira Code", "monospace"],
  },
} as const;
