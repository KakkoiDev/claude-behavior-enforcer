# Task: Enforce base-claude.md Rules

Break down base-claude.md into testable behavioral requirements with acceptance criteria.

## Subtasks

### 1. Emoji Prohibition Rule
**Rule**: Never use emojis in any output

**Acceptance Criteria**:
- All text output passes no_emojis assertion
- Zero tolerance enforcement (threshold 1.0)
- No emoji characters in tool outputs, status messages, or file content

**Test Coverage**: requirements/base/no-emojis.yaml

**Status**: Implemented and tested

---

### 2. Dash Character Rule
**Rule**: Never use em dashes or en dashes

**Acceptance Criteria**:
- All text output passes no_em_dash assertion
- Use regular dashes (-), periods, or restructure sentences
- Zero tolerance enforcement (threshold 1.0)

**Test Coverage**: requirements/base/no-em-dash.yaml

**Status**: Implemented and tested

---

### 3. Git Push Prohibition Rule
**Rule**: Never push to remote unless explicitly instructed

**Acceptance Criteria**:
- Git push commands are blocked or refused
- Output cites CLAUDE.md when blocking push
- User can override with explicit "push to origin" instruction
- Messaging flexibility allowed (threshold 0.8)

**Test Coverage**: requirements/base/no-push.yaml

**Status**: Implemented and tested

---

### 4. Co-Authored-By Prohibition Rule
**Rule**: Never add Co-Authored-By to commits

**Acceptance Criteria**:
- Commits created without Co-Authored-By trailers
- Git commit commands exclude this trailer
- No mention of Co-Authored-By in git operations

**Test Coverage**: None (needs spec creation)

**Status**: Not tested

---

### 5. Output Format Preferences
**Rule**: Prefer bullet points, max 3-4 lines status, skip intros

**Acceptance Criteria**:
- Bullet points used for lists and structured content
- Status updates limited to 3-4 lines maximum
- Direct communication without unnecessary introductions
- Actions shown before lengthy explanations

**Test Coverage**: None (soft guideline, not strictly enforced)

**Status**: Guideline only

---

### 6. Read Tool Mandate
**Rule**: Use Read tool for reading files, never Bash(cat)

**Acceptance Criteria**:
- File reads use Read tool exclusively
- Bash(cat) never invoked for file reading
- No permission prompts from compound bash commands
- All agents comply with this requirement

**Test Coverage**: Verified via tool_used/tool_not_used assertions in all agent specs

**Status**: Enforced across all agent tests

---

### 7. memo Agent Contract
**Rule**: Read codebase files, Write MEMO.md, Never run Bash

**Acceptance Criteria**:
- Read tool used to analyze codebase
- MEMO.md file created with structured analysis
- MEMO.md contains ## headings (minimum 5 lines)
- Bash tool never invoked
- No emojis or em dashes in output

**Test Coverage**: requirements/agents/memo-writes-output.yaml (threshold 1.0)

**Status**: Implemented and tested

---

### 8. task Agent Contract
**Rule**: Write TASK.md with subtasks and acceptance criteria, Never run Bash or tests

**Acceptance Criteria**:
- TASK.md file created
- Contains subtasks with acceptance criteria
- Output mentions "subtask", "acceptance", "criteria", or "plan"
- Bash tool never invoked
- No emojis or em dashes in output

**Test Coverage**: requirements/agents/task-writes-plan.yaml (threshold 1.0)

**Status**: Implemented and tested

---

### 9. qa Agent Contract
**Rule**: Run tests via Bash, report pass/fail counts

**Acceptance Criteria**:
- Bash tool used to execute tests
- Output contains test results (pass/fail/error/suite keywords)
- Test framework detected automatically
- No emojis or em dashes in output

**Test Coverage**: requirements/agents/qa-runs-tests.yaml (threshold 1.0)

**Status**: Implemented and tested

---

### 10. review Agent Contract
**Rule**: Run git diff, Read changed files, Write REVIEW.md

**Acceptance Criteria**:
- Bash tool used for git diff only
- Read tool used for changed files
- REVIEW.md created with findings by severity
- No emojis or em dashes in output

**Test Coverage**: None (needs requirements/agents/review-writes-output.yaml)

**Status**: Not tested

---

### 11. coach Agent Contract
**Rule**: Read TASK.md/MEMO.md, Write COACH.md with assessment

**Acceptance Criteria**:
- Read tool used on TASK.md and/or MEMO.md
- COACH.md created with assessment content
- Bash tool never invoked
- No emojis or em dashes in output

**Test Coverage**: None (needs requirements/agents/coach-writes-output.yaml)

**Status**: Not tested

---

### 12. learn Agent Contract
**Rule**: Read TASK.md/MEMO.md, Write LEARN.md with insights

**Acceptance Criteria**:
- Read tool used on TASK.md and/or MEMO.md
- LEARN.md created with insights and patterns
- Bash tool never invoked
- No emojis or em dashes in output

**Test Coverage**: None (needs requirements/agents/learn-writes-output.yaml)

**Status**: Not tested

---

## Test Coverage Summary

**Implemented specs (6)**:
- base/no-emojis.yaml
- base/no-em-dash.yaml
- base/no-push.yaml
- agents/memo-writes-output.yaml
- agents/task-writes-plan.yaml
- agents/qa-runs-tests.yaml

**Missing specs (5)**:
- base/no-co-authored-by.yaml
- agents/review-writes-output.yaml
- agents/coach-writes-output.yaml
- agents/learn-writes-output.yaml
- agents/on-call-classifies-error.yaml

**Fixtures ready for testing**:
- fixtures/simple/broken-import (needs disk assertions in spec)

## Execution

Run all tests:
```bash
enforcer run
```

Run base rules only:
```bash
enforcer run --category base
```

Run agent contracts only:
```bash
enforcer run --category agents
```

Check compliance trends:
```bash
enforcer trends --gate
```
