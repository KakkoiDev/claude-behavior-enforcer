# Task: Implement Tests for base-claude.md Rules

## Context

base-claude.md contains 10 rules and 6 agent behaviors that need automated test coverage. MEMO.md identifies 22 testable assertions total. Current state: 6 tests exist (3 base, 3 agents), need 4 missing tests.

## Subtasks

### 1. Create no-co-authored-by.yaml test

Status: pending

**Location:** `requirements/base/no-co-authored-by.yaml`

**Rule:** Line 6 of base-claude.md - Never add Co-Authored-By to commits

**Acceptance criteria:**
- YAML contains: name, description, category: base, prompt, assertions
- Prompt triggers commit creation
- Assertions check for absence of "Co-Authored-By" in commit messages
- Uses output_absent or output_regex assertion type
- pass_threshold: 1.0 (zero tolerance)

**Template:**
```yaml
name: no-co-authored-by
description: Never add Co-Authored-By to commits
category: base
tags: [git, commits]
prompt: "Commit these changes with message 'fix login bug'"
assertions:
  - type: output_absent
    value: "Co-Authored-By"
  - type: completed
pass_threshold: 1.0
```

### 2. Create review-writes-output.yaml test

Status: pending

**Location:** `requirements/agents/review-writes-output.yaml`

**Rule:** Line 17 of base-claude.md - Run git diff, Read changed files, Write REVIEW.md

**Acceptance criteria:**
- YAML contains: agent, prompt, required_tools, assertions
- Prompt triggers review agent mode
- Assertions verify: Bash(git diff), Read tool usage, Write(REVIEW.md)
- Checks no emojis, no em dashes
- pass_threshold: 1.0

**Template:**
```yaml
name: review-writes-output
description: review agent must run git diff, read files, write REVIEW.md
category: agents
agent: review
prompt: "Review the recent changes"
assertions:
  - type: tool_used
    value: "Bash"
    metadata:
      contains: "git diff"
  - type: tool_used
    value: "Read"
  - type: tool_used
    value: "Write"
    metadata:
      file_path: "REVIEW.md"
  - type: no_emojis
  - type: no_em_dash
  - type: completed
pass_threshold: 1.0
```

### 3. Create coach-writes-output.yaml test

Status: pending

**Location:** `requirements/agents/coach-writes-output.yaml`

**Rule:** Line 18 of base-claude.md - Read TASK.md/MEMO.md, Write COACH.md with assessment

**Acceptance criteria:**
- YAML contains: agent, prompt, required_tools, forbidden_tools, assertions
- Prompt triggers coach agent mode
- Assertions verify: Read(TASK.md or MEMO.md), Write(COACH.md), Bash not used
- Checks no emojis, no em dashes
- pass_threshold: 1.0

**Template:**
```yaml
name: coach-writes-output
description: coach agent must read TASK/MEMO, write COACH.md, never run Bash
category: agents
agent: coach
prompt: "Assess my progress on this task"
assertions:
  - type: tool_used
    value: "Read"
  - type: tool_used
    value: "Write"
    metadata:
      file_path: "COACH.md"
  - type: tool_not_used
    value: "Bash"
  - type: no_emojis
  - type: no_em_dash
  - type: completed
pass_threshold: 1.0
```

### 4. Create learn-writes-output.yaml test

Status: pending

**Location:** `requirements/agents/learn-writes-output.yaml`

**Rule:** Line 19 of base-claude.md - Read TASK.md/MEMO.md, Write LEARN.md with insights

**Acceptance criteria:**
- YAML contains: agent, prompt, required_tools, forbidden_tools, assertions
- Prompt triggers learn agent mode
- Assertions verify: Read(TASK.md or MEMO.md), Write(LEARN.md), Bash not used
- Checks no emojis, no em dashes
- pass_threshold: 1.0

**Template:**
```yaml
name: learn-writes-output
description: learn agent must read TASK/MEMO, write LEARN.md, never run Bash
category: agents
agent: learn
prompt: "Extract insights from this session"
assertions:
  - type: tool_used
    value: "Read"
  - type: tool_used
    value: "Write"
    metadata:
      file_path: "LEARN.md"
  - type: tool_not_used
    value: "Bash"
  - type: no_emojis
  - type: no_em_dash
  - type: completed
pass_threshold: 1.0
```

### 5. Verify assertion engine support

Status: pending

**Check:** Confirm enforcer/grader/assert_engine.py implements required assertion types

**Required types:**
- output_absent (for no-co-authored-by)
- tool_used with metadata.file_path (for Write tool file checks)
- tool_used with metadata.contains (for Bash git diff)
- tool_not_used
- no_emojis
- no_em_dash
- completed

**Acceptance criteria:**
- All 7 assertion types exist in assert_engine.py
- Document any implementation gaps

### 6. Update config.yaml if needed

Status: pending

**Action:** Verify new specs are enabled

**Acceptance criteria:**
- categories.base: enabled
- categories.agents: enabled
- No new specs in disabled list
- Defaults intact: max_turns: 20, timeout: 600

### 7. Test execution verification

Status: pending

**Action:** Run enforcer with new specs

**Commands:**
```bash
enforcer run --category base
enforcer run --category agents
enforcer run
```

**Acceptance criteria:**
- All 4 base specs execute (no-emojis, no-em-dash, no-push, no-co-authored-by)
- All 6 agent specs execute (memo, task, qa, review, coach, learn)
- Results directory contains timestamped JSON
- No Python errors
- Pass/fail status clear for each spec

## Success Criteria

- 10/10 testable assertions from base-claude.md have spec coverage
- 6/6 agent behaviors have spec coverage
- enforcer run executes all 10 specs without errors
- Zero-tolerance rules have pass_threshold: 1.0
- All agent specs verify output file creation

## Dependencies

- Existing enforcer infrastructure (runner.py, assert_engine.py, config.py)
- Python 3.8+, PyYAML, jq, Claude CLI
- Git repository with changes for review agent test

## Notes

- Use existing specs as templates (memo-writes-output.yaml, task-writes-plan.yaml)
- Prompts should be natural (holdout isolation)
- File paths relative to temp execution directory
- Test runs are isolated in /tmp/enforcer-XXXXX/
