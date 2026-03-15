---
name: claude-behavior-enforcer
description: Test and enforce Claude Code behavioral requirements. Use when the user wants to run behavior tests, add/remove requirements, check compliance trends, manage fixtures, or install/verify the enforcer system. Triggers on "enforcer", "behavior test", "compliance check", "run specs", "requirement".
---

# claude-behavior-enforcer

CLI tool at `~/.claude-behavior-enforcer/` that tests Claude Code behavioral requirements via holdout-isolated specs. Claude cannot read the specs or assertions (blocked by hook), ensuring genuine compliance rather than test-optimization.

## Commands

Run commands via Bash tool:

| Command | Description |
|---------|-------------|
| `enforcer run` | Run all active requirement specs |
| `enforcer run --category base` | Run only base CLAUDE.md compliance specs |
| `enforcer run --category agents` | Run only agent behavioral contract specs |
| `enforcer run --category skills` | Run only skill trigger/output specs |
| `enforcer run --category fixtures` | Run only fixture-based fix evaluation specs |
| `enforcer run --fixture broken-import` | Run a specific fixture by name |
| `enforcer run --model sonnet` | Run with specific model |
| `enforcer run --escalate` | Auto-escalate: haiku -> sonnet -> opus |
| `enforcer add "requirement description"` | Scaffold a new requirement spec YAML |
| `enforcer add "requirement" --category agents` | Scaffold in specific category |
| `enforcer enable <spec-name>` | Re-enable a disabled spec |
| `enforcer disable <spec-name>` | Temporarily disable a spec |
| `enforcer install` | Install hooks and symlink to PATH |
| `enforcer install --verify` | Verify installation state |
| `enforcer report` | Show latest run results |
| `enforcer trends` | Show pass rate over time |
| `enforcer trends --gate` | Exit non-zero on >5pp regression |

## Project Structure

```
~/.claude-behavior-enforcer/
  bin/enforcer              # CLI entrypoint
  enforcer/                 # Python package
    cli.py                  # argparse commands
    runner.py               # Spec discovery + execution + grading
    config.py               # config.yaml management
    installer.py            # Hook registration + PATH symlink
    reporter.py             # Report + trends
    grader/
      assert_engine.py      # 26 assertion types
      disk_assertions.py    # Disk-state assertions for fixtures
  requirements/
    base/*.yaml             # CLAUDE.md compliance
    agents/*.yaml           # Agent behavioral contracts
    skills/*.yaml           # Skill trigger/output
    fixtures/*.yaml         # Fixture-based specs
  fixtures/
    simple/                 # Simple broken projects (1-2 files)
    complex/                # Complex projects (monorepo, fullstack)
  hooks/
    block-enforcer-access.sh  # Holdout isolation hook
  config.yaml               # Active/disabled specs, defaults
  results/                   # Timestamped run results
```

## Spec Format

```yaml
name: spec-name
description: What this spec tests
category: base|agents|skills|fixtures
tags: [tag1, tag2]
fixture: simple/broken-import    # optional: fixture directory to copy
prompt: "The prompt sent to claude -p"
config:
  max_turns: 20
  timeout: 600
assertions:
  - type: completed
  - type: no_emojis
  - type: tool_used
    value: "Read"
  - type: file_contains
    file: "MEMO.md"
    value: "##"
    min_lines: 5
  - type: disk_command_succeeds    # fixture only
    value: "npm test"
pass_threshold: 1.0
```

## Assertion Types (26 total)

### Output assertions
- `output_contains` - text contains value (case-insensitive)
- `output_absent` - text does NOT contain value
- `output_regex` - text matches regex pattern
- `no_emojis` - no decorative emojis in output
- `no_em_dash` - no em dashes or en dashes

### Tool assertions
- `tool_used` - specific tool was used
- `tool_not_used` - specific tool was NOT used

### File assertions (from tool_inputs)
- `file_exists` - file was written via Write tool
- `file_content` - written file contains value
- `file_contains` - written file contains value + optional min_lines

### Command assertions
- `command_executed` - bash command containing value was run
- `command_blocked` - bash command containing value was NOT run

### Agent assertions
- `agent_invoked` - specific agent type was spawned

### Metric assertions
- `response_length` - output line count (op: lte/gte/eq)
- `duration_under` - execution time within limit
- `cost_under` / `max_cost_usd` - API cost within limit
- `completed` - no error in execution

### LLM assertions
- `llm_judge` - LLM-as-judge scores output 0-100 against criteria

### Disk-state assertions (fixtures)
- `disk_file_contains` - actual file on disk contains value
- `disk_file_absent` - file does NOT exist on disk
- `disk_command_succeeds` - shell command exits 0 in temp dir
- `disk_diff_clean` - only expected files changed

## Model Escalation

```bash
enforcer run --escalate
```

Runs each spec starting with haiku. On failure, retries with sonnet, then opus. Reports minimum model needed per spec in an escalation matrix.

## Workflow

1. `enforcer install` - one-time setup
2. Edit requirements YAML or `enforcer add` to scaffold new specs
3. `enforcer run` - verify all requirements pass
4. `enforcer run --escalate` - find minimum model per requirement
5. `enforcer report` - review latest results
6. `enforcer trends --gate` - CI regression detection

## Important Notes

- Specs live in holdout (Claude cannot read them during testing)
- Fixtures are copied to /tmp for each run and discarded after grading
- config.yaml controls which specs are active
- Results are saved with timestamps for trend tracking
- Cost warning triggers at $5 total per run (configurable)
