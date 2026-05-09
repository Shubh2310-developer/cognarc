# ══════════════════════════════════════════════════════════════
# COGNARC — Makefile
# Conda env: cognarc | Python 3.12 | RTX 4050 CUDA 13.2
# ══════════════════════════════════════════════════════════════

.PHONY: install install-no-gpu dev test lint format build deploy health clean help

# ── Default ───────────────────────────────────────────────────
help:
	@echo ""
	@echo "  COGNARC Makefile Commands"
	@echo "  ─────────────────────────────────────────────────"
	@echo "  make install        Full Python install (GPU + llama-cpp)"
	@echo "  make install-no-gpu Skip PyTorch GPU & llama-cpp build"
	@echo "  make dev            Start all services (Docker Compose)"
	@echo "  make test           Run all tests (pytest + vitest)"
	@echo "  make lint           Lint all code (ruff + eslint)"
	@echo "  make format         Format code (ruff + prettier)"
	@echo "  make health         Smoke-test local services"
	@echo "  make clean          Remove build artifacts & cache"
	@echo "  make deploy-api     Deploy API to Railway"
	@echo "  make deploy-web     Deploy web to Vercel"
	@echo ""

# ── Install ───────────────────────────────────────────────────
install: ## MVP deps only — safe default (Phases 1-6, no llama-cpp)
	@bash scripts/setup/install-deps.sh

install-full: ## Full install incl. llama-cpp-python (Phase 8)
	@echo "⚠️  Requires gcc13: sudo pacman -S gcc13"
	@bash scripts/setup/install-deps.sh --full

gcc13: ## Install gcc13 from AUR (EndeavourOS/Arch — required for llama-cpp CUDA)
	yay -S gcc13 --noconfirm

# ── Phase-gated installs (FROZEN until gate conditions met) ───
install-phase7: ## Phase 7 — Celery worker (after 14 days stable MVP)
	@echo "⚠️  GATE: MVP must be stable for 14+ days before installing Phase 7 deps"
	pip install -r apps/worker/requirements.txt

install-phase8: ## Phase 8 — Evaluation engine (after Phase 7 stable)
	@echo "⚠️  GATE: Phase 7 must be stable before installing Phase 8 deps"
	@echo "⚠️  llama-cpp-python requires: sudo pacman -S gcc13"
	pip install -r ai-services/requirements.phase8.txt

install-phase9: ## Phase 9 — Advanced gamification (after Phase 8 stable)
	@echo "⚠️  GATE: Phase 8 must be stable before installing Phase 9 deps"
	pip install -r ai-services/requirements.phase9.txt

install-phase10: ## Phase 10 — Agentic orchestration (30 days stable Phases 6-9)
	@echo "⚠️  GATE: Phases 6-9 must be stable for 30+ days before Phase 10"
	pip install -r ai-services/requirements.phase10.txt

install-all: ## Install ALL phase deps now (dev env setup — skip llama-cpp)
	@echo ""
	@echo "╔══════════════════════════════════════════════════════╗"
	@echo "║  COGNARC — Installing ALL phase dependencies               ║"
	@echo "║  Phase gates apply to DEPLOYMENT, not pip installs         ║"
	@echo "╚══════════════════════════════════════════════════════╝"
	@echo ""
	@echo "▶  [Step 1/6] MVP deps (Phases 1–6) + PyTorch CUDA 12.4..."
	@bash scripts/setup/install-deps.sh
	@echo ""
	@echo "▶  [Step 2/6] Phase 7: Celery worker deps..."
	-pip install -r apps/worker/requirements.txt --quiet
	@echo "✅  Phase 7 done (or skipped on network error — re-run if needed)"
	@echo ""
	@echo "▶  [Step 3/6] Phase 8: Evaluation + behavioral engine deps..."
	-pip install -r ai-services/requirements.phase8.txt --quiet
	@echo "✅  Phase 8 done (or skipped on network error — re-run if needed)"
	@echo ""
	@echo "▶  [Step 4/6] Phase 9: Advanced gamification deps..."
	-pip install -r ai-services/requirements.phase9.txt --quiet
	@echo "✅  Phase 9 done (or skipped on network error — re-run if needed)"
	@echo ""
	@echo "▶  [Step 5/6] Phase 10: LangGraph + agentic orchestration deps..."
	-pip install -r ai-services/requirements.phase10.txt --quiet
	@echo "✅  Phase 10 done (or skipped on network error — re-run if needed)"
	@echo ""
	@echo "▶  [Step 6/6] llama-cpp-python (Phase 8 Phi-2 fallback)..."
	@if command -v g++-13 &>/dev/null; then \
		echo "   g++-13 found — building with CUDA..."; \
		CMAKE_ARGS="-DGGML_CUDA=on" CUDAHOSTCXX=$$(which g++-13) \
		pip install llama-cpp-python==0.3.8 --no-cache-dir --quiet && \
		echo "✅  llama-cpp-python installed (CUDA)"; \
	else \
		echo "⚠️  g++-13 not found — skipping llama-cpp-python"; \
		echo "   Fix: sudo pacman -S gcc13  then re-run: make install-all"; \
	fi
	@echo ""
	@echo "🚀  ALL dependencies installed. Run: make dev"
	@echo ""

# ── Development ───────────────────────────────────────────────
dev:
	docker compose -f docker-compose.dev.yml up -d
	@echo "✅  Services starting..."
	@echo "    API  → http://localhost:8000"
	@echo "    Web  → http://localhost:3000"

dev-down:
	docker compose -f docker-compose.dev.yml down

dev-logs:
	docker compose -f docker-compose.dev.yml logs -f api

# ── Testing ───────────────────────────────────────────────────
test:
	cd apps/api && pytest tests/ -v --cov=app --cov-report=term-missing
	pnpm run test --filter=web

test-api:
	cd apps/api && pytest tests/ -v

test-web:
	pnpm run test --filter=web

test-e2e:
	pnpm run test:e2e --filter=web

# ── Linting ───────────────────────────────────────────────────
lint:
	cd apps/api && ruff check app/
	cd apps/api && mypy app/
	pnpm run lint

lint-api:
	cd apps/api && ruff check app/ && mypy app/

lint-web:
	pnpm run lint --filter=web

# ── Formatting ────────────────────────────────────────────────
format:
	cd apps/api && ruff format app/
	pnpm run format

# ── Health Checks ─────────────────────────────────────────────
health:
	@echo "Checking local services..."
	@curl -sf http://localhost:8000/health       && echo "✅  API alive" || echo "❌  API down"
	@curl -sf http://localhost:8000/health/ready && echo "✅  API ready" || echo "❌  API not ready"
	@curl -sf http://localhost:3000             && echo "✅  Web alive" || echo "❌  Web down"

# ── Deployment ────────────────────────────────────────────────
deploy-api:
	railway up --service cognarc-api

deploy-web:
	vercel --prod

# ── Cleanup ───────────────────────────────────────────────────
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .next -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name dist -exec rm -rf {} + 2>/dev/null || true
	@echo "✅  Cleaned"
