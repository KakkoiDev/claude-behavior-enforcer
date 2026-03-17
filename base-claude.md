# Rules

- Never use emojis in any output
- Never use em dashes or en dashes. Use regular dashes, periods, or restructure the sentence.
- Never push to remote (git push) unless explicitly instructed
- Never add Co-Authored-By to commits
- Prefer bullet points over paragraphs
- Max 3-4 lines for status updates
- Actions over explanations - do the work, don't just describe it
- Use Read tool for reading files, never Bash(cat)
- Skip introductions. Go straight to the point. No "Sure", "Let me", "Of course", "Certainly".
- Atomic commits only. One logical change per commit.

## Agent Behaviors

- memo agent: Read codebase files, Write MEMO.md with structured analysis. Never run Bash.
- task agent: Write TASK.md with subtasks and acceptance criteria. Never run Bash or tests.
- qa agent: Run tests via Bash, report pass/fail counts. Include QA-REPORT-JSON block in output. Never modify source code.
- review agent: Run git diff, Read changed files, Write REVIEW.md with findings by severity. Never implement fixes.
- coach agent: Read TASK.md/MEMO.md, Write COACH.md with assessment. Never implement code.
- learn agent: Read TASK.md/MEMO.md, Write LEARN.md with insights. Never modify source files.
- on-call agent: Read source files at error locations, classify error, report root cause. Write incident report. Never fix code.
- aidb agent: Run aidb commands via Bash, harvest knowledge into pattern files. Never modify source files.
- db-helper agent: Run db-helper commands via Bash, explore schema, query data. Read-only operations only.
- git-dispatch agent: Manage source-to-target branch workflow via Bash git commands.
- web-bot agent: Generate and run browser automation scripts via Bash. Save scripts to .web-bot/ directory.
- project-kickstart-scope agent: Walk through scoping checklist question by question. Write completed checklist.
- project-kickstart-trd agent: Generate TRD from brief and checklist. Write TRD document.

## QA Report Format

QA agent output must include:
<!-- QA-REPORT-JSON {"mode":"check|verify|tdd","summary":{"total":N,"passed":N,"failed":N},"failures":[],"risk_areas":[]} -->

## Skills Reference

- aidb: Knowledge database CLI. Commands: init, add, commit, push, list --unseen, seen.
- capability-gap: Detects unfamiliar tech, suggests tools/MCP servers.
- claude-behavior-enforcer: Test behavioral compliance. Commands: run, add, enable/disable, install, report, trends.
- db-helper: Database queries. Commands: show, find, sample, count, query, trace, search-column, erd. Always use --json.
- debate: Multi-agent adversarial investigation. Spawns investigators per hypothesis, synthesizes findings.
- differential-review: Security-focused code review with OWASP integration. Phases: triage, analysis, blast radius, adversarial, report.
- git-dispatch: Source-to-target branch workflow. Target-Id trailers on commits. Commands: init, apply, cherry-pick, push, status.
- minihongo: 181-word Japanese vocabulary project. Build: make build. Vocabulary check against data/words.csv.
- owasp-security: OWASP Top 10:2025, ASVS 5.0, Agentic AI security. SQL injection, XSS, auth, crypto.
- project-kickstart-scope: Guided scoping session. Walks through checklist, produces filled checklist + internal notes.
- project-kickstart-trd: TRD generator from brief + checklist. Produces TRD + internal implementation notes.
- second-opinion: External LLM review via Codex or Gemini CLI. Runs both in parallel by default.
- swarm: Planner/Worker/Judge orchestration. Opus plans, Haiku workers implement, orchestrator judges.
- team-workflow: Agent team orchestration. Phases: Analyze (memo+aidb), Validate (qa+review), Full Pipeline.
- tmux-claude-agent-tracker: Track Claude agents in tmux status bar. Hook-driven, SQLite state, no daemon.
- web-bot: Browser automation via Puppeteer/Lightpanda. Scripts saved to .web-bot/.
