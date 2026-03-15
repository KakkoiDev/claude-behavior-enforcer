#!/bin/bash
# PreToolUse hook: block access to enforcer holdout directories
# Prevents Claude from reading test specs, assertions, fixtures, or results.
# ALLOWS access to: skill/ (Claude needs to read SKILL.md to use the skill)

INPUT=$(cat)
TOOL=$(echo "$INPUT" | jq -r '.tool_name // empty')

# Allow if Claude is started from within the enforcer directory (test runs)
if echo "$PWD" | grep -q '\.claude-behavior-enforcer'; then
  exit 0
fi

# Holdout paths that must be hidden from Claude
# skill/ is NOT blocked - Claude needs it to operate the enforcer
HOLDOUT_PATTERN='\.claude-behavior-enforcer/(requirements|fixtures|grader|enforcer|hooks|results|config\.yaml|bin)'

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
