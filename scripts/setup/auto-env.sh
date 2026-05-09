#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════
# COGNARC — Conda Auto-Activation via PROMPT_COMMAND
# ══════════════════════════════════════════════════════════════
#
# HOW TO INSTALL (one-time, run this file directly):
#   source /home/agentrogue/cognarc/scripts/setup/auto-env.sh
#
# Or paste the block below manually into your ~/.bashrc
# (after the `conda init` block)
# ══════════════════════════════════════════════════════════════

BASHRC="$HOME/.bashrc"

# The block to insert
read -r -d '' SNIPPET << 'SNIPPET_END'

# ── COGNARC: Auto-activate conda env when inside project ─────
_cognarc_auto_conda() {
    if [[ "$PWD" == /home/agentrogue/cognarc* ]]; then
        if [[ "$CONDA_DEFAULT_ENV" != "cognarc" ]]; then
            conda activate cognarc
        fi
    else
        if [[ "$CONDA_DEFAULT_ENV" == "cognarc" ]]; then
            conda activate base
        fi
    fi
}
# Prepend to PROMPT_COMMAND so it runs before conda's own hook
PROMPT_COMMAND="_cognarc_auto_conda${PROMPT_COMMAND:+; $PROMPT_COMMAND}"
# ── END COGNARC auto-activation ───────────────────────────────
SNIPPET_END

# Only add if not already present
if grep -q "_cognarc_auto_conda" "$BASHRC"; then
    echo "✅ Auto-activation already installed in ~/.bashrc"
else
    echo "$SNIPPET" >> "$BASHRC"
    echo "✅ Added cognarc auto-activation to ~/.bashrc"
    echo "   Run: source ~/.bashrc  — then cd out and back in."
fi
