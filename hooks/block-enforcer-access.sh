#!/usr/bin/env bash
# Block Claude from reading files in ~/.claude-behavior-enforcer/
# This is a PreToolUse hook for Read|Glob|Grep|Bash tools.
# Ensures holdout isolation: Claude cannot see test specs or assertions.

set -euo pipefail

INPUT=$(cat)
ENFORCER_DIR="$HOME/.claude-behavior-enforcer"

# Extract file path or command from tool input
FILE_PATH=$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // .tool_input.path // .tool_input.pattern // .tool_input.command // ""' 2>/dev/null || echo "")

# Check if path references enforcer directory
if [[ "$FILE_PATH" == *".claude-behavior-enforcer"* ]] || [[ "$FILE_PATH" == *"claude-behavior-enforcer"* ]]; then
    cat <<'DENY'
{
  "decision": "deny",
  "reason": "Access to ~/.claude-behavior-enforcer/ is blocked (holdout isolation). Test specs and assertions must remain hidden from Claude."
}
DENY
    exit 0
fi

# Allow all other paths
exit 0
