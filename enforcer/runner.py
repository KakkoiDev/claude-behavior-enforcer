"""Spec discovery, execution, and grading pipeline."""

import json
import os
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

import yaml

from enforcer import config
from enforcer.grader.assert_engine import grade, parse_result

ENFORCER_DIR = Path(os.path.expanduser("~/.claude-behavior-enforcer"))
REQUIREMENTS_DIR = ENFORCER_DIR / "requirements"
FIXTURES_DIR = ENFORCER_DIR / "fixtures"
RESULTS_DIR = ENFORCER_DIR / "results"


def discover_specs(category=None, fixture=None, tag=None):
    """Walk requirements/ and return list of (spec_path, spec_dict) tuples."""
    specs = []
    cfg = config.load()

    for yaml_path in sorted(REQUIREMENTS_DIR.rglob("*.yaml")):
        with open(yaml_path) as f:
            spec = yaml.safe_load(f)
        if not spec or not spec.get("prompt"):
            continue

        spec_name = spec.get("name", yaml_path.stem)
        if config.is_disabled(spec_name, cfg):
            continue

        spec_category = yaml_path.parent.name
        if category and spec_category != category:
            continue

        is_fixture = spec.get("fixture") is not None
        if fixture is not None:
            if fixture is True and not is_fixture:
                continue
            if isinstance(fixture, str) and spec.get("fixture") != fixture:
                continue

        if tag and tag not in spec.get("tags", []):
            continue

        spec["_path"] = str(yaml_path)
        spec["_category"] = spec_category
        specs.append(spec)

    return specs


def snapshot_files(directory):
    """Snapshot all file paths in a directory (for disk_diff_clean)."""
    files = set()
    for root, dirs, filenames in os.walk(directory):
        for f in filenames:
            rel = os.path.relpath(os.path.join(root, f), directory)
            files.add(rel)
    return files


def run_spec(spec, model=None):
    """Execute a single spec. Returns grading report dict."""
    cfg = config.load()
    defaults = cfg.get("defaults", {})

    prompt = spec["prompt"]
    max_turns = spec.get("config", {}).get("max_turns", defaults.get("max_turns", 20))
    timeout = spec.get("config", {}).get("timeout", defaults.get("timeout", 600))
    permission_mode = spec.get("config", {}).get("permission_mode", "")
    setup_cmd = spec.get("setup", "")
    teardown_cmd = spec.get("teardown", "")
    fixture_name = spec.get("fixture")

    # Create temp dir
    temp_dir = tempfile.mkdtemp(prefix="enforcer-")
    context = {"temp_dir": temp_dir}

    try:
        # Copy base CLAUDE.md so Claude sees behavioral rules during testing
        base_claude = ENFORCER_DIR / "base-claude.md"
        if base_claude.exists():
            shutil.copy2(str(base_claude), os.path.join(temp_dir, "CLAUDE.md"))

        # Copy fixture if specified
        if fixture_name:
            fixture_path = FIXTURES_DIR / fixture_name
            if fixture_path.exists():
                shutil.copytree(str(fixture_path), temp_dir, dirs_exist_ok=True)

        # Snapshot for disk_diff_clean
        context["file_snapshot"] = snapshot_files(temp_dir)

        # Run setup
        if setup_cmd:
            subprocess.run(
                setup_cmd, shell=True, cwd=temp_dir,
                capture_output=True, timeout=30
            )

        # Build claude command
        claude_args = [
            "claude", "-p", prompt,
            "--output-format", "json",
            "--verbose",
            "--max-turns", str(max_turns),
            "-d", temp_dir,
        ]
        if permission_mode:
            claude_args += ["--permission-mode", permission_mode]
        else:
            claude_args.append("--dangerously-skip-permissions")
        if model:
            claude_args += ["--model", model]

        # Execute - result file outside temp dir so Claude doesn't see it
        result_file = f"/tmp/enforcer-result-{os.getpid()}-{id(spec)}.json"
        err_file = result_file + ".err"
        try:
            with open(result_file, "w") as out, open(err_file, "w") as err:
                proc = subprocess.run(
                    claude_args, stdout=out, stderr=err,
                    timeout=timeout
                )
        except subprocess.TimeoutExpired:
            pass
        except Exception as e:
            with open(err_file, "a") as err:
                err.write(f"\nRunner exception: {e}\n")

        # Parse and grade
        result = parse_result(result_file)
        try:
            os.unlink(result_file)
        except OSError:
            pass

        # Run teardown
        if teardown_cmd:
            subprocess.run(
                teardown_cmd, shell=True, cwd=temp_dir,
                capture_output=True, timeout=30
            )

        report = grade(spec, result, context)
        report["spec_name"] = spec.get("name", "unknown")
        report["category"] = spec.get("_category", "unknown")
        report["model"] = model
        return report

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def run_all(category=None, fixture=None, tag=None, model=None, escalate=False):
    """Run all matching specs. Returns (results_list, summary_dict)."""
    specs = discover_specs(category=category, fixture=fixture, tag=tag)
    if not specs:
        return [], {"total": 0, "passed": 0, "failed": 0, "cost_usd": 0}

    results = []
    total_cost = 0

    for spec in specs:
        spec_name = spec.get("name", "unknown")
        print(f"  {spec_name} ... ", end="", flush=True)

        if escalate:
            report = _run_with_escalation(spec)
        else:
            report = run_spec(spec, model=model)

        status = "PASS" if report.get("meets_threshold") else "FAIL"
        cost = report.get("cost_usd", 0)
        total_cost += cost
        print(f"{status}  {report.get('passed', 0)}/{report.get('total', 0)}  ${cost:.4f}")

        if not report.get("meets_threshold"):
            for r in report.get("results", []):
                if not r["passed"]:
                    print(f"    FAIL: {r['type']}: {r['evidence']}")

        results.append(report)

    passed = sum(1 for r in results if r.get("meets_threshold"))
    failed = len(results) - passed

    summary = {
        "total": len(results),
        "passed": passed,
        "failed": failed,
        "cost_usd": total_cost,
        "timestamp": datetime.now().isoformat(),
    }

    # Cost warning
    cfg = config.load()
    warn_threshold = cfg.get("defaults", {}).get("cost_warn_threshold", 5.0)
    if total_cost > warn_threshold:
        print(f"\n  WARNING: Total cost ${total_cost:.2f} exceeds ${warn_threshold:.2f} threshold")

    # Save results
    _save_results(results, summary)

    return results, summary


def _run_with_escalation(spec):
    """Run spec with model escalation: haiku -> sonnet -> opus."""
    models = ["haiku", "sonnet", "opus"]
    attempts = []
    total_cost = 0

    for model in models:
        report = run_spec(spec, model=model)
        total_cost += report.get("cost_usd", 0)
        attempts.append({
            "model": model,
            "pass_rate": report.get("pass_rate", 0),
            "meets_threshold": report.get("meets_threshold", False),
        })
        if report.get("meets_threshold"):
            report["minimum_model_needed"] = model
            report["escalation_attempts"] = attempts
            report["cost_usd"] = total_cost
            return report

    # All models failed
    report["minimum_model_needed"] = None
    report["escalation_attempts"] = attempts
    report["cost_usd"] = total_cost
    return report


def _save_results(results, summary):
    """Save run results to timestamped directory."""
    run_dir = RESULTS_DIR / datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=True)

    for report in results:
        name = report.get("spec_name", "unknown")
        with open(run_dir / f"{name}.json", "w") as f:
            json.dump(report, f, indent=2)

    with open(run_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)
