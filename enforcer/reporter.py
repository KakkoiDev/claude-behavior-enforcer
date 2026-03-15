"""Report generation and trend tracking."""

import json
import os
import sys
from pathlib import Path

RESULTS_DIR = Path(os.path.expanduser("~/.claude-behavior-enforcer/results"))


def latest_run():
    """Find the most recent results directory."""
    if not RESULTS_DIR.exists():
        return None
    runs = sorted(RESULTS_DIR.iterdir())
    return runs[-1] if runs else None


def load_run(run_dir):
    """Load all results from a run directory."""
    results = []
    summary = None

    summary_path = run_dir / "summary.json"
    if summary_path.exists():
        with open(summary_path) as f:
            summary = json.load(f)

    for json_file in sorted(run_dir.glob("*.json")):
        if json_file.name == "summary.json":
            continue
        with open(json_file) as f:
            results.append(json.load(f))

    return results, summary


def report():
    """Print latest run results."""
    run_dir = latest_run()
    if not run_dir:
        print("No results found. Run 'enforcer run' first.")
        return

    results, summary = load_run(run_dir)

    print(f"=== Enforcer Report: {run_dir.name} ===\n")

    if summary:
        total = summary.get("total", 0)
        passed = summary.get("passed", 0)
        failed = summary.get("failed", 0)
        cost = summary.get("cost_usd", 0)
        print(f"Total: {total}  Passed: {passed}  Failed: {failed}  Cost: ${cost:.4f}\n")

    # Per-spec results
    for r in results:
        name = r.get("spec_name", "unknown")
        status = "PASS" if r.get("meets_threshold") else "FAIL"
        score = f"{r.get('passed', 0)}/{r.get('total', 0)}"
        cost = r.get("cost_usd", 0)
        model = r.get("model") or "default"

        print(f"  {name:40s} {status:5s} {score:6s} ${cost:.4f} ({model})")

        # Show escalation if present
        if r.get("escalation_attempts"):
            min_model = r.get("minimum_model_needed", "none")
            print(f"    Escalation: min model = {min_model}")
            for attempt in r["escalation_attempts"]:
                amodel = attempt["model"]
                apass = "PASS" if attempt["meets_threshold"] else "FAIL"
                print(f"      {amodel}: {apass} ({attempt['pass_rate']:.0%})")

        # Show failures
        if not r.get("meets_threshold"):
            for assertion in r.get("results", []):
                if not assertion.get("passed"):
                    print(f"    FAIL: {assertion['type']}: {assertion['evidence']}")

    print()


def trends(gate=False, fmt="text"):
    """Show pass rate over time."""
    if not RESULTS_DIR.exists():
        print("No results found.")
        return

    runs = []
    for run_dir in sorted(RESULTS_DIR.iterdir()):
        summary_path = run_dir / "summary.json"
        if summary_path.exists():
            with open(summary_path) as f:
                data = json.load(f)
            data["run_id"] = run_dir.name
            runs.append(data)

    if not runs:
        print("No results with summaries found.")
        return

    if fmt == "json":
        print(json.dumps(runs, indent=2))
        return

    print("=== Compliance Trends ===\n")
    print(f"{'Run':<25s} {'Pass':>6s} {'Total':>6s} {'Rate':>8s} {'Cost':>10s}")
    print("-" * 60)

    for run in runs:
        passed = run.get("passed", 0)
        total = run.get("total", 0)
        rate = (passed / total * 100) if total else 0
        cost = run.get("cost_usd", 0)
        print(f"{run['run_id']:<25s} {passed:>6d} {total:>6d} {rate:>7.1f}% ${cost:>9.4f}")

    # Regression gate
    if gate and len(runs) >= 2:
        first_rate = runs[0].get("passed", 0) / max(runs[0].get("total", 1), 1) * 100
        last_rate = runs[-1].get("passed", 0) / max(runs[-1].get("total", 1), 1) * 100
        drop = first_rate - last_rate
        if drop > 5:
            msg = (
                f"\nREGRESSION GATE FAILED: pass rate dropped {drop:.1f}pp "
                f"(baseline: {first_rate:.1f}%, current: {last_rate:.1f}%)"
            )
            print(msg, file=sys.stderr)
            sys.exit(1)
