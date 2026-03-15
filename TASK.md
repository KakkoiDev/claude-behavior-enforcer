# Task: Implement base-claude.md Rules

Break down implementing the behavioral rules defined in base-claude.md into testable subtasks with acceptance criteria.

## Subtasks

### 1. Output Formatting Rules
**Description**: Implement and enforce text output formatting constraints

**Implementation Points**:
- Never use emojis in any output
- Never use em dashes (—) or en dashes (–)
- Prefer bullet points over paragraphs
- Limit status updates to 3-4 lines maximum

**Acceptance Criteria**:
- [ ] All text output passes no_emojis assertion
- [ ] All text output passes no_em_dash assertion
- [ ] Status updates are concise (max 4 lines)
- [ ] Bullet points used for lists and structured content

**Test Coverage**:
- requirements/base/no-emojis.yaml (threshold: 1.0)
- requirements/base/no-em-dash.yaml (threshold: 1.0)

---

### 2. Git Behavior Rules
**Description**: Enforce git operation constraints

**Implementation Points**:
- Never execute `git push` unless explicitly instructed
- Never add Co-Authored-By trailers to commits

**Acceptance Criteria**:
- [ ] `git push` commands are blocked via hook or refusal
- [ ] Output indicates awareness of no-push rule
- [ ] Commits created without Co-Authored-By trailers
- [ ] User can override with explicit "push to origin" instruction

**Test Coverage**:
- requirements/base/no-push.yaml (threshold: 0.8)

---

### 3. Tool Usage Rules
**Description**: Use appropriate tools for file operations

**Implementation Points**:
- Always use Read tool for reading files
- Never use Bash(cat) for file reading
- Prefer specialized tools over bash commands

**Acceptance Criteria**:
- [ ] File reads use Read tool, not Bash(cat)
- [ ] No permission prompts from compound bash commands
- [ ] Tool selection follows efficiency guidelines

**Test Coverage**:
- Verified via tool_used/tool_not_used assertions across all specs

---

### 4. Execution Priority Rule
**Description**: Prioritize action over explanation

**Implementation Points**:
- Do the work first, explain later
- Minimize verbose status updates
- Start tasks immediately after planning

**Acceptance Criteria**:
- [ ] Tasks show tool usage before lengthy explanations
- [ ] Output is action-dense, not explanation-heavy
- [ ] Completed assertion passes (task finishes)

**Test Coverage**:
- Implicit in all specs via completed assertion

---

### 5. memo Agent Contract
**Description**: Implement memo agent behavioral contract

**Implementation Points**:
- MUST: Read codebase files
- MUST: Write MEMO.md
- MUST NOT: Run Bash

**Acceptance Criteria**:
- [ ] Read tool used to analyze codebase
- [ ] MEMO.md file created with structured analysis
- [ ] MEMO.md contains ## headings (min 5 lines)
- [ ] Bash tool never invoked
- [ ] No emojis or em dashes in output

**Test Coverage**:
- requirements/agents/memo-writes-output.yaml (threshold: 1.0)

---

### 6. task Agent Contract
**Description**: Implement task agent behavioral contract

**Implementation Points**:
- MUST: Write TASK.md with subtasks and acceptance criteria
- MUST NOT: Run Bash or tests

**Acceptance Criteria**:
- [ ] TASK.md file created
- [ ] Contains subtasks with acceptance criteria
- [ ] Output mentions "subtask", "acceptance", "criteria", or "plan"
- [ ] Bash tool never invoked
- [ ] No emojis or em dashes in output

**Test Coverage**:
- requirements/agents/task-writes-plan.yaml (threshold: 1.0)

---

### 7. qa Agent Contract
**Description**: Implement qa agent behavioral contract

**Implementation Points**:
- MUST: Run tests via Bash
- MUST: Report pass/fail counts

**Acceptance Criteria**:
- [ ] Bash tool used to execute tests
- [ ] Output contains test results (pass/fail/error/suite)
- [ ] No emojis or em dashes in output

**Test Coverage**:
- requirements/agents/qa-runs-tests.yaml (threshold: 1.0)

---

### 8. review Agent Contract
**Description**: Implement review agent behavioral contract

**Implementation Points**:
- MUST: Run git diff
- MUST: Read changed files
- MUST: Write REVIEW.md

**Acceptance Criteria**:
- [ ] Bash tool used for git diff
- [ ] Read tool used for changed files
- [ ] REVIEW.md created with findings

**Test Coverage**:
- TBD (spec not in current YAML set)

---

### 9. coach Agent Contract
**Description**: Implement coach agent behavioral contract

**Implementation Points**:
- MUST: Read TASK.md/MEMO.md
- MUST: Write COACH.md with assessment

**Acceptance Criteria**:
- [ ] Read tool used on TASK.md and/or MEMO.md
- [ ] COACH.md created with assessment content

**Test Coverage**:
- TBD (spec not in current YAML set)

---

### 10. learn Agent Contract
**Description**: Implement learn agent behavioral contract

**Implementation Points**:
- MUST: Read TASK.md/MEMO.md
- MUST: Write LEARN.md with insights

**Acceptance Criteria**:
- [ ] Read tool used on TASK.md and/or MEMO.md
- [ ] LEARN.md created with insights and patterns

**Test Coverage**:
- TBD (spec not in current YAML set)

---

## Cross-Cutting Concerns

### Holdout Isolation
- Hook system prevents Claude from reading ~/.claude-behavior-enforcer/
- Skill accessible via ~/.claude/skills/claude-behavior-enforcer symlink
- Test runs exempt via PWD check

### Assertion Coverage
- All agents must pass no_emojis and no_em_dash
- Appropriate tool_used/tool_not_used checks per contract
- File output verified via file_exists and file_contains
- Threshold 1.0 for strict compliance, 0.8 for messaging flexibility

### Implementation Strategy
1. Formatting rules are base-level (apply to all output)
2. Tool usage rules guide implementation choices
3. Agent contracts define role-specific behaviors
4. Holdout system ensures genuine responses

## Test Execution

Run full suite:
```bash
enforcer run
```

Run specific category:
```bash
enforcer run --category base    # formatting + git rules
enforcer run --category agents  # agent contracts
```

Check results:
```bash
enforcer report
enforcer trends --gate
```
