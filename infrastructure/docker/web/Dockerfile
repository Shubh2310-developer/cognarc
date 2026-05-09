# ══════════════════════════════════════════════════════════════
# COGNARC — Next.js Web Dockerfile (Production)
# infrastructure/docker/web/ — referenced by docker-compose.yml
# T1.13: Multi-stage Next.js build (node:20-alpine)
# ══════════════════════════════════════════════════════════════

FROM node:20-alpine AS base

RUN apk add --no-cache libc6-compat curl

# Install pnpm
RUN corepack enable && corepack prepare pnpm@10.33.4 --activate

WORKDIR /app

# ── Dependency Layer ──────────────────────────────────────────
FROM base AS deps

# Copy workspace manifests for pnpm to resolve packages
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
COPY packages/shared-types/package.json ./packages/shared-types/
COPY packages/design-tokens/package.json ./packages/design-tokens/
COPY packages/logger/package.json ./packages/logger/
COPY packages/auth-client/package.json ./packages/auth-client/ 2>/dev/null || true

COPY apps/web/package.json ./apps/web/

RUN pnpm install --frozen-lockfile

# ── Builder Layer ─────────────────────────────────────────────
FROM deps AS builder

COPY . .

ENV NEXT_TELEMETRY_DISABLED=1

RUN pnpm --filter web run build

# ── Runner Layer ──────────────────────────────────────────────
FROM base AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Non-root user
RUN addgroup --system --gid 1001 nodejs \
    && adduser --system --uid 1001 nextjs

# Copy standalone build output
COPY --from=builder /app/apps/web/.next/standalone ./
COPY --from=builder /app/apps/web/.next/static ./apps/web/.next/static
COPY --from=builder /app/apps/web/public ./apps/web/public

USER nextjs

EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:3000 || exit 1

CMD ["node", "apps/web/server.js"]
