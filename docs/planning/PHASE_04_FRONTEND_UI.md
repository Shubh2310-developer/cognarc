# PHASE 04 — FRONTEND UI
> **COGNARC Engineering Governance | Phase 4 of 10**
> Agents: `frontend-developer` · `nextjs-developer` · `typescript-pro` · `gsd-planner`
> Skills: `senior-architect` · `gepetto` · `ui-design-system` · `frontend-design` · `tailwind-patterns`

---

## Phase Goal

Build the complete Next.js 14 App Router dashboard — with feature-first folder structure, Zustand global stores, React Query data fetching, Dexie.js IndexedDB offline cache, and a fully functional quest display + XP/streak UI — such that a user can log in, view 3 AI-generated quests, mark one done, and see XP update without page reload.

---

## Architectural Rules Addressed

| Rule (CLAUDE.md) | Constraint |
|---|---|
| §05 Feature-First Structure | Every feature in `features/<name>/` with `components/`, `hooks/`, `stores/`, `types/`, `api/`, `utils/`, `tests/` |
| §05 State Management | Zustand for global (XP/level/streak). React Query for server data. Dexie for offline. Never Redux. |
| §05 Next.js 14 Rules | App Router only. Server Components by default. `'use client'` only for interactivity. |
| §05 Design System | All tokens from `packages/design-tokens/`. Never hardcode hex values. |
| §05 API Layer Rule | NEVER make raw `fetch`/`axios` calls from components. All calls via `features/<name>/api/`. |
| §14 MVP Simplifications | No Framer Motion, no interactive DAG viz, no boss battles, no leaderboard in this phase. |
| §17 Naming Conventions | Components: `PascalCase.tsx`. Hooks: `camelCase.ts`. Stores: `use<Name>Store.ts`. |

---

## Task Breakdown (Checklist)

### Design System Foundation

- [ ] **T1.1** Populate `packages/design-tokens/src/tokens.css` with all §05 CSS variables:
  ```css
  :root {
    --color-primary: #6D28D9;
    --color-accent: #D97706;
    --color-surface-dark: #0F0F1A;
    --color-surface-card: #1A1A2E;
    --color-text-primary: #F8FAFC;
    --color-text-secondary: #94A3B8;
    --color-success: #10B981;
    --color-warning: #F59E0B;
    --color-danger: #EF4444;
    --font-heading: 'Space Grotesk', sans-serif;
    --font-body: 'Inter', sans-serif;
  }
  ```
- [ ] **T1.2** Import Google Fonts (Space Grotesk + Inter) in `apps/web/src/app/layout.tsx`
- [ ] **T1.3** Configure `tailwind.config.ts` to reference CSS variables for all custom colors
- [ ] **T1.4** Create `apps/web/src/styles/globals.css` — base reset + typography scale

### Feature-First Directory Structure

- [ ] **T2.1** Create feature directories under `apps/web/src/features/`:
  - `auth/`, `quests/`, `gamification/`, `skill-tree/`, `analytics/`, `notifications/`, `onboarding/`
  - Each with sub-dirs: `components/`, `hooks/`, `stores/`, `types/`, `api/`, `utils/`, `tests/`

- [ ] **T2.2** Create `apps/web/src/shared/` with:
  - `stores/` — global Zustand stores
  - `components/` — shared UI primitives
  - `hooks/` — shared custom hooks (e.g., `useDebounce`, `useLocalStorage`)
  - `utils/` — shared utilities (date, format, validation)
  - `utils/db.ts` — Dexie.js IndexedDB configuration

### Shared Zustand Stores

- [ ] **T3.1** Create `apps/web/src/shared/stores/useUserStore.ts`
  ```typescript
  import { create } from 'zustand'
  import { persist } from 'zustand/middleware'

  interface UserState {
    userId: string | null
    username: string | null
    level: number
    totalXp: number
    streak: number
    activeSkillTree: string
    setUser: (user: Partial<UserState>) => void
    clearUser: () => void
  }

  export const useUserStore = create<UserState>()(
    persist(
      (set) => ({
        userId: null, username: null, level: 1, totalXp: 0,
        streak: 0, activeSkillTree: 'AI Engineering',
        setUser: (user) => set((state) => ({ ...state, ...user })),
        clearUser: () => set({ userId: null, username: null }),
      }),
      { name: 'cognarc-user' }
    )
  )
  ```

- [ ] **T3.2** Create `apps/web/src/shared/stores/useGamificationStore.ts`
  - State: `totalXp`, `level`, `xpForNextLevel`, `progressPct`, `streak`, `streakMultiplier`
  - Actions: `awardXp(amount: number)`, `updateStreak(count: number)`
  - Pure level computation: `Math.floor((totalXp / 100) ** (1 / 1.8))`

- [ ] **T3.3** Configure `zustand/middleware/devtools` for development only

### Dexie.js Offline Cache

- [ ] **T4.1** Implement `apps/web/src/shared/utils/db.ts`
  ```typescript
  import Dexie, { Table } from 'dexie'

  export interface CachedQuest { id?: number; questId: string; data: object; cachedAt: Date }
  export interface PendingSync { id?: number; action: string; payload: object; createdAt: Date }

  class CognarcDB extends Dexie {
    quests!: Table<CachedQuest>
    pendingSync!: Table<PendingSync>

    constructor() {
      super('CognarcDB')
      this.version(1).stores({
        quests: '++id, questId, cachedAt',
        pendingSync: '++id, action, createdAt'
      })
    }
  }

  export const db = new CognarcDB()
  ```

- [ ] **T4.2** Create `apps/web/src/features/quests/utils/questCache.ts`
  - `cacheQuests(quests: Quest[]) → Promise<void>`
  - `getCachedQuests() → Promise<Quest[] | null>`
  - `clearExpiredQuests() → Promise<void>` (remove quests older than 24h)

### Quest Feature Components

- [ ] **T5.1** Create `apps/web/src/features/quests/api/questsApi.ts`
  ```typescript
  export async function generateQuests(): Promise<Quest[]> {
    const res = await fetch(`${API_BASE}/quests/generate`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${getToken()}` }
    })
    if (!res.ok) throw new Error('Quest generation failed')
    return res.json()
  }

  export async function completeQuest(questId: string): Promise<XpResult> {
    const res = await fetch(`${API_BASE}/quests/${questId}/evaluate`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${getToken()}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ self_report: true })
    })
    return res.json()
  }
  ```

- [ ] **T5.2** Create `apps/web/src/features/quests/hooks/useQuests.ts` — React Query hook
  ```typescript
  export function useQuests() {
    return useQuery({
      queryKey: ['quests', 'today'],
      queryFn: async () => {
        try { return await generateQuests() }
        catch { return getCachedQuests() }
      },
      staleTime: 1000 * 60 * 60,  // 1 hour
    })
  }
  ```

- [ ] **T5.3** Create `apps/web/src/features/quests/components/QuestCard.tsx`
  - Display: title, type badge (color-coded), difficulty pill, XP reward, estimated minutes
  - Action: "Mark Complete" button → triggers `completeQuest()` → updates `useGamificationStore`
  - Loading: skeleton state while fetching
  - Error: offline fallback message if API unreachable

- [ ] **T5.4** Create `apps/web/src/features/quests/components/QuestList.tsx`
  - Renders 3 `QuestCard` components
  - Shows "Generating your quests..." skeleton on first load
  - Shows "Quests loaded from offline cache" banner if offline

### Gamification Feature Components

- [ ] **T6.1** Create `apps/web/src/features/gamification/components/XpBar.tsx`
  - Display: current XP / XP for next level, progress percentage
  - MVP: static CSS width transition (no Framer Motion yet)
  - Uses `useGamificationStore` for live XP value

- [ ] **T6.2** Create `apps/web/src/features/gamification/components/LevelBadge.tsx`
  - Display: level number + tier name (Apprentice/Practitioner/Engineer etc.)

- [ ] **T6.3** Create `apps/web/src/features/gamification/components/StreakDisplay.tsx`
  - Display: 🔥 flame emoji + streak count + "day streak"
  - Color: gold (`--color-accent`) on streak > 0

### Dashboard Page

- [ ] **T7.1** Create `apps/web/src/app/(dashboard)/page.tsx` — Server Component
  - Layout per §31 dashboard design: header (XP bar + level + streak + avatar), quest panel, skill tree sidebar, streak/boss/leaderboard row

- [ ] **T7.2** Create `apps/web/src/app/(dashboard)/layout.tsx` — authenticated layout wrapper
  - Check session; redirect to `/login` if none (via `middleware.ts`)

- [ ] **T7.3** Create `apps/web/src/app/(auth)/login/page.tsx` — Magic link login form
  - Input: email → Supabase `signInWithOtp()` → "Check your email" confirmation

- [ ] **T7.4** Create `apps/web/src/app/(auth)/callback/page.tsx` — Supabase auth callback handler

### Skill Tree (MVP — Text Display Only)

- [ ] **T8.1** Create `apps/web/src/features/skill-tree/components/SkillTreeSidebar.tsx`
  - MVP: text list showing current node (◎), mastered nodes (✓), locked nodes (○)
  - No interactive DAG visualization — that is Phase 3
  - Data from `GET /skills/tree` via React Query

### React Query Provider + App Shell

- [ ] **T9.1** Create `apps/web/src/app/providers.tsx` — `'use client'` wrapper
  - `QueryClientProvider` + `QueryClient` configuration
  - Zustand store hydration

- [ ] **T9.2** Update `apps/web/src/app/layout.tsx` — wrap with `<Providers>`

---

## Data Flow & Dependencies

```
[Next.js App Router]
  Server Component (page.tsx)
  └── renders layout + passes to Client Components

[features/quests/hooks/useQuests.ts]  (React Query)
  ├── Cache HIT (React Query staleTime) → render immediately
  ├── Cache MISS → features/quests/api/questsApi.ts
  │                   └── POST /quests/generate → FastAPI
  │                                │ JWT in header
  │                                ▼
  │                         [Quest objects JSON]
  │                                │
  │                   ┌───────────▼──────────────┐
  │                   │ Dexie IndexedDB (offline) │
  │                   │ React Query cache (60min) │
  │                   └──────────────────────────┘
  └── Error → getCachedQuests() → Dexie fallback

[features/gamification/components/XpBar.tsx]
  └── useGamificationStore (Zustand) → live XP value
  └── completeQuest() → POST /quests/{id}/evaluate
                      → awardXp() → Zustand state update
                      → React Query invalidate ['quests','today']
```

**Dependency Order:**
1. Phase 1 (Auth) complete → `middleware.ts` and auth-client work
2. Phase 2 (Data) complete → API returns real MongoDB data
3. Phase 3 (AI) complete → `/quests/generate` returns real quests
4. `packages/design-tokens/` populated → before any styled component

---

## Testing & Observability

### Required Tests

| Test | Tool | File | Target |
|---|---|---|---|
| `QuestCard` renders with mock data | Vitest + Testing Library | `features/quests/tests/QuestCard.test.tsx` | 100% |
| `QuestCard` "Mark Complete" triggers mutation | Vitest | `features/quests/tests/QuestCard.test.tsx` | 100% |
| `useGamificationStore` `awardXp()` updates level | Vitest | `shared/stores/tests/gamification.test.ts` | 100% |
| `XpBar` renders correct progress % | Vitest | `features/gamification/tests/XpBar.test.tsx` | 100% |
| Dexie cache stores and retrieves quests | Vitest | `features/quests/tests/questCache.test.ts` | 90% |
| Login page renders email input | Vitest | `auth/tests/LoginPage.test.tsx` | 100% |
| `middleware.ts` redirects unauthenticated | Vitest | `tests/unit/middleware.test.ts` | 100% |

### E2E Tests (Day 7 Gate)

- [ ] Write `apps/web/tests/e2e/dashboard.spec.ts` (Playwright):
  - Login via magic link mock
  - Dashboard loads with 3 quest cards
  - Click "Mark Complete" on quest 1
  - XP counter updates on page (no reload)

### Observability

- [ ] Track `quest_viewed`, `quest_completed`, `xp_awarded` events in frontend analytics
- [ ] Log React Query cache hit/miss ratio in development console (structured)
- [ ] Sentry configured for browser error capture with `user_id` context

---

## Validation Gate

**Phase 4 is DONE when ALL pass:**

```bash
# 1. Type check
cd apps/web && npx tsc --noEmit         # 0 errors

# 2. Lint
cd apps/web && npm run lint              # 0 warnings

# 3. Unit tests
cd apps/web && npm run test              # All Vitest tests green

# 4. Manual browser test (Day 7 gate):
# Open http://localhost:3000
# → Login page loads
# → Enter email → "Check your email" shown
# → Click magic link → redirected to /dashboard
# → 3 quest cards visible with type/difficulty/XP data
# → Click "Mark Complete" on any quest → XP bar updates
# → No console errors (no raw fetch from components)

# 5. Offline test:
# Load dashboard → open DevTools → go Offline → refresh
# → Quests still visible from Dexie cache
# → "Offline" banner visible
```

---

## Absolute 'Do-Not-Do' List for Phase 4

| Forbidden | Reason |
|---|---|
| ❌ Framer Motion animations | Phase 3 (COGNARC Phase 3). Toast only in MVP §14. |
| ❌ Interactive DAG skill tree | Phase 3. Text list is the MVP implementation §14. |
| ❌ Boss battle UI | Phase 3 §13 |
| ❌ Leaderboard page | Phase 3 §13 |
| ❌ Badge/achievement display | Phase 3 §13 |
| ❌ Raw `fetch`/`axios` in React components | Must use `features/<name>/api/` layer §05 |
| ❌ Redux or MobX | Zustand only §05, §27 |
| ❌ Calling AI endpoints directly from frontend | Always via backend API §05 |
| ❌ Server state and Zustand holding same data | Separate concerns §05 |
| ❌ Hardcoded hex color values in components | Use design token CSS variables §05 |
| ❌ Raw `<img>` tags | Use `next/image` §05 |
| ❌ Pages Router (`pages/` directory) | App Router only §05 |
| ❌ `'use client'` on Server Components | Only add when interactivity required §05 |

---

*Phase 4 Target: Days 7–8 (within MVP window)*
*Owner: `frontend-developer` · `nextjs-developer` · `typescript-pro`*
*Next: [PHASE_05_MVP_GAMIFICATION.md](./PHASE_05_MVP_GAMIFICATION.md)*
