# COGNARC UI/UX Design System & Architectural Blueprint

**Version:** 1.0.0
**Target:** Frontend Developers, AI Engineering Agents (`frontend-developer`, `ui-design-system`, `code-reviewer`)
**Status:** Enforced Configuration

---

## 1. Core Aesthetic Philosophy: "Tactical IDE"

COGNARC is built for developers. We are explicitly rejecting the standard "Consumer AI SaaS" aesthetic. 
*   **REJECT:** Glassmorphism, purple/blue neon gradients, friendly 12px rounded corners, playful physics, and abstract generative AI blobs.
*   **EMBRACE:** "Tactical IDE," Cyberpunk-technical, high-contrast monochrome with targeted neon accents. Information-dense, low cognitive load, mechanical, and highly structured. The platform should feel like an integrated development environment (IDE) overlaid with a military-grade heads-up display (HUD).

---

## 2. Design Tokens & Color Engineering

**CRITICAL RULE:** The color purple (and nearby hues like magenta or violet) is strictly banned from this project to ensure we do not look like a generic AI wrapper. All styles must use these CSS variables.

### 2.1 The Palette
*   **Base & Backgrounds (The Canvas)**
    *   `--bg-void`: `#050505` (Absolute dark, used for deep backgrounds)
    *   `--surfaces-obsidian`: `#0B0C10` (Primary app background)
    *   `--surface-gunmetal`: `#16181D` (Card backgrounds, sidebars, bento boxes)
    *   `--surface-elevated`: `#1F2229` (Hover states, active elements)

*   **Primary Accents (The Energy)**
    *   `--accent-forge`: `#FF6B00` (Forge Amber) - Used for active skill nodes, streaks, primary CTAs, active cursor carets, and warning indicators. It provides high-contrast warmth.
    *   `--accent-forge-dim`: `#4A2300` (Muted Amber for subtle active backgrounds)

*   **Success & Progress (The Reward)**
    *   `--accent-volt`: `#CCFF00` (Volt Lime) - Used exclusively for completed quests, XP additions, and node mastery. Provides an instant, technical dopamine hit. 

*   **Typography & Grids**
    *   `--text-bright`: `#F8FAFC` (Headers, active data)
    *   `--text-muted`: `#8B949E` (Descriptions, inactive console text)
    *   `--border-tactical`: `#2D3748` (1px sharp borders used everywhere for the grid)

---

## 3. Typography Architecture

We use a dual-font system to separate narrative context from technical data.

1.  **Headers & Narrative (`font-sans`): Space Grotesk**
    *   *Usage:* H1 to H6, quest titles, primary marketing copy.
    *   *Style:* Geometric, slightly brutalist. Tracking should be tight.
2.  **Data & UI Metrics (`font-mono`): JetBrains Mono (or Fira Code)**
    *   *Usage:* XP values, level numbers, timers, metadata tags, button labels masquerading as terminal commands, and telemetry overlays. 
    *   *Style:* Builds immediate "IDE trust." All data should look like readouts.

---

## 4. Layout Framework: The Tactical Bento Box

The frontend utilizes a rigid, 1px-bordered grid system. We are not using floating cards; we are using interlocking panes resembling an advanced terminal window.

### 4.1 Structural Edges
*   **Border Radius:** Maximum `2px` (Tailwind `rounded-sm`) on components. Most structural panes should be `0px`.
*   **Gutters:** Fixed `16px` or `24px` gaps. All panes must have a solid `--border-tactical` 1px stroke.

### 4.2 Dashboard Layout Topology
1.  **Global Status Bar (Top/Bottom Edge):** Mimics VS Code's bottom bar.
    *   Content: `[SYSTEM: NOMINAL]` | `[USER: ROGUE_DEV]` | `[LEVEL: 14]` | `[XP: ▓▓▓▓░ 85%]`
2.  **The Quest Hub (Center Left):**
    *   Displays current quests as technical Jira/Linear style tickets. Sub-labels use monospace: `[Type: Architecture]` `[Est Time: 25m]`.
    *   Action buttons have a terminal hover state: `> Execute_` where the underscore blinks.
3.  **The Architecture Blueprint / Skill DAG (Center Right):**
    *   A massive, interactive Directed Acyclic Graph. Nodes are sharp rectangles. 
    *   Completed nodes are Volt Lime. Active nodes pulse Forge Amber.
4.  **Telemetry Grid (Bottom):**
    *   GitHub-inspired commit heatmap using the Forge Amber scale (Black -> Deep Red -> Bright Orange -> Amber).
    *   "Boss Battle Preparedness" loading bar.

---

## 5. Component Specifics

*   **Buttons:** Completely flat. No drop shadows. 1px border. On hover, background fills with `--accent-forge` and text inverses, accompanied by a monospace `>` chevron appearing.
*   **Badges/Tags:** Monospace, all caps, enclosed in brackets. Example: `[ BACKEND ]`, `[ HARD ]`.
*   **Modals:** Instead of soft popups, modals should slide in like terminal side-drawers or command palettes, heavily distinct from the background layer via a 1px Volt Lime or Forge Amber border.

---

## 6. Motion & Physics (Framer Motion Specs)

Motion must feel mechanical, snappy, and deliberate. 

*   **Easing Curves (The "Clack"):** Use spring physics with high stiffness and high damping to eliminate floatiness.
    *   *Spec:* `transition={{ type: "spring", stiffness: 300, damping: 30 }}`
*   **Level-Up Sequence:** No confetti. Screen dims. A text deciphering animation runs (`[ 0x1A2F... decrypting... ]`). Then, the new Level number strikes the screen accompanied by a simulated mechanical terminal lock sound.
*   **Boss Battle Trigger:** "Lockdown Protocol." The standard interface dims, `--border-tactical` lines transition to `--accent-forge`, sidebars collapse, and a stark countdown timer begins.

---

## 7. Developer & Agent Directives

1.  **To `frontend-developer` and UI Agents:** When scaffolding Next.js/Tailwind components, read this file FIRST.
2.  **Tailwind Config:** Override default Tailwind radii and implement the CSS variables outlined in Section 2.
3.  **ShadCN:** If utilizing ShadCN components, run the CLI configuration to set radius to 0, and strip out all default shadow utilities. Replace default primary colors with the Forge/Volt palette.
4.  **Enforcement:** Any PR containing `bg-purple-500`, `rounded-xl`, or generic gradient text (`bg-gradient-to-r`) must be flagged and rejected by the `code-reviewer` agent.

---

## 8. Human Interactivity & "Dopamine" Engineering

While the aesthetic is strictly "Tactical IDE / Brutalist", the user experience MUST be highly interactive, responsive, and designed to trigger intense dopamine hits. The interface should feel alive, reacting to user input with satisfying, mechanical precision that makes the user want to click, complete, and interact.

### 8.1 Micro-Interactions & Hover States
*   **Mechanical Tactility:** Buttons and interactive elements should feel physical. On hover or active click, implement a slight inward sink (`whileTap={{ scale: 0.98 }}`) to mimic the actuation of a heavy mechanical keyboard switch.
*   **Data Reveal (The "Glitch"):** When hovering over locked data points (like a future skill node or hidden quest), briefly display a scramble of characters (e.g., `[ 0x4F8A... ]`) for 100ms before resolving to the actual text. This creates immediate, cinematic engagement.
*   **Target Locking:** Hovering over a quest card should instantly illuminate its border in Forge Amber (`#FF6B00`) and transition a subtle scanning line (`translate-x`) across the card, mimicking a targeting system.

### 8.2 Progress & Reward Mechanisms (The Dopamine Hit)
*   **Odometer / Tally Counters:** Numbers (XP, Streak, Level) must NEVER instantly switch from `1200` to `1500`. They must rapidly cycle or spin up sequentially like an electronic tally counter or terminal data readout. This visual momentum is highly satisfying.
*   **Chunked Progress Bars:** Instead of a smooth, fluid gradient fill, progress bars should fill in discrete graphical blocks (e.g., `[████████░░░░]`). When a block fills, it should hyper-flash Volt Lime (`#CCFF00`) at 150% brightness for 50ms before settling.
*   **The "Execution" Sequence:** When a user clicks "MARK COMPLETE" on a quest:
    1. The button text snaps from `> EXECUTE` to `[ RUNNING_PR0CESS... ]` with a blinking cursor.
    2. A high-speed progress bar sweeps across the button background.
    3. The entire card border violently flashes Volt Lime.
    4. A terminal-style log streams instantly below it: `> +120 XP SECURED. NODE ADVANCED.`.
    5. The card collapses and disappears using stiff spring physics.

### 8.3 Unlocks & Ceremonies
*   **Skill Mastery:** When a skill node hits 100%, trigger a "Decryption" ceremony. The node's text scrambles, the border pulses rapidly, and it locks permanently into Volt Lime with a satisfying visual shockwave pushing neighboring elements back 1px temporarily.
*   **Streak Extensions (The Power Surge):** Maintaining a streak should feel powerful. Extending a 7+ day streak should trigger a visual "Power Surge" across the interface—a brief 200ms wave of Forge Amber energy tracing along the 1px grid lines of the entire dashboard topology.