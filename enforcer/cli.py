"""CLI interface for claude-behavior-enforcer."""

import argparse
import os
import sys

# Ensure enforcer package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enforcer import __version__, config
from enforcer.runner import run_all
from enforcer.installer import install, verify
from enforcer.reporter import report, trends


def cmd_run(args):
    """Run all matching specs."""
    fixture = args.fixture if args.fixture else (True if args.fixtures_only else None)
    results, summary = run_all(
        category=args.category,
        fixture=fixture,
        tag=args.tag,
        model=args.model,
        escalate=args.escalate,
    )

    total = summary.get("total", 0)
    passed = summary.get("passed", 0)
    failed = summary.get("failed", 0)
    cost = summary.get("cost_usd", 0)

    print(f"\n=== Results ===")
    print(f"Total: {total}  Passed: {passed}  Failed: {failed}  Cost: ${cost:.4f}")

    if failed > 0:
        sys.exit(1)


def cmd_add(args):
    """Create a new requirement spec."""
    import yaml as _yaml

    name = args.name.lower().replace(" ", "-")
    cat = args.category or "base"
    cat_dir = os.path.expanduser(f"~/.claude-behavior-enforcer/requirements/{cat}")
    os.makedirs(cat_dir, exist_ok=True)

    spec = {
        "name": name,
        "description": args.name,
        "category": cat,
        "prompt": f'"{args.name}" - verify this requirement is met',
        "config": {"max_turns": 20, "timeout": 600},
        "assertions": [
            {"type": "completed"},
            {"type": "no_emojis"},
            {"type": "no_em_dash"},
        ],
        "pass_threshold": 1.0,
    }

    filepath = os.path.join(cat_dir, f"{name}.yaml")
    with open(filepath, "w") as f:
        _yaml.dump(spec, f, default_flow_style=False, sort_keys=False)

    print(f"Created: {filepath}")
    print("Edit the spec to customize prompt and assertions.")


def cmd_enable(args):
    """Enable a spec."""
    config.enable_spec(args.spec)
    print(f"Enabled: {args.spec}")


def cmd_disable(args):
    """Disable a spec."""
    config.disable_spec(args.spec)
    print(f"Disabled: {args.spec}")


def cmd_install(args):
    """Install enforcer hooks and symlink."""
    if args.verify:
        issues = verify()
        if issues:
            print("Verification issues:")
            for issue in issues:
                print(f"  - {issue}")
            sys.exit(1)
        else:
            print("Installation verified: OK")
        return

    success = install(prefix=args.prefix)
    if not success:
        sys.exit(1)


def cmd_report(args):
    """Show latest run results."""
    report()


def cmd_trends(args):
    """Show compliance trends."""
    trends(gate=args.gate, fmt=args.format)


def main():
    parser = argparse.ArgumentParser(
        prog="enforcer",
        description="Test and enforce Claude Code behavioral requirements.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # run
    p_run = subparsers.add_parser("run", help="Run requirement specs")
    p_run.add_argument("--category", "-c", help="Filter by category (base, agents, skills, fixtures)")
    p_run.add_argument("--fixture", "-f", help="Run specific fixture by name")
    p_run.add_argument("--fixtures-only", action="store_true", help="Run only fixture specs")
    p_run.add_argument("--tag", "-t", help="Filter by tag")
    p_run.add_argument("--model", "-m", help="Model to use (haiku, sonnet, opus)")
    p_run.add_argument("--escalate", action="store_true", help="Auto-escalate: haiku -> sonnet -> opus")
    p_run.set_defaults(func=cmd_run)

    # add
    p_add = subparsers.add_parser("add", help="Create a new requirement spec")
    p_add.add_argument("name", help="Requirement description")
    p_add.add_argument("--category", "-c", default="base", help="Category (default: base)")
    p_add.set_defaults(func=cmd_add)

    # enable
    p_enable = subparsers.add_parser("enable", help="Enable a disabled spec")
    p_enable.add_argument("spec", help="Spec name to enable")
    p_enable.set_defaults(func=cmd_enable)

    # disable
    p_disable = subparsers.add_parser("disable", help="Disable a spec")
    p_disable.add_argument("spec", help="Spec name to disable")
    p_disable.set_defaults(func=cmd_disable)

    # install
    p_install = subparsers.add_parser("install", help="Install hooks and CLI symlink")
    p_install.add_argument("--prefix", help=f"PATH directory for symlink (default: {os.path.expanduser('~/.local/bin')})")
    p_install.add_argument("--verify", action="store_true", help="Verify installation state")
    p_install.set_defaults(func=cmd_install)

    # report
    p_report = subparsers.add_parser("report", help="Show latest run results")
    p_report.set_defaults(func=cmd_report)

    # trends
    p_trends = subparsers.add_parser("trends", help="Show compliance trends over time")
    p_trends.add_argument("--gate", action="store_true", help="Exit non-zero on regression > 5pp")
    p_trends.add_argument("--format", choices=["text", "json"], default="text")
    p_trends.set_defaults(func=cmd_trends)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
