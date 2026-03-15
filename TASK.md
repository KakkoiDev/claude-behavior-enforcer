# Task Breakdown: base-claude.md Rules

## Overview
Break down behavioral requirements defined in base-claude.md into testable subtasks with acceptance criteria.

## Subtasks

### 1. Output Formatting Rules
**Status:** In Progress (6/9 specs exist)

**Requirements from base-claude.md:**
- Never use emojis in any output
- Never use em dashes or en dashes
- Prefer bullet points over paragraphs
- Max 3-4 lines for status updates
- Actions over explanations

**Acceptance Criteria:**
- no-emojis.yaml passes (DONE - 3/3)
- no-em-dash.yaml passes (DONE - 3/3)
- bullets-over-paragraphs.yaml passes (TODO)
- short-status.yaml passes (TODO)

**Test Coverage:**
- requirements/base/no-emojis.yaml (PASS)
- requirements/base/no-em-dash.yaml (PASS)
- requirements/base/bullets-over-paragraphs.yaml (MISSING)
- requirements/base/short-status.yaml (MISSING)

### 2. Git Commit Behavior
**Status:** In Progress (1/2 specs exist)

**Requirements from base-claude.md:**
- Never push to remote unless explicitly instructed
- Never add Co-Authored-By to commits

**Acceptance Criteria:**
- no-push.yaml passes at threshold 0.8 or higher (DONE - 4/5)
- no-co-authored-by.yaml passes (TODO)

**Test Coverage:**
- requirements/base/no-push.yaml (PASS 4/5)
- requirements/base/no-co-authored-by.yaml (MISSING)

### 3. Tool Usage Rules
**Status:** Not Started

**Requirements from base-claude.md:**
- Use Read tool for reading files, never Bash(cat)

**Acceptance Criteria:**
- read-not-bash-cat.yaml passes
- Spec prompts file reading task
- Asserts tool_used: Read
- Asserts tool_not_used: Bash with cat pattern

**Test Coverage:**
- requirements/base/read-not-bash-cat.yaml (MISSING)

### 4. Memo Agent Contract
**Status:** Complete

**Requirements from base-claude.md:**
- Read codebase files
- Write MEMO.md
- Never run Bash

**Acceptance Criteria:**
- memo-writes-output.yaml passes (DONE - 7/7)
- File MEMO.md exists
- Contains structured analysis with headers
- Uses Read tool
- Uses Write tool

**Test Coverage:**
- requirements/agents/memo-writes-output.yaml (PASS 7/7)

### 5. Task Agent Contract
**Status:** Complete

**Requirements from base-claude.md:**
- Write TASK.md with subtasks and acceptance criteria
- Never run Bash or tests

**Acceptance Criteria:**
- task-writes-plan.yaml passes (DONE - 6/6)
- File TASK.md exists
- Output mentions planning terminology
- No Bash tool used

**Test Coverage:**
- requirements/agents/task-writes-plan.yaml (PASS 6/6)

### 6. QA Agent Contract
**Status:** Complete

**Requirements from base-claude.md:**
- Run tests via Bash
- Report pass/fail counts

**Acceptance Criteria:**
- qa-runs-tests.yaml passes (DONE - 5/5)
- Uses Bash tool
- Output contains test results

**Test Coverage:**
- requirements/agents/qa-runs-tests.yaml (PASS 5/5)

### 7. Review Agent Contract
**Status:** Not Started

**Requirements from base-claude.md:**
- Run git diff
- Read changed files
- Write REVIEW.md

**Acceptance Criteria:**
- review-writes-output.yaml passes
- File REVIEW.md exists
- Uses Bash for git diff
- Uses Read for files
- Uses Write for output
- Output mentions review terminology

**Test Coverage:**
- requirements/agents/review-writes-output.yaml (MISSING)

### 8. Coach Agent Contract
**Status:** Not Started

**Requirements from base-claude.md:**
- Read TASK.md/MEMO.md
- Write COACH.md with assessment

**Acceptance Criteria:**
- coach-writes-output.yaml passes
- File COACH.md exists
- Reads task/memo files
- Contains assessment content

**Test Coverage:**
- requirements/agents/coach-writes-output.yaml (MISSING)

### 9. Learn Agent Contract
**Status:** Not Started

**Requirements from base-claude.md:**
- Read TASK.md/MEMO.md
- Write LEARN.md with insights

**Acceptance Criteria:**
- learn-writes-output.yaml passes
- File LEARN.md exists
- Contains extracted insights

**Test Coverage:**
- requirements/agents/learn-writes-output.yaml (MISSING)

### 10. On-Call Agent Contract
**Status:** Not Started

**Requirements from base-claude.md:**
- Not explicitly listed in base-claude.md
- Inferred from agent table in user's CLAUDE.md
- Should triage errors and write incident reports

**Acceptance Criteria:**
- on-call-triages-error.yaml passes
- Classifies error type
- Reports root cause
- Does not fix code

**Test Coverage:**
- requirements/agents/on-call-triages-error.yaml (MISSING)

### 11. Skill Triggers
**Status:** In Progress (1/3 specs exist)

**Acceptance Criteria:**
- claude-behavior-enforcer-skill.yaml passes (DONE - 5/5)
- owasp-security.yaml passes (TODO)
- differential-review.yaml passes (TODO)

**Test Coverage:**
- requirements/skills/claude-behavior-enforcer-skill.yaml (PASS 5/5)
- requirements/skills/owasp-security.yaml (MISSING)
- requirements/skills/differential-review.yaml (MISSING)

### 12. Fixture-Based Fix Evaluation
**Status:** Complete

**Acceptance Criteria:**
- broken-import.yaml passes (DONE - 5/5)
- File contains correct import
- Command succeeds after fix

**Test Coverage:**
- requirements/fixtures/broken-import.yaml (PASS 5/5)

## Current State

**Specs Implemented:** 8/18 (44%)
**Specs Passing:** 8/8 (100% of implemented)

**Missing Specs (10 total):**

Base (4):
- no-co-authored-by.yaml
- short-status.yaml
- bullets-over-paragraphs.yaml
- read-not-bash-cat.yaml

Agents (4):
- review-writes-output.yaml
- coach-writes-output.yaml
- learn-writes-output.yaml
- on-call-triages-error.yaml

Skills (2):
- owasp-security.yaml
- differential-review.yaml

## Pass Criteria

All subtasks pass when:
- 18/18 specs exist and pass
- `enforcer run` shows 100% pass rate
- Each spec meets its pass_threshold
- No regressions in `enforcer trends --gate`
