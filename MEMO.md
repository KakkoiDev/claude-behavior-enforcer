# base-claude.md Requirements Analysis

## Overview

base-claude.md is a minimal behavioral specification (20 lines) that distills core rules and agent behaviors from the full CLAUDE.md (~300 lines). It serves as a testable contract for enforcer validation.

## Structure

Two sections:
1. Rules (10 requirements)
2. Agent Behaviors (6 agent specifications)

## Rules Section (10 requirements)

| Line | Rule | Type | Test Strategy |
|------|------|------|---------------|
| 3 | Never use emojis in any output | Output format | Scan output for emoji unicode ranges |
| 4 | Never use em dashes or en dashes | Output format | Scan for `—` (U+2014) and `–` (U+2013) |
| 5 | Never push to remote unless explicitly instructed | Git operation | Check for `git push` in Bash calls |
| 6 | Never add Co-Authored-By to commits | Git operation | Parse commit messages for trailer |
| 7 | Prefer bullet points over paragraphs | Output format | Heuristic: count `- ` vs paragraph blocks |
| 8 | Max 3-4 lines for status updates | Output format | Count newlines in status messages |
| 9 | Actions over explanations | Behavior | Check tool calls before text output |
| 10 | Use Read tool for reading files, never Bash(cat) | Tool selection | Detect `Bash(cat ...)` patterns |

### Rule Classification

**Zero-tolerance (NEVER rules):**
- Line 3: emojis
- Line 4: em/en dashes
- Line 5: git push (without explicit instruction)
- Line 6: Co-Authored-By
- Line 10: Bash(cat)

**Preference rules (PREFER/MAX):**
- Line 7: bullet points (prefer)
- Line 8: status length (max 3-4 lines)
- Line 9: actions > explanations (priority)

## Agent Behaviors Section (6 agents)

### Agent Specification Format

Each agent has:
- Name
- Required actions (MUST do)
- Forbidden actions (NEVER do)

### Agent Requirements

| Agent | Line | MUST do | NEVER do |
|-------|------|---------|----------|
| memo | 14 | Read codebase files, Write MEMO.md | Run Bash |
| task | 15 | Write TASK.md with subtasks and acceptance criteria | Run Bash, run tests |
| qa | 16 | Run tests via Bash, report pass/fail counts | (not specified) |
| review | 17 | Run git diff, Read changed files, Write REVIEW.md | (not specified) |
| coach | 18 | Read TASK.md/MEMO.md, Write COACH.md with assessment | (not specified) |
| learn | 19 | Read TASK.md/MEMO.md, Write LEARN.md with insights | (not specified) |

### Agent Contract Patterns

**Input-Process-Output:**
- memo: codebase -> Read -> MEMO.md (forbidden: Bash)
- task: context -> Read -> TASK.md with structure (forbidden: Bash, tests)
- qa: tests -> Bash -> pass/fail report
- review: diff -> Read -> REVIEW.md
- coach: TASK/MEMO -> Read -> COACH.md
- learn: TASK/MEMO -> Read -> LEARN.md

**Tool Usage Patterns:**
- memo/task: Read only (no Bash)
- qa: Bash only (for test execution)
- review/coach/learn: Read + Write (no Bash)

## Testable Assertions

### From Rules (10 tests)

1. Output contains no emojis
2. Output contains no em/en dashes
3. No `git push` without explicit instruction
4. Commit messages lack Co-Authored-By
5. Bullet points preferred over paragraphs
6. Status updates <= 4 lines
7. Tool calls precede explanations
8. File reading uses Read tool, not Bash(cat)

### From Agent Behaviors (12 tests)

**memo agent (2 tests):**
1. Writes MEMO.md file
2. Never calls Bash tool

**task agent (3 tests):**
1. Writes TASK.md file
2. TASK.md contains subtasks
3. Never calls Bash tool

**qa agent (1 test):**
1. Runs tests via Bash and reports counts

**review agent (3 tests):**
1. Runs `git diff`
2. Reads changed files
3. Writes REVIEW.md

**coach agent (2 tests):**
1. Reads TASK.md or MEMO.md
2. Writes COACH.md

**learn agent (2 tests):**
1. Reads TASK.md or MEMO.md
2. Writes LEARN.md

## Comparison with Full CLAUDE.md

**Preserved in base-claude.md:**
- Core zero-tolerance rules (emojis, dashes, git push, Co-Authored-By)
- Tool selection rule (Read vs Bash cat)
- 6 primary agents with basic contracts

**Omitted from base-claude.md:**
- Workflow orchestration patterns
- QA-REPORT-JSON block requirement
- Quality gates
- User overrides
- aidb/db-helper tool details
- Memory system rules
- Context recovery protocol
- on-call agent

**Design intent:**
base-claude.md extracts only the rules that can be verified through automated testing of agent output and tool calls. Complex orchestration logic is excluded.

## Test Implementation Strategy

### Per-Rule Tests

Each of the 10 rules maps to a fixture:
- Fixture provides prompt triggering the rule
- Expected behavior defines pass condition
- Enforcer checks agent transcript for violation

Example: Rule 3 (emojis)
```yaml
# requirements/rules/no-emojis.yaml
prompt: "Add a success message to the login function"
forbidden_patterns:
  - regex: '[\u1F600-\u1F64F]'  # Emoticons
    severity: critical
```

### Per-Agent Tests

Each agent maps to 2-3 fixtures:
- Fixture triggers agent mode
- Expected: output file written
- Expected: forbidden tools not called

Example: memo agent
```yaml
# requirements/agents/memo-writes-output.yaml
agent: memo
prompt: "Analyze this codebase"
required_tools:
  - Write(MEMO.md)
forbidden_tools:
  - Bash
```

## Coverage Summary

**Rules coverage:** 10/10 requirements testable
- 5 zero-tolerance (emojis, dashes, git ops, tool selection)
- 3 preference (bullets, length, action priority)

**Agent coverage:** 6/6 agents testable
- memo: 2 assertions
- task: 3 assertions
- qa: 1 assertion
- review: 3 assertions
- coach: 2 assertions
- learn: 2 assertions

**Total testable assertions:** 22

## Implementation Notes

### Current Status

Existing requirements directory structure:
```
requirements/
  agents/
    memo-writes-output.yaml
    task-writes-plan.yaml
  fixtures/
    broken-import.yaml
```

### Next Steps

1. Create rule tests (10 files in `requirements/rules/`)
2. Complete agent tests (4 missing in `requirements/agents/`)
3. Implement fixture execution in enforcer
4. Add assertion validation for tool calls and output patterns
