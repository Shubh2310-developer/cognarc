#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════
# COGNARC — Full Python Dependency Installer
# Conda env: cognarc (Python 3.12)
# GPU: RTX 4050 Mobile | CUDA 13.2 | GCC 16.1 on system
#
# Usage:
#   bash scripts/setup/install-deps.sh          # MVP deps only (Phases 1-6)
#   bash scripts/setup/install-deps.sh --full   # + llama-cpp-python (Phase 8)
# ══════════════════════════════════════════════════════════════
set -e

INSTALL_LLAMA=false
[[ "$1" == "--full" ]] && INSTALL_LLAMA=true

# ── Guard: must be in cognarc conda env ──────────────────────
if [[ "$CONDA_DEFAULT_ENV" != "cognarc" ]]; then
    echo "❌  Not in the cognarc conda environment."
    echo "    Run: conda activate cognarc"
    exit 1
fi

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║      COGNARC Python Dependency Installer             ║"
echo "║      Python : $(python --version)                   ║"
echo "║      Env    : $CONDA_DEFAULT_ENV                     ║"
echo "║      Mode   : $([ "$INSTALL_LLAMA" = true ] && echo "Full (+ llama-cpp)" || echo "MVP (Phases 1-6)")                  ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# ── Step 1: Upgrade pip ──────────────────────────────────────
echo "▶  [1/5] Upgrading pip..."
pip install --upgrade pip --quiet
echo "✅  pip upgraded"

# ── Step 2: PyTorch with CUDA 12.4 (latest for cu124 index) ──
echo ""
echo "▶  [2/5] Installing PyTorch 2.6.0 (CUDA 12.4 build)..."
echo "   (CUDA 12.4 build is backward-compatible with your CUDA 13.2 driver)"
pip install torch==2.6.0 torchvision==0.21.0 \
    --index-url https://download.pytorch.org/whl/cu124 \
    --quiet
echo "✅  PyTorch installed"

# ── Step 3: FastAPI backend deps (prod + dev) ────────────────
echo ""
echo "▶  [3/5] Installing API dependencies (prod + dev)..."
pip install -r apps/api/requirements.dev.txt --quiet
echo "✅  API dependencies installed"

# ── Step 4: AI Services deps ─────────────────────────────────
echo ""
echo "▶  [4/5] Installing AI Services dependencies..."
pip install -r ai-services/requirements.txt --quiet
echo "✅  AI Services dependencies installed"

# ── Step 5: llama-cpp-python (Phase 8 only — needs gcc13) ────
if [[ "$INSTALL_LLAMA" == "true" ]]; then
    echo ""
    echo "▶  [5/5] Building llama-cpp-python with CUDA support..."
    echo "   Requires gcc13 (CUDA 13.2 incompatible with system GCC 16)"

    # Auto-detect gcc13 or gcc14
    CUDA_HOST_CXX=""
    if command -v g++-13 &>/dev/null; then
        CUDA_HOST_CXX=$(which g++-13)
        echo "   Found g++-13 → $CUDA_HOST_CXX"
    elif command -v g++-14 &>/dev/null; then
        CUDA_HOST_CXX=$(which g++-14)
        echo "   Found g++-14 → $CUDA_HOST_CXX"
    else
        echo ""
        echo "   ❌  g++-13 not found. Install it first:"
        echo "       sudo pacman -S gcc13"
        echo ""
        echo "   Then re-run: bash scripts/setup/install-deps.sh --full"
        echo ""
        echo "   ⚠️  Skipping llama-cpp-python for now."
        echo "   Note: This is only needed in Phase 8 (Phi-2 local fallback)."
        echo "   You can start building MVP (Phases 1-6) without it."
        INSTALL_LLAMA=false
    fi

    if [[ "$INSTALL_LLAMA" == "true" ]]; then
        CMAKE_ARGS="-DGGML_CUDA=on" \
        CUDAHOSTCXX="$CUDA_HOST_CXX" \
        pip install llama-cpp-python==0.3.8 \
            --no-cache-dir --quiet
        echo "✅  llama-cpp-python installed (CUDA-enabled via $CUDA_HOST_CXX)"
    fi
else
    echo ""
    echo "▶  [5/5] Skipping llama-cpp-python (MVP mode — not needed until Phase 8)"
    echo "   When ready for Phase 8, run:"
    echo "   1. sudo pacman -S gcc13"
    echo "   2. bash scripts/setup/install-deps.sh --full"
fi

# ── Final Verification ───────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║  Verification                                        ║"
echo "╚══════════════════════════════════════════════════════╝"
python -c "import fastapi;      print(f'  ✅  fastapi              {fastapi.__version__}')"
python -c "import pydantic;     print(f'  ✅  pydantic             {pydantic.__version__}')"
python -c "import motor;        print(f'  ✅  motor                {motor.version}')"
python -c "import groq;         print(f'  ✅  groq                 installed')"
python -c "import torch;        print(f'  ✅  torch                {torch.__version__}')"
python -c "
import torch
avail = torch.cuda.is_available()
gpu   = torch.cuda.get_device_name(0) if avail else 'N/A'
print(f'  ✅  CUDA available       {avail}')
print(f'  ✅  GPU                  {gpu}')
"
python -c "import sentence_transformers; print(f'  ✅  sentence-transformers installed')"

echo ""
if [[ "$1" == "--full" && "$INSTALL_LLAMA" == "true" ]]; then
    python -c "import llama_cpp; print(f'  ✅  llama-cpp-python     installed')" 2>/dev/null || \
        echo "  ⚠️  llama-cpp-python     not installed (Phase 8 only)"
fi

echo ""
echo "🚀  Done! All MVP dependencies installed."
echo "    Start building: make dev"
echo ""
