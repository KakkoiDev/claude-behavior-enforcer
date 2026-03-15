# Claude Behavior Enforcer Analysis

## System Purpose

Automated testing framework for Claude Code behavioral compliance. Validates rules and agent contracts through isolated execution with deterministic and LLM-based grading.

## Architecture

### Test Pipeline
1. Spec discovery (requirements/**/*.yaml)
2. Isolation setup (temp dir + holdout hook)
3. Execution (claude -p with JSON output)
4. Grading (26 assertion types)
5. Result persistence (timestamped results/)

### Holdout Protection
- Hook blocks Read access to ~/.claude-behavior-enforcer/ during execution
- Prevents test optimization from visible specs
- Forces genuine behavioral response to prompts

### Execution Environment
```
/tmp/enforcer-XXXXX/
  CLAUDE.md (copied from base-claude.md)
  [fixture files if specified]
  [test execution workspace]

/tmp/enforcer-result-{pid}-{id}.json (outside temp dir, invisible to Claude)
```

## Spec Format

```yaml
name: spec-identifier
description: Human-readable purpose
category: base | agents | skills | fixtures
tags: [tag1, tag2]
prompt: "Instruction sent to claude -p"
fixture: simple/broken-import  # optional
setup: "bash command"           # optional
teardown: "bash command"        # optional
config:
  max_turns: 20
  timeout: 600
  permission_mode: ""  # empty = dangerously-skip
assertions:
  - type: completed
  - type: file_exists
    value: "MEMO.md"
  - type: tool_used
    value: "Read"
  - type: file_contains
    file: "MEMO.md"
    value: "##"
    min_lines: 5
pass_threshold: 1.0
```

## Assertion Types (26 total)

| Category | Types | Purpose |
|----------|-------|---------|
| Output | output_contains, output_absent, output_regex, no_emojis, no_em_dash | Response text validation |
| Tool | tool_used, tool_not_used | Tool usage patterns |
| File | file_exists, file_content, file_contains | Written files in memory |
| Command | command_executed, command_blocked | Bash history verification |
| Agent | agent_invoked | Agent delegation confirmation |
| Metric | response_length, duration_under, cost_under, max_cost_usd, completed | Performance/completion |
| LLM | llm_judge | Subjective quality evaluation |
| Disk | disk_file_contains, disk_file_absent, disk_command_succeeds, disk_diff_clean | Temp dir state validation |

## Behavioral Rules (from base-claude.md)

### Output Formatting Rules
- No emojis (zero tolerance)
- No em dashes or en dashes
- Bullet points over paragraphs
- Max 3-4 lines for status updates

### Git Operation Rules
- Never git push (unless explicit instruction)
- Never add Co-Authored-By to commits
- Atomic commits only

### Tool Usage Rules
- Use Read for file reading (never Bash cat)
- Actions over explanations

## Agent Contracts

| Agent | MUST Write | MUST Read | MUST NOT Do |
|-------|-----------|-----------|-------------|
| memo | MEMO.md | Codebase files | Run Bash |
| task | TASK.md with subtasks + acceptance criteria | CLAUDE.md, MEMO.md | Run Bash, run tests |
| qa | Test reports + QA-REPORT-JSON | Test framework files | Modify source code |
| review | REVIEW.md | git diff, changed files | Implement fixes |
| coach | COACH.md | TASK.md, MEMO.md, commits | Implement code |
| learn | LEARN.md | TASK.md, MEMO.md | Modify source files |

### QA Report Format Requirement
```html
<!-- QA-REPORT-JSON {"mode":"check|verify|tdd","summary":{"total":N,"passed":N,"failed":N},"failures":[],"risk_areas":[]} -->
```

## CLI Commands

```bash
enforcer run                          # all active specs
enforcer run --category agents        # filter by category
enforcer run --fixture broken-import  # specific fixture
enforcer run --escalate               # model escalation: haiku -> sonnet -> opus
enforcer add "rule description"       # scaffold new spec
enforcer enable/disable spec-name     # toggle specs
enforcer install                      # register hooks + symlink CLI
enforcer report                       # show latest results
enforcer trends --gate                # regression detection (>5pp = exit 1)
```

## Fixture Testing

Fixtures in fixtures/ (simple/, complex/):
- Copied to temp dir before execution
- Used for bug-fix evaluation
- Disk assertions verify fixes

Example spec (requirements/fixtures/broken-import.yaml):
```yaml
fixture: simple/broken-import
prompt: "The app crashes on startup. Fix the bug."
assertions:
  - disk_file_contains: {file: "app.py", value: "from collections"}
  - disk_command_succeeds: {value: "python3 app.py"}
```

## Model Escalation

With --escalate flag:
1. Try haiku (cheapest)
2. If fails, retry sonnet
3. If fails, retry opus
4. Report minimum model needed
5. Aggregate cost across attempts

## Results Tracking

```
results/YYYYMMDD-HHMMSS/
  {spec-name}.json    # per-spec grading report
  summary.json        # total/passed/failed/cost
```

Enables trend analysis and regression detection.

## Configuration (config.yaml)

```yaml
version: 1
defaults:
  max_turns: 20
  timeout: 600
  model: null
  cost_warn_threshold: 5.0
disabled:
  - spec-name-to-skip
categories:
  base: enabled
  agents: enabled
  skills: enabled
  fixtures: enabled
```

## Current Test Coverage

18 specs across 4 categories:

### base (7 specs)
- no-emojis
- no-em-dash
- no-push
- no-co-authored-by
- short-status
- bullets-over-paragraphs
- read-not-bash-cat

### agents (7 specs)
- memo-writes-output
- task-writes-plan
- qa-runs-tests
- review-writes-output
- coach-writes-output
- learn-writes-output
- on-call-triages-error

### skills (3 specs)
- claude-behavior-enforcer-skill
- owasp-security
- differential-review

### fixtures (1 spec)
- broken-import

## Key Design Decisions

1. **Result file isolation**: Written to /tmp outside temp dir, prevents Claude from reading test expectations during execution
2. **base-claude.md copying**: Gives Claude behavioral context without exposing test specs
3. **Holdout hook**: System-enforced isolation at settings.json level
4. **Temp dir cleanup**: Finally block ensures cleanup on timeout/exception
5. **JSON output requirement**: Enables deterministic parsing of tool use, file operations, command history

## Grading Flow

1. Parse claude output JSON (parse_result)
2. Extract:
   - Tool uses (names + args)
   - File writes (path + content)
   - Bash commands (command strings)
   - Response blocks (text output)
   - Completion status
3. For each assertion in spec:
   - Run assertion type handler
   - Collect pass/fail + evidence
4. Calculate pass_rate = passed / total
5. Compare to pass_threshold
6. Return grading report with meets_threshold boolean

## Implementation Structure

```
~/.claude-behavior-enforcer/
  bin/enforcer              # CLI entrypoint
  enforcer/                 # Python package
    cli.py                  # 7 commands
    runner.py               # Spec discovery, execution, grading
    config.py               # config.yaml management
    installer.py            # Hook registration, PATH symlink
    reporter.py             # Report generation, trend tracking
    grader/
      assert_engine.py      # 26 assertion types
  requirements/
    base/*.yaml             # CLAUDE.md compliance tests
    agents/*.yaml           # Agent behavioral contracts
    skills/*.yaml           # Skill trigger/output checks
    fixtures/*.yaml         # Fixture-based fix evaluation
  fixtures/
    simple/                 # 1-2 file broken projects
    complex/                # Monorepo, fullstack scenarios
  hooks/
    block-enforcer-access.sh  # Holdout isolation hook
  config.yaml               # Active/disabled specs, defaults
  results/                  # Timestamped run results
```

## Dependencies

- Python 3.8+
- PyYAML
- jq
- Claude CLI (with --output-format json support)

## base-claude.md vs Full CLAUDE.md

### Preserved in base-claude.md
- Core zero-tolerance rules (emojis, dashes, git push, Co-Authored-By)
- Tool selection rule (Read vs Bash cat)
- 6 primary agents with basic contracts

### Omitted from base-claude.md
- Workflow orchestration patterns
- QA-REPORT-JSON block requirement (present in full CLAUDE.md)
- Quality gates
- User overrides
- aidb/db-helper tool details
- Memory system rules
- Context recovery protocol

### Design Intent
base-claude.md extracts only rules verifiable through automated testing of agent output and tool calls. Complex orchestration logic excluded.

## Test Coverage Gaps

Comparing base-claude.md (20 lines) to current 18 specs:

### Missing from base-claude.md but in specs:
- on-call agent (line not in base-claude.md)
- Skills testing (owasp-security, differential-review)

### Present in base-claude.md but missing specs:
None - all 10 rules and 6 agent behaviors have corresponding specs.

### Discrepancy
base-claude.md omits QA-REPORT-JSON requirement, but full CLAUDE.md requires it. Current qa-runs-tests.yaml spec should verify this.
