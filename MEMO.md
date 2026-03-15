# CLAUDE.md Behavioral Requirements Analysis

## Document Sources

1. **~/.claude/CLAUDE.md** - Global user configuration (7 sections)
2. **base-claude.md** - Minimal distilled rules (20 lines, 2 sections)
3. **Requirements specs** - YAML test specifications (6 files)

## Core Rule Categories

### 1. Output Formatting Rules

| Rule | Description | Enforcement Level | Test Spec |
|------|-------------|-------------------|-----------|
| No emojis | Zero tolerance, no exceptions | STRICT | no-emojis.yaml |
| No em/en dashes | Use regular dashes or periods | STRICT | no-em-dash.yaml |
| Bullet points | Prefer over paragraphs | PREFERENCE | - |
| Max 3-4 lines status | Concise updates only | GUIDELINE | - |
| Skip introductions | Direct communication | GUIDELINE | - |
| Actions over explanations | Do work, minimize talk | GUIDELINE | - |

### 2. Git Operation Rules

| Rule | Description | Enforcement Level | Test Spec |
|------|-------------|-------------------|-----------|
| Never push | Block git push unless explicit instruction | STRICT | no-push.yaml |
| Atomic commits | One logical change per commit | GUIDELINE | - |
| No Co-Authored-By | Never add this trailer | STRICT | - |
| Commit after task | Create commits when done | GUIDELINE | - |

### 3. Tool Selection Rules

| Rule | Description | Enforcement Level | Test Spec |
|------|-------------|-------------------|-----------|
| Use Read tool | Never Bash(cat) for reading files | STRICT | All agent specs |
| Specialized tools | Prefer dedicated tools over bash | PREFERENCE | - |

## Agent Behavioral Contracts

### Contract Matrix

| Agent | Input | Output | Bash | Must Read | Must Write | Test Spec |
|-------|-------|--------|------|-----------|------------|-----------|
| memo | Codebase files | MEMO.md | NO | Yes | Yes | memo-writes-output.yaml |
| task | CLAUDE.md, MEMO.md | TASK.md | NO | Yes | Yes | task-writes-plan.yaml |
| qa check | Test suite | stdout | YES | No | No | qa-runs-tests.yaml |
| qa verify | Target code | Test file + stdout | YES | No | Yes | - |
| qa tdd | Specs | Test file + stdout | YES | No | Yes | - |
| review | git diff | REVIEW.md | YES (git only) | Yes | Yes | - |
| coach | TASK.md, MEMO.md, commits | COACH.md | NO | Yes | Yes | - |
| learn | TASK.md, MEMO.md | LEARN.md | NO | Yes | Yes | - |
| aidb | Project files | _aidb/*.md | YES (aidb CLI) | Yes | Yes | - |
| on-call | Source at error location | incident_*.md | NO | Yes | Yes | - |

### Agent Invariants

**Universal requirements (all agents)**:
- No emojis in output
- No em/en dashes in output
- Must write designated output file
- Must read relevant source files before output

**Role-specific constraints**:
- Analysis agents (memo, task, coach, learn, on-call): NEVER run Bash
- Testing agents (qa): MUST run Bash, MUST report pass/fail counts
- Review agent: MAY run Bash for git diff only
- Tool agents (aidb): MAY run Bash for specific CLI only

### QA Agent Modes

All QA modes MUST include this JSON block in output:
```
<!-- QA-REPORT-JSON {"mode":"check|verify|tdd","summary":{"total":N,"passed":N,"failed":N},"failures":[],"risk_areas":[]} -->
```

| Mode | Description | File Output | Behavior |
|------|-------------|-------------|----------|
| check | Run existing test suite | No | Detect framework, execute, report counts |
| verify | Write targeted test for claim | Yes (test file) | Write test, run it, report results |
| tdd | Write specs first (red phase) | Yes (test file) | Write failing tests, report TDD status |

## Workflow Routing

### Automatic Chaining

| User Intent Pattern | Agent Chain | Skip Conditions |
|---------------------|-------------|-----------------|
| "build/add/implement feature X" | memo -> task -> implement -> qa -> review | Small feature: skip memo |
| "fix bug/issue X" | implement -> qa | Obvious fix: skip qa |
| "review/check this code" | review (+ owasp-security if security) | - |
| "test/verify X" | qa (auto-detect mode) | - |
| "what does this codebase do" | memo | - |
| "plan/break down X" | task | - |
| "is this secure" | review + owasp-security | - |
| "ship/deploy this" | qa -> review -> commit | - |
| "learn/harvest/reflect" | learn + aidb | - |

### Quality Gates

- After code implementation: auto-run `qa check` if test suite exists
- After qa finds issues: suggest fixes
- After review: offer to address critical findings
- Max chain depth: 3 automatic steps, then ask user

### User Override Patterns

- "skip review" / "skip qa" / "just implement" - bypass gates
- "only review" / "only test" - single agent, no chaining
- Explicit agent prefix (e.g., "qa verify X") - direct routing

## Tool Usage Patterns

### Read Tool Mandate

**Why Read instead of Bash(cat)**:
- Bash(cat) triggers permission prompts (compound commands don't match allow-list)
- Read tool is auto-approved, never prompts
- STRICT enforcement across all agents

### aidb Tool (Knowledge Persistence)

**Commands**:
- `aidb add <file>` - Track file (symlinks to ~/.aidb)
- `aidb commit <msg>` - Commit changes
- `aidb list --unseen` - Files needing attention
- `aidb seen <file>` - Mark processed

**Workflow**:
1. Agent creates output file with Write tool
2. Run `aidb add <output-file>`
3. Run `aidb commit "<message>"`
4. Run `aidb push` (optional)

### db-helper Tool

14 commands for database exploration:
- Schema: show, search-column, diff-prisma, erd, config, update
- Query: find, sample, count, query
- Relationships: trace
- Init: create

All commands support --json flag. Requires init: `cd apps/server && db-helper create --env .env`

## Memory Strategy

**Disabled**: Built-in auto-memory, MEMORY.md files in ~/.claude/projects/

**Active**: MEMO.md + aidb for all persistence
- Insights, decisions, patterns -> MEMO.md (via memo agent)
- Track with aidb add + commit + push
- Cross-project knowledge -> ~/.aidb/

**Context Recovery Protocol** (after compaction or /clear):
1. Read TASK.md (current task state)
2. Read MEMO.md (project analysis and decisions)
3. Read LEARN.md (accumulated patterns)

These files ARE the context.

## Test Specifications

### Existing Specs (6 files)

**Base category** (3 specs):
- no-emojis.yaml - Strict zero-emoji enforcement
- no-em-dash.yaml - Strict dash character enforcement
- no-push.yaml - Block git push, cite CLAUDE.md (threshold 0.8 for messaging)

**Agents category** (3 specs):
- memo-writes-output.yaml - Verify MEMO.md creation, no Bash
- task-writes-plan.yaml - Verify TASK.md creation, content structure
- qa-runs-tests.yaml - Verify Bash usage, test output format

### Assertion Types Used

**Current coverage**:
- completed - Task finishes successfully
- file_exists - Output file created
- file_contains - Output has specific content
- output_regex - Output matches pattern
- tool_used - Specific tool was invoked
- tool_not_used - Specific tool was blocked
- no_emojis - No emoji characters in output
- no_em_dash - No em/en dash characters in output
- output_contains - Output has exact string
- command_blocked - Command was rejected

**Available but unused**:
- disk_file_contains - File in temp dir has content
- disk_file_absent - File was deleted
- disk_command_succeeds - Command in temp dir succeeds
- disk_diff_clean - No uncommitted changes
- llm_judge - LLM evaluates output quality

### Coverage Gaps

**Missing specs for agents**:
- review-writes-output.yaml (review agent contract)
- coach-writes-output.yaml (coach agent contract)
- learn-writes-output.yaml (learn agent contract)
- aidb-tracks-knowledge.yaml (aidb agent contract)
- on-call-classifies-error.yaml (on-call agent contract)

**Missing specs for workflow**:
- workflow-chaining.yaml (automatic agent routing)
- quality-gates.yaml (auto-qa after implementation)

**Missing specs for fixtures**:
- fixtures/broken-import.yaml exists but needs disk assertions

## Behavioral Invariants

### Hard Constraints (threshold 1.0)

1. All agents MUST write designated output file
2. Analysis agents (memo, task, coach, learn, on-call) MUST NOT run Bash
3. QA agent MUST run Bash
4. All output MUST pass no_emojis assertion
5. All output MUST pass no_em_dash assertion
6. Read tool MUST be used for file reading (not Bash(cat))

### Soft Constraints (threshold 0.8)

1. Git push SHOULD be blocked (allow messaging flexibility)
2. Status updates SHOULD be 3-4 lines
3. Bullet points PREFERRED over paragraphs

### Context-Dependent Rules

1. Bash usage: FORBIDDEN for memo/task/coach/learn/on-call, REQUIRED for qa, ALLOWED for review (git diff only), ALLOWED for aidb (aidb CLI only)
2. Agent chaining: AUTOMATIC for feature implementation, OPTIONAL for bug fixes, DISABLED if user says "skip"
3. Quality gates: ENABLED by default, BYPASSED on user override

## Design Principles

1. **Minimal changes** - Smallest diff to achieve goal
2. **Test first** - Verify before implementing
3. **Framework docs lie** - Verify behavior empirically
4. **No over-engineering** - Simplest solution wins

## Holdout Isolation System

**Purpose**: Prevent Claude from reading test specs during execution

**Mechanism**:
- Hook: `~/.claude/hooks/block-enforcer-access.sh`
- Blocks all reads under `~/.claude-behavior-enforcer/`
- Exempts skill access via `~/.claude/skills/claude-behavior-enforcer` symlink
- Exempts test runs by PWD check

**Result**: Claude responds genuinely to prompts, cannot optimize for visible test expectations

## Implementation Status

**Completed**:
- Base rules (no-emojis, no-em-dash, no-push) implemented and tested
- 3 agent contracts (memo, task, qa) implemented and tested
- Holdout hook system installed
- CLI with 7 commands: run, add, enable, disable, install, report, trends
- 26 assertion types in grader engine

**Pending**:
- 5 agent contracts (review, coach, learn, aidb, on-call)
- Workflow chaining automation
- Quality gate enforcement
- Fixture-based testing with disk assertions
- Model escalation (haiku -> sonnet -> opus)
