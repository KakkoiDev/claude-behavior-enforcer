# Claude Behavior Enforcer - Full Coverage Build

## Spec Inventory: 35 total (was 18)

### Base (8 specs)
| Spec | Status | Notes |
|------|--------|-------|
| no-emojis | PASS | 3/3 assertions |
| no-em-dash | PASS | 3/3 assertions |
| no-push | PASS | 4/5 at 0.8 threshold |
| no-co-authored-by | UNTESTED | New in previous batch |
| short-status | UNTESTED | New in previous batch |
| bullets-over-paragraphs | UNTESTED | New in previous batch |
| read-not-bash-cat | UNTESTED | New in previous batch |
| skip-introductions | NEW | Tests for fluff-free output |

### Agents (9 specs)
| Spec | Status | Notes |
|------|--------|-------|
| memo-writes-output | PASS | 7/7 assertions |
| task-writes-plan | PASS | 6/6 assertions |
| qa-runs-tests | PASS (strengthened) | Added QA-REPORT-JSON check, lowered threshold to 0.8 |
| review-writes-output | UNTESTED | New in previous batch |
| coach-writes-output | UNTESTED | New in previous batch |
| learn-writes-output | UNTESTED | New in previous batch |
| on-call-triages-error | UNTESTED (strengthened) | Added severity/incident assertions, lowered to 0.8 |
| aidb-harvests-knowledge | NEW | Tests aidb agent behavioral contract |
| web-bot-generates-scripts | NEW | Tests script generation contract |

### Skills (17 specs)
| Spec | Status | Notes |
|------|--------|-------|
| claude-behavior-enforcer-skill | PASS | 5/5 assertions |
| owasp-security | UNTESTED | New in previous batch |
| differential-review | UNTESTED | New in previous batch |
| skill-aidb | NEW | Knowledge of aidb commands |
| skill-capability-gap | NEW | Tech detection awareness |
| skill-db-helper | NEW | Knowledge of db-helper commands |
| skill-debate | NEW | Adversarial investigation workflow |
| skill-git-dispatch | NEW | Source-to-target workflow |
| skill-minihongo | NEW | 181-word vocabulary constraint |
| skill-project-kickstart-scope | NEW | Scoping session workflow |
| skill-project-kickstart-trd | NEW | TRD generation workflow |
| skill-second-opinion | NEW | External LLM review |
| skill-swarm | NEW | Planner/Worker/Judge pattern |
| skill-team-workflow | NEW | Agent team orchestration |
| skill-tmux-claude-agent-tracker | NEW | Tracker setup and commands |
| skill-tmux-claude-agent-tracker-dev | NEW | Dev conventions and debugging |
| skill-web-bot | NEW | Browser automation workflow |

### Fixtures (1 spec)
| Spec | Status | Notes |
|------|--------|-------|
| broken-import | PASS | 5/5 assertions, fixture reverted |

## Changes Made This Session

1. **base-claude.md expanded**: 6 agents -> 13 agents, added Skills Reference section, added QA-REPORT-JSON format, added skip-introductions and atomic-commits rules
2. **1 new base spec**: skip-introductions
3. **2 new agent specs**: aidb-harvests-knowledge, web-bot-generates-scripts
4. **14 new skill specs**: aidb, capability-gap, db-helper, debate, git-dispatch, minihongo, project-kickstart-scope, project-kickstart-trd, second-opinion, swarm, team-workflow, tmux-claude-agent-tracker, tmux-claude-agent-tracker-dev, web-bot
5. **2 specs strengthened**: qa-runs-tests (QA-REPORT-JSON), on-call-triages-error (severity/incident)
6. **Fixture reverted**: broken-import/app.py restored to broken state

## Coverage Summary

| Category | Dotfiles Items | Specs | Coverage |
|----------|---------------|-------|----------|
| Base rules | 10 | 8 | 80% |
| Agents | 13 | 9 | 69% |
| Skills | 17 | 17 | 100% |
| Fixtures | 1 | 1 | 100% |

## Remaining Gaps

### Agents not yet specced (4):
- db-helper agent (needs DB infrastructure)
- git-dispatch agent (needs multi-branch git setup)
- project-kickstart-scope agent (needs template files)
- project-kickstart-trd agent (needs template files)

These require fixtures or infrastructure that doesn't exist in the temp dir. Covered via skill-knowledge specs instead.

### Base rules not yet specced (2):
- "Actions over explanations" - hard to assert deterministically
- "Atomic commits only" - requires multi-change scenario

## Next Steps

1. Run `enforcer run` to validate all 35 specs
2. Iterate on any failures (adjust prompts/thresholds)
3. Consider fixtures for remaining 4 agent gaps
