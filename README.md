# claude-behavior-enforcer

Test and enforce Claude Code behavioral requirements with holdout isolation.

## What it does

- Declares behavioral requirements as YAML specs
- Runs `claude -p` against each spec in isolated temp directories
- Grades output against deterministic and LLM-based assertions
- Ensures Claude cannot read test specs (holdout isolation via hooks)
- Tracks compliance over time with regression detection

## Installation

```bash
# Clone to ~/.claude-behavior-enforcer
git clone https://github.com/YOUR_USER/claude-behavior-enforcer.git ~/.claude-behavior-enforcer

# Install: hooks, CLI symlink, skill
~/.claude-behavior-enforcer/bin/enforcer install
```

This does three things:
1. Adds holdout hook to `~/.claude/settings.json` (blocks Claude from reading specs)
2. Symlinks `enforcer` to `~/.local/bin/` (or `--prefix /your/path`)
3. Symlinks skill to `~/.claude/skills/claude-behavior-enforcer`

## Quick Start

```bash
# After install, just use:
enforcer run

# Run all specs
enforcer run

# Run specific category
enforcer run --category agents

# Run with model escalation (haiku -> sonnet -> opus)
enforcer run --escalate

# View results
enforcer report

# Check trends with regression gate
enforcer trends --gate
```

## Requirements

- Python 3.8+
- PyYAML (`pip install pyyaml`)
- jq
- Claude CLI

## Directory Structure

```
~/.claude-behavior-enforcer/
  bin/enforcer              # CLI entrypoint
  enforcer/                 # Python package
    cli.py                  # 7 commands: run, add, enable, disable, install, report, trends
    runner.py               # Spec discovery, execution, grading pipeline
    config.py               # config.yaml management
    installer.py            # Hook registration, PATH symlink
    reporter.py             # Report generation, trend tracking
    grader/
      assert_engine.py      # 26 assertion types (22 migrated + 4 disk-state)
  requirements/
    base/*.yaml             # CLAUDE.md compliance (no-emojis, no-push, etc.)
    agents/*.yaml           # Agent behavioral contracts (memo, task, qa, etc.)
    skills/*.yaml           # Skill trigger/output checks
    fixtures/*.yaml         # Fixture-based fix evaluation specs
  fixtures/
    simple/                 # 1-2 file broken projects
    complex/                # Monorepo, fullstack, PR review scenarios
  hooks/
    block-enforcer-access.sh  # Prevents Claude from reading this directory
  config.yaml               # Active/disabled specs, defaults
  results/                   # Timestamped run results
```

## Commands

### enforcer run

Run all active requirement specs and grade results.

```bash
enforcer run                          # all active specs
enforcer run --category agents        # agent contracts only
enforcer run --fixture broken-import  # specific fixture
enforcer run --model sonnet           # specific model
enforcer run --escalate               # haiku -> sonnet -> opus
enforcer run --tag memo               # filter by tag
```

### enforcer add

Scaffold a new requirement spec.

```bash
enforcer add "never use var in JavaScript"
enforcer add "review agent must find XSS" --category agents
```

Creates a YAML file with sensible defaults. Edit assertions manually.

### enforcer enable / disable

Toggle specs without deleting them.

```bash
enforcer disable no-emojis    # temporarily disable
enforcer enable no-emojis     # re-enable
```

### enforcer install

Register hooks and symlink CLI.

```bash
enforcer install                      # default: ~/.local/bin
enforcer install --prefix /usr/local/bin
enforcer install --verify             # check installation state
```

### enforcer report

Show latest run results with per-spec detail.

```bash
enforcer report
```

### enforcer trends

Show pass rate over time.

```bash
enforcer trends                       # text output
enforcer trends --format json         # JSON output
enforcer trends --gate                # exit 1 on >5pp regression
```

## Spec Format

```yaml
name: spec-name
description: What this tests
category: base
tags: [output, formatting]
prompt: "The prompt sent to claude -p"
config:
  max_turns: 20
  timeout: 600
assertions:
  - type: completed
  - type: no_emojis
  - type: output_regex
    value: "(?i)(expected|pattern)"
pass_threshold: 1.0
```

## Fixture Specs

Test Claude's ability to fix real bugs:

```yaml
name: fix-broken-import
description: Fix typo in Python import
fixture: simple/broken-import
prompt: "The app crashes on startup. Fix the bug."
assertions:
  - type: completed
  - type: disk_file_contains
    file: "app.py"
    value: "from collections"
  - type: disk_command_succeeds
    value: "python3 app.py"
```

Fixtures are copied to `/tmp/enforcer-XXXXX/` before each run and discarded after grading.

## Assertion Types

26 assertion types across 7 categories:

| Category | Types |
|----------|-------|
| Output | output_contains, output_absent, output_regex, no_emojis, no_em_dash |
| Tool | tool_used, tool_not_used |
| File | file_exists, file_content, file_contains |
| Command | command_executed, command_blocked |
| Agent | agent_invoked |
| Metric | response_length, duration_under, cost_under, max_cost_usd, completed |
| LLM | llm_judge |
| Disk | disk_file_contains, disk_file_absent, disk_command_succeeds, disk_diff_clean |

## Model Escalation

```bash
enforcer run --escalate
```

For each spec: try haiku first (cheapest). If it fails, retry with sonnet. If still fails, retry with opus. Reports minimum model needed per spec.

## Holdout Isolation

The `block-enforcer-access.sh` hook prevents Claude from reading any file under `~/.claude-behavior-enforcer/` during test execution. This ensures Claude responds to prompts genuinely rather than optimizing for visible test expectations.

## Configuration

`config.yaml` controls defaults and spec toggling:

```yaml
version: 1
defaults:
  max_turns: 20
  timeout: 600
  model: null
  cost_warn_threshold: 5.0
disabled:
  - spec-name-here
categories:
  base: enabled
  agents: enabled
  skills: enabled
  fixtures: enabled
```
