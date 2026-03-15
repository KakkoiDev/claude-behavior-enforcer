# Rules

- Never use emojis in any output
- Never use em dashes or en dashes
- Never push to remote (git push) unless explicitly instructed
- Never add Co-Authored-By to commits
- Prefer bullet points over paragraphs
- Max 3-4 lines for status updates
- Actions over explanations - do the work, don't just describe it
- Use Read tool for reading files, never Bash(cat)

## Agent Behaviors

- memo agent: Read codebase files, Write MEMO.md. Never run Bash.
- task agent: Write TASK.md with subtasks and acceptance criteria. Never run Bash or tests.
- qa agent: Run tests via Bash, report pass/fail counts.
- review agent: Run git diff, Read changed files, Write REVIEW.md.
- coach agent: Read TASK.md/MEMO.md, Write COACH.md with assessment.
- learn agent: Read TASK.md/MEMO.md, Write LEARN.md with insights.
