#!/bin/bash
# PreToolUse hook: block access to ~/.claude-behavior-enforcer/
# Prevents Claude from reading test specs, assertions, fixtures, or results.
# The skill is discovered via symlink at ~/.claude/skills/ (separate path, not affected).

INPUT=$(cat)
TOOL=$(echo "$INPUT" | jq -r '.tool_name // empty')

# Allow if Claude is started from within the enforcer directory (test runs)
if echo "$PWD" | grep -q '\.claude-behavior-enforcer'; then
  exit 0
fi

# Block any access to the enforcer directory
HOLDOUT_PATTERN='\.claude-behavior-enforcer'

check_path() {
  if echo "$1" | grep -qE "$HOLDOUT_PATTERN"; then
    echo "Blocked: enforcer holdout directory is off-limits" >&2
    exit 2
  fi
}

check_bash_cmd() {
  if echo "$1" | grep -qE "(cd|cat|ls|find|head|tail|less|more|source|\.)\s+\S*$HOLDOUT_PATTERN"; then
    echo "Blocked: enforcer holdout directory is off-limits" >&2
    exit 2
  fi
}

case "$TOOL" in
  Read)
    check_path "$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')"
    ;;
  Glob)
    check_path "$(echo "$INPUT" | jq -r '.tool_input.pattern // empty')"
    check_path "$(echo "$INPUT" | jq -r '.tool_input.path // empty')"
    ;;
  Grep)
    check_path "$(echo "$INPUT" | jq -r '.tool_input.path // empty')"
    ;;
  Bash)
    check_bash_cmd "$(echo "$INPUT" | jq -r '.tool_input.command // empty')"
    ;;
esac

exit 0
