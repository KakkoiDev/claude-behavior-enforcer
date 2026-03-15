# Hook System Analysis

## Overview

claude-behavior-enforcer uses a PreToolUse hook to implement holdout isolation, preventing Claude from reading test specs during execution. This ensures genuine behavioral compliance rather than test-optimization.

## Hook Architecture

### 1. Hook Registration (installer.py:28-66)

**Mechanism**: Additive merge into ~/.claude/settings.json

```python
hooks.setdefault("PreToolUse", []).append({
    "matcher": "Read|Glob|Grep|Bash",
    "hooks": [{
        "type": "command",
        "command": "~/.claude-behavior-enforcer/hooks/block-enforcer-access.sh"
    }]
})
```

**Key behaviors**:
- Idempotent: checks for existing installation before adding
- Non-destructive: preserves existing hooks via setdefault()
- Applied to 4 tool types: Read, Glob, Grep, Bash

**Installation flow** (installer.py:154-185):
1. Check dependencies (python3, jq, claude, PyYAML)
2. Add hook to settings.json
3. Symlink bin/enforcer -> ~/.local/bin/enforcer
4. Symlink skill/ -> ~/.claude/skills/claude-behavior-enforcer
5. Verify installation state

### 2. Hook Execution (block-enforcer-access.sh)

**Input**: JSON via stdin from Claude Code tool invocation

**Exit codes**:
- 0: Allow tool execution
- 2: Block tool execution

**Logic flow**:

```
INPUT=$(cat)  # Read JSON from stdin
TOOL=$(echo "$INPUT" | jq -r '.tool_name // empty')

# Exception: Allow if PWD is within enforcer directory (test runs)
if echo "$PWD" | grep -q '\.claude-behavior-enforcer'; then
  exit 0
fi

# Block pattern
HOLDOUT_PATTERN='\.claude-behavior-enforcer'

case "$TOOL" in
  Read)   check_path(tool_input.file_path)
  Glob)   check_path(tool_input.pattern + tool_input.path)
  Grep)   check_path(tool_input.path)
  Bash)   check_bash_cmd(tool_input.command)
esac
```

**Critical exception** (block-enforcer-access.sh:9-12):
- Test runs execute from within ~/.claude-behavior-enforcer/
- Hook allows ALL access when PWD matches holdout pattern
- Enables the enforcer to read its own specs during grading

**Bash command detection** (block-enforcer-access.sh:24-29):
- Regex: `(cd|cat|ls|find|head|tail|less|more|source|\.) \s+\S*\.claude-behavior-enforcer`
- Catches indirect access via cd, cat, find, source, etc.

### 3. Skill Discovery Bypass

**Problem**: Skill needs to be visible to Claude Code via ~/.claude/skills/

**Solution**: Symlink separation
- Skill source: ~/.claude-behavior-enforcer/skill/
- Skill discovery: ~/.claude/skills/claude-behavior-enforcer (symlink)
- Hook blocks access to .claude-behavior-enforcer but NOT .claude/skills/
- Claude can read SKILL.md via symlink without triggering hook

## Test Execution Pipeline

### Spec Discovery (runner.py:22-55)

**Flow**:
1. Walk requirements/**/*.yaml
2. Load each spec with yaml.safe_load()
3. Filter by config.disabled list
4. Filter by category/fixture/tag CLI args
5. Return list of spec dicts

**Directory structure**:
```
requirements/
  base/           # CLAUDE.md compliance (no-emojis, no-push, etc.)
  agents/         # Agent contracts (memo, task, qa, etc.)
  skills/         # Skill trigger/output checks
  fixtures/       # Fixture-based fix evaluation
```

### Spec Execution (runner.py:68-145)

**Isolation**:
1. Create temp dir: `/tmp/enforcer-XXXXX/`
2. Copy fixture if specified: `shutil.copytree(fixture_path, temp_dir)`
3. Snapshot files for disk_diff_clean: `snapshot_files(temp_dir)`
4. Run setup command (if specified)

**Claude invocation**:
```bash
claude -p "$PROMPT" \
  --output-format json \
  --verbose \
  --max-turns 20 \
  -d /tmp/enforcer-XXXXX/ \
  --dangerously-skip-permissions
```

**Key flags**:
- `-d`: Working directory (isolates Claude to temp dir)
- `--output-format json`: Enables parse_result() parsing
- `--verbose`: Captures tool_use events for assertion grading
- `--dangerously-skip-permissions`: Avoids interactive prompts

**Grading**:
1. Parse JSON output: `parse_result(result_file)`
2. Grade assertions: `grade(spec, result, context)`
3. Teardown command (if specified)
4. Delete temp dir

### Result Parsing (grader/assert_engine.py:13-73)

**Extracted data**:
- text: All assistant text blocks
- tools_used: Tool names (including Agent:subagent_type)
- tool_inputs: Full input objects for each tool
- tool_results: Tool result events
- files_written: Paths from Write/Edit tools
- bash_commands: Commands from Bash tool
- cost_usd: Total API cost
- duration_ms: Execution time
- is_error: Error flag
- num_turns: Turn count

**Event types**:
- `result`: cost_usd, duration_ms, is_error, num_turns
- `assistant`: text blocks, tool_use blocks
- `tool_result`: tool execution results

### Assertion Engine (grader/assert_engine.py:85-95)

**26 assertion types**:

| Category | Types | Purpose |
|----------|-------|---------|
| Output | output_contains, output_absent, output_regex, no_emojis, no_em_dash | Text validation |
| Tool | tool_used, tool_not_used | Tool invocation checks |
| File | file_exists, file_content, file_contains | Write/Edit verification |
| Command | command_executed, command_blocked | Bash command checks |
| Agent | agent_invoked | Subagent spawning |
| Metric | response_length, duration_under, cost_under, max_cost_usd, completed | Quantitative bounds |
| LLM | llm_judge | Qualitative LLM-as-judge |
| Disk | disk_file_contains, disk_file_absent, disk_command_succeeds, disk_diff_clean | Fixture state validation |

**Grading logic**:
```python
passed_count = sum(1 for r in results if r["passed"])
pass_rate = passed_count / len(results)
meets_threshold = pass_rate >= spec.get("pass_threshold", 1.0)
```

## Holdout Integrity

**Why it works**:

1. **Hook blocks READ access**:
   - Direct: Read tool with file_path matching pattern
   - Search: Glob/Grep with path matching pattern
   - Indirect: Bash commands with cd/cat/find/ls/etc.

2. **Skill remains accessible**:
   - Symlink at different path (~/.claude/skills/)
   - Hook pattern only matches .claude-behavior-enforcer
   - SKILL.md visible but specs/assertions/fixtures hidden

3. **Test runs exempt**:
   - PWD check allows enforcer to grade itself
   - Enables runner.py to read specs and results
   - Prevents Claude from accessing during `-p` execution

4. **Temp dir isolation**:
   - Each test runs in /tmp/enforcer-XXXXX/
   - Claude's `-d` flag restricts working directory
   - Fixture modifications don't affect source

## Installation Portability

**Three-step install** (enforcer install):

1. **Hook registration**: settings.json merge (installer.py:28-66)
2. **CLI symlink**: bin/enforcer -> ~/.local/bin/ (installer.py:69-87)
3. **Skill symlink**: skill/ -> ~/.claude/skills/ (installer.py:90-106)

**Verification** (enforcer install --verify):
- Dependencies: python3, jq, claude, PyYAML
- Hook presence in settings.json
- Hook script existence
- CLI on PATH
- Skill in ~/.claude/skills/

## Model Escalation

**Flow** (runner.py:201-225):
```python
for model in ["haiku", "sonnet", "opus"]:
    report = run_spec(spec, model=model)
    total_cost += report["cost_usd"]
    if report["meets_threshold"]:
        return report  # Stop at first passing model
```

**Use case**: Find minimum model capability per requirement

**Cost tracking**: Cumulative across all attempts

## Config Management

**config.yaml** (config.py:10-28):
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

**Commands**:
- `enforcer disable <spec>`: Add to disabled list
- `enforcer enable <spec>`: Remove from disabled list

**Filter application** (runner.py:34):
```python
if config.is_disabled(spec_name, cfg):
    continue
```

## Results Persistence

**Directory structure**:
```
results/
  20260315-180325/
    no-emojis.json
    no-push.json
    memo-writes-output.json
    summary.json
```

**Timestamped runs** (runner.py:228-239):
- One JSON per spec: assertion results, pass_rate, cost, duration
- summary.json: total/passed/failed counts, aggregate cost, timestamp

**Trend tracking** (reporter.py):
- Read all results/*/summary.json files
- Calculate pass rate over time
- Gate mode: exit 1 on >5pp regression

## Key Design Patterns

1. **Additive hook installation**: Preserves existing hooks
2. **PWD-based exception**: Allows self-testing
3. **Symlink separation**: Skill visible, specs hidden
4. **Temp dir isolation**: Stateless test execution
5. **JSON output parsing**: Deterministic grading
6. **Pass threshold**: Partial credit support (0.0-1.0)
7. **Model escalation**: Cost/capability optimization
8. **Timestamped results**: Historical compliance tracking

## Security Considerations

**Hook evasion vectors** (all blocked):
- Direct Read: Blocked by check_path()
- Glob search: Blocked by pattern check
- Grep search: Blocked by path check
- Bash cd+cat: Blocked by check_bash_cmd() regex
- Bash find: Blocked by command regex
- Bash source: Blocked by command regex

**Residual risk**: None identified. All tool-based access paths blocked.

## Fixture System

**Purpose**: Test Claude's ability to fix real bugs

**Flow**:
1. Copy fixture from fixtures/ to /tmp/enforcer-XXXXX/
2. Run Claude with fix prompt
3. Verify fix with disk-state assertions (disk_file_contains, disk_command_succeeds)
4. Check for clean diff (only expected files changed)

**Example fixture spec**:
```yaml
name: fix-broken-import
fixture: simple/broken-import
prompt: "The app crashes on startup. Fix the bug."
assertions:
  - type: disk_file_contains
    file: "app.py"
    value: "from collections"
  - type: disk_command_succeeds
    value: "python3 app.py"
```

**Fixture categories**:
- fixtures/simple/: 1-2 file broken projects
- fixtures/complex/: Monorepo, fullstack, multi-component

## CLI Interface

**7 commands** (cli.py:110-161):

| Command | Purpose | Example |
|---------|---------|---------|
| run | Execute specs | enforcer run --category agents |
| add | Scaffold spec | enforcer add "no var in JS" |
| enable | Reactivate spec | enforcer enable no-emojis |
| disable | Deactivate spec | enforcer disable no-emojis |
| install | Setup hooks | enforcer install --verify |
| report | Show latest | enforcer report |
| trends | Historical | enforcer trends --gate |

**Filter options**:
- --category: base, agents, skills, fixtures
- --fixture: Specific fixture name
- --fixtures-only: Only fixture specs
- --tag: Tag-based filter
- --model: Force model (haiku/sonnet/opus)
- --escalate: Auto-escalate on failure
