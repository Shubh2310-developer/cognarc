import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./src/**/*.{ts,tsx}",
    "./app/**/*.{ts,tsx}",
    "../../packages/ui/src/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      // ── Tactical IDE Color System ─────────────────────────────
      colors: {
        // Surfaces
        void: "var(--bg-void)",
        obsidian: "var(--surfaces-obsidian)",
        gunmetal: "var(--surface-gunmetal)",
        // Borders
        tactical: "var(--border-tactical)",
        // Accents
        forge: "var(--accent-forge)",
        volt: "var(--accent-volt)",
        // Text
        bright: "var(--color-bright)",
        muted: "var(--color-muted)",
        // Semantic aliases
        primary: "var(--accent-forge)",
        success: "var(--accent-volt)",
        surface: "var(--surface-gunmetal)",
        background: "var(--surfaces-obsidian)",
        border: "var(--border-tactical)",
      },

      // ── Typography System ──────────────────────────────────────
      fontFamily: {
        "space-grotesk": ["Space Grotesk", "sans-serif"],  // Headings
        mono: ["JetBrains Mono", "Fira Code", "Consolas", "monospace"],  // Telemetry
        inter: ["Inter", "sans-serif"],  // Body
        sans: ["Inter", "sans-serif"],   // Default override
      },

      // ── Sharp Grid — No Radius Anywhere ────────────────────────
      borderRadius: {
        none: "0px",
        DEFAULT: "0px",
        sm: "0px",
        md: "0px",
        lg: "0px",
        xl: "0px",
        "2xl": "0px",
        full: "0px",  // Even "pill" shapes are square in Tactical IDE
      },

      // ── Border Width ───────────────────────────────────────────
      borderWidth: {
        DEFAULT: "1px",
        "0": "0px",
        "2": "2px",   // Double-border for critical states (active quest)
      },

      // ── Tactical Grid Spacing ──────────────────────────────────
      spacing: {
        "px": "1px",
        "0.5": "2px",
        "1": "4px",
        "2": "8px",
        "3": "12px",
        "4": "16px",
        "5": "20px",
        "6": "24px",
        "8": "32px",
        "10": "40px",
        "12": "48px",
        "16": "64px",
        "20": "80px",
        "24": "96px",
        "32": "128px",
      },

      // ── Box Shadow: NONE ───────────────────────────────────────
      // Depth = borders only. No glow, no blur, no drop-shadow.
      boxShadow: {
        none: "none",
        DEFAULT: "none",
        sm: "none",
        md: "none",
        lg: "none",
        xl: "none",
        "2xl": "none",
        inner: "none",
      },

      // ── Mechanical Animation Timing ───────────────────────────
      // Framer Motion handles spring physics. CSS transitions are snap-sharp.
      transitionTimingFunction: {
        mechanical: "cubic-bezier(0.25, 0.46, 0.45, 0.94)",
        snap: "cubic-bezier(0.77, 0, 0.175, 1)",  // Hard snap
      },
      transitionDuration: {
        DEFAULT: "100ms",
        "0": "0ms",
        "100": "100ms",
        "150": "150ms",
        "200": "200ms",
      },

      // ── Grid Templates for Bento Dashboard ────────────────────
      gridTemplateColumns: {
        "bento-4": "repeat(4, 1fr)",
        "bento-3": "repeat(3, 1fr)",
        "bento-2": "repeat(2, 1fr)",
      },
      gridTemplateRows: {
        "bento": "auto",
      },

      // ── Typography Scale ───────────────────────────────────────
      fontSize: {
        "2xs": ["10px", { lineHeight: "14px", letterSpacing: "0.08em" }],
        xs: ["11px", { lineHeight: "16px", letterSpacing: "0.06em" }],
        sm: ["12px", { lineHeight: "18px", letterSpacing: "0.04em" }],
        base: ["14px", { lineHeight: "20px", letterSpacing: "0.01em" }],
        lg: ["16px", { lineHeight: "24px", letterSpacing: "0em" }],
        xl: ["18px", { lineHeight: "28px", letterSpacing: "-0.01em" }],
        "2xl": ["22px", { lineHeight: "32px", letterSpacing: "-0.02em" }],
        "3xl": ["28px", { lineHeight: "36px", letterSpacing: "-0.03em" }],
        "4xl": ["36px", { lineHeight: "44px", letterSpacing: "-0.04em" }],
        "5xl": ["48px", { lineHeight: "56px", letterSpacing: "-0.04em" }],
      },

      // ── Letter Spacing ─────────────────────────────────────────
      letterSpacing: {
        tightest: "-0.04em",
        tighter: "-0.02em",
        tight: "-0.01em",
        normal: "0em",
        wide: "0.04em",
        wider: "0.08em",
        widest: "0.12em",
        // For mono tags and labels
        tactical: "0.10em",
      },

      // ── Animation Keyframes ────────────────────────────────────
      keyframes: {
        // Typewriter cursor blink — mechanical
        blink: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0" },
        },
        // Hard scan line sweep (status indicators)
        scanline: {
          "0%": { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(100vh)" },
        },
        // XP bar fill — mechanical left-to-right
        xpFill: {
          "0%": { width: "0%" },
          "100%": { width: "var(--xp-percent)" },
        },
        // Status pulse — no blur, sharp opacity flicker
        tacticalPulse: {
          "0%, 100%": { opacity: "1", borderColor: "var(--accent-forge)" },
          "50%": { opacity: "0.6", borderColor: "var(--accent-forge)" },
        },
        // Forge amber glow-in for active elements (border only)
        forgeActivate: {
          "0%": { borderColor: "var(--border-tactical)" },
          "100%": { borderColor: "var(--accent-forge)" },
        },
      },
      animation: {
        blink: "blink 1s step-end infinite",
        scanline: "scanline 8s linear infinite",
        "xp-fill": "xpFill 0.4s cubic-bezier(0.77, 0, 0.175, 1) forwards",
        "tactical-pulse": "tacticalPulse 2s step-end infinite",
        "forge-activate": "forgeActivate 0.1s snap forwards",
      },
    },
  },
  plugins: [],
};

export default config;
