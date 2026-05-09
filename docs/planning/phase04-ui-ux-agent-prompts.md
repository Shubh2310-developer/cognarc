# Phase 4 Planning: Tactical IDE UI/UX Agent Prompts

**Status:** Active integration for all frontend implementation phases.
**Reference Blueprint:** `/home/agentrogue/cognarc/docs/website_ui/ui-ux-blueprint.md`

## Overview
This document contains highly detailed instructions and system prompts to inject into agents (`frontend-developer`, `code-reviewer`) and skills (`ui-design-system`) when executing UI/UX tasks. This ensures the "Tactical IDE" design philosophy is consistently applied across all Next.js applications and React components.

---

## 1. `frontend-developer` Agent System Prompt Addition

Inject the following context into the `frontend-developer` agent when kicking off any UI sprint:

> **[SYSTEM DIRECTIVE: COGNARC OVERRIDE - TACTICAL IDE]**
> You are building a frontend for COGNARC. You MUST adhere to the "Tactical IDE / Industrial Blueprint" design system outlined in `docs/website_ui/ui-ux-blueprint.md`. 
>
> 🛑 **CRITICAL RESTRICTION**: The color PURPLE (and all magenta/violet variants) is STRICTLY BANNED. Do not use Tailwind classes like `bg-purple-500` or `text-violet-400`. Do not use glassmorphism (`backdrop-blur`).
> 
> **AESTHETIC RULES**:
> 1. **Bento Grid**: Use strict 1px solid borders (`border-tactical` / `#2D3748`) to box out content. Do not use drop shadows.
> 2. **Sharp Geometry**: Use `rounded-none` or max `rounded-sm` (2px).
> 3. **The Palette**: Backgrounds must be Obsidian (`#0B0C10`) or Gunmetal (`#16181D`). Accents are Forge Amber (`#FF6B00`) for activity/warnings and Volt Lime (`#CCFF00`) for success/XP.
> 4. **Dual Typography**: Use `Space Grotesk` or `Geist` for narrative headings. Use exclusively `JetBrains Mono` or `Fira Code` for all telemetry, XP metrics, tags, buttons (masquerading as commands), and time estimates.

---

## 2. `code-reviewer` Agent Pre-Flight Checklist

When calling the `code-reviewer` agent on any frontend PR, include this instruction check:

> **[SYSTEM DIRECTIVE: UI ENFORCEMENT PROTOCOL]**
> Before reviewing business logic, you must run the following UI/UX quality gates on the frontend code:
> 
> - **[ ] Check for Banned Colors:** Scan the diff for `purple`, `violet`, `indigo`, `magenta`, `fuchsia`. If found, **REJECT** the PR with a reminder that COGNARC uses the Forge/Volt Tactical palette.
> - **[ ] Check for Banned UX Patterns:** Scan the diff for `shadow` or `drop-shadow` or `backdrop-blur`. If found, **REJECT** the PR. We use flat UI with 1px borders (`border-tactical`).
> - **[ ] Check Geometry:** Ensure there are no large border radii (e.g., `rounded-xl`, `rounded-full`, `rounded-lg`). If found, recommend `rounded-none` or `rounded-sm`.
> - **[ ] Check Motion Physics:** If `framer-motion` is used, ensure the `transition` object relies on mechanical spring physics (e.g., `stiffness: 300, damping: 30`) and not floaty/bouncy defaults.

---

## 3. `ui-design-system` Skill Augmentation

For any agent executing the `ui-design-system` skill to build shared components:

> **[SKILL UPGRADE: COGNARC SHADCN PORT]**
> When scaffolding new ShadCN/Radix UI components into `packages/ui`:
> 1. In `tailwind.config.ts`, map the semantic colors directly to the CSS variables defined in the blueprint (e.g., `bg-primary` -> `var(--accent-forge)`).
> 2. Strip all inherent shadow definitions from the component defaults.
> 3. Set the global CSS `--radius` variable to `0rem` or `0.1rem`.
> 4. For buttons, implement a custom hover state that inverses the foreground/background and appends a mono-font `>` symbol.

---

## 4. Integration into GSD Planning Flow
During `/gsd:plan-phase`, the `gsd-planner` agent MUST read `docs/website_ui/ui-ux-blueprint.md` as context before generating tasks. All Jira/Linear task generations must contain the acceptance criteria: *"Adheres to Tactical IDE Design System (No Purple, 1px Bento Grid)"*.