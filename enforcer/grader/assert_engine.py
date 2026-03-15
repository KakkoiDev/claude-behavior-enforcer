"""Assertion engine for grading Claude -p JSON output against YAML specs.

Migrated from .claude-tests/assert.py with all 22 assertion types preserved.
Extended with disk-state assertions for fixture grading.
"""

import json
import os
import re
import subprocess


def parse_result(filepath):
    """Parse claude -p JSON output (array of events)."""
    try:
        with open(filepath) as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return None

    if not isinstance(data, list):
        if isinstance(data, dict) and "error" in data:
            return None
        return None

    result = {
        "text": [],
        "tools_used": [],
        "tool_inputs": [],
        "tool_results": [],
        "files_written": [],
        "bash_commands": [],
        "cost_usd": 0,
        "duration_ms": 0,
        "is_error": False,
        "num_turns": 0,
    }

    for ev in data:
        if ev.get("type") == "result":
            result["cost_usd"] = ev.get("total_cost_usd", 0)
            result["duration_ms"] = ev.get("duration_ms", 0)
            result["is_error"] = ev.get("is_error", False)
            result["num_turns"] = ev.get("num_turns", 0)

        elif ev.get("type") == "assistant":
            content = ev.get("message", {}).get("content", [])
            for block in content:
                if block.get("type") == "text":
                    result["text"].append(block["text"])
                elif block.get("type") == "tool_use":
                    name = block.get("name", "")
                    inp = block.get("input", {})
                    result["tools_used"].append(name)
                    result["tool_inputs"].append({"name": name, "input": inp})
                    if name in ("Write", "Edit"):
                        path = inp.get("file_path", "")
                        if path:
                            result["files_written"].append(path)
                    if name == "Bash":
                        cmd = inp.get("command", "")
                        if cmd:
                            result["bash_commands"].append(cmd)
                    if name == "Agent":
                        result["tools_used"].append(
                            f"Agent:{inp.get('subagent_type', inp.get('name', ''))}"
                        )

        elif ev.get("type") == "tool_result":
            result["tool_results"].append(ev)

    result["full_text"] = "\n".join(result["text"])
    return result


# Decorative emojis only - exclude text symbols
EMOJI_RE = re.compile(
    "[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF\U00002702-\U000027B0\U000024C2-\U0001F251]+",
    re.UNICODE,
)


def check_assertion(assertion, result, context=None):
    """Check a single assertion against a result.

    Args:
        assertion: dict with 'type' and optional 'value', 'file', etc.
        result: parsed claude -p output from parse_result()
        context: optional dict with 'temp_dir' for disk assertions

    Returns:
        (passed: bool, evidence: str)
    """
    atype = assertion.get("type", "")
    value = assertion.get("value", "")
    text = result["full_text"]
    tools = result["tools_used"]

    # --- Output assertions ---

    if atype == "output_contains":
        found = value.lower() in text.lower()
        return found, f"{'Found' if found else 'Not found'}: '{value}'"

    elif atype == "output_absent":
        absent = value.lower() not in text.lower()
        return absent, f"{'Absent' if absent else 'Found'}: '{value}'"

    elif atype == "output_regex":
        match = bool(re.search(value, text, re.IGNORECASE | re.MULTILINE))
        return match, f"Regex {'matched' if match else 'no match'}: {value}"

    elif atype == "no_emojis":
        clean = not bool(EMOJI_RE.search(text))
        return clean, "No emojis" if clean else "Contains emojis"

    elif atype == "no_em_dash":
        clean = "\u2014" not in text and "\u2013" not in text
        return clean, "No em/en dashes" if clean else "Contains em/en dash"

    # --- Tool assertions ---

    elif atype == "tool_used":
        used = value in tools
        return used, f"Tool '{value}' {'used' if used else 'not used'}"

    elif atype == "tool_not_used":
        not_used = value not in tools
        return not_used, f"Tool '{value}' {'not used' if not_used else 'was used'}"

    # --- File assertions (from tool_inputs) ---

    elif atype == "file_exists":
        written = any(value in f for f in result["files_written"])
        return written, f"File '{value}' {'written' if written else 'not written'}"

    elif atype == "file_content":
        target = assertion.get("file", "")
        for ti in result["tool_inputs"]:
            if ti["name"] == "Write" and target in ti["input"].get("file_path", ""):
                content = ti["input"].get("content", "")
                found = value.lower() in content.lower()
                return found, f"File content {'contains' if found else 'missing'}: '{value}'"
        return False, f"File '{target}' not found in writes"

    elif atype == "file_contains":
        target = assertion.get("file", "")
        min_lines = assertion.get("min_lines", None)
        for ti in result["tool_inputs"]:
            if ti["name"] == "Write" and target in ti["input"].get("file_path", ""):
                content = ti["input"].get("content", "")
                if value and value.lower() not in content.lower():
                    return False, f"File '{target}' missing content: '{value}'"
                if min_lines is not None:
                    actual_lines = len([l for l in content.split("\n") if l.strip()])
                    if actual_lines < min_lines:
                        return False, f"File '{target}' has {actual_lines} lines (min: {min_lines})"
                return True, f"File '{target}' contains '{value}'"
        return False, f"File '{target}' not found in writes"

    # --- Command assertions ---

    elif atype == "command_executed":
        executed = any(value in cmd for cmd in result["bash_commands"])
        return executed, f"Command '{value}' {'executed' if executed else 'not executed'}"

    elif atype == "command_blocked":
        blocked = not any(value in cmd for cmd in result["bash_commands"])
        return blocked, f"Command '{value}' {'blocked' if blocked else 'was executed'}"

    # --- Agent assertions ---

    elif atype == "agent_invoked":
        invoked = f"Agent:{value}" in tools or any(
            ti["name"] == "Agent" and value in str(ti["input"])
            for ti in result["tool_inputs"]
        )
        return invoked, f"Agent '{value}' {'invoked' if invoked else 'not invoked'}"

    # --- Metric assertions ---

    elif atype == "response_length":
        op = assertion.get("op", "lte")
        limit = int(value)
        lines = len([l for l in text.strip().split("\n") if l.strip()])
        if op == "lte":
            ok = lines <= limit
        elif op == "gte":
            ok = lines >= limit
        else:
            ok = lines == limit
        return ok, f"Response {lines} lines (limit: {op} {limit})"

    elif atype == "duration_under":
        limit_ms = int(value)
        actual = result["duration_ms"]
        ok = actual <= limit_ms
        return ok, f"Duration {actual}ms (limit: {limit_ms}ms)"

    elif atype in ("cost_under", "max_cost_usd"):
        limit = float(value)
        actual = result["cost_usd"]
        ok = actual <= limit
        return ok, f"Cost ${actual:.4f} (max: ${limit:.4f})"

    elif atype == "completed":
        ok = not result["is_error"]
        return ok, "Completed" if ok else "Error"

    # --- LLM assertions ---

    elif atype == "llm_judge":
        criteria = assertion.get("criteria", value)
        threshold = int(assertion.get("threshold", 70))
        try:
            grader_input = text
            file_contents = []
            for ti in result["tool_inputs"]:
                if ti["name"] == "Write":
                    fp = ti["input"].get("file_path", "")
                    content = ti["input"].get("content", "")
                    if fp and content:
                        file_contents.append(
                            f"\n--- FILE WRITTEN: {fp} ---\n{content[:3000]}\n--- END FILE ---"
                        )
            if file_contents:
                grader_input = text + "\n" + "\n".join(file_contents)

            prompt = (
                f"Rate the following AI output on a scale of 0-100 based on this criterion:\n"
                f"CRITERION: {criteria}\n\n"
                f"Output to evaluate:\n{grader_input[:4000]}\n\n"
                f"Respond with exactly two lines:\nSCORE: <number>\nREASON: <one sentence>"
            )
            proc = subprocess.run(
                ["claude", "-p", prompt, "--output-format", "json", "--max-turns", "1"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if proc.returncode == 0:
                events = json.loads(proc.stdout)
                response_text = ""
                for ev in events:
                    if ev.get("type") == "assistant":
                        for block in ev.get("message", {}).get("content", []):
                            if block.get("type") == "text":
                                response_text += block["text"]
                score_match = re.search(r"SCORE:\s*(\d+)", response_text, re.IGNORECASE)
                reason_match = re.search(r"REASON:\s*(.+)", response_text, re.IGNORECASE)
                score = int(score_match.group(1)) if score_match else 0
                reason = reason_match.group(1).strip() if reason_match else "no reason"
                ok = score >= threshold
                return ok, f"LLM judge score {score}/100 (threshold: {threshold}): {reason[:100]}"
            return False, f"llm_judge subprocess failed: exit {proc.returncode}"
        except Exception as e:
            return False, f"llm_judge error: {str(e)}"

    # --- Disk-state assertions (fixture grading) ---

    elif atype == "disk_file_contains":
        if not context or not context.get("temp_dir"):
            return False, "disk_file_contains requires temp_dir context"
        target = assertion.get("file", "")
        filepath = os.path.join(context["temp_dir"], target)
        if not os.path.exists(filepath):
            return False, f"File not found on disk: {target}"
        try:
            with open(filepath) as f:
                content = f.read()
            if value and value.lower() not in content.lower():
                return False, f"Disk file '{target}' missing content: '{value}'"
            return True, f"Disk file '{target}' contains '{value}'"
        except Exception as e:
            return False, f"disk_file_contains error: {e}"

    elif atype == "disk_file_absent":
        if not context or not context.get("temp_dir"):
            return False, "disk_file_absent requires temp_dir context"
        target = assertion.get("file", value)
        filepath = os.path.join(context["temp_dir"], target)
        absent = not os.path.exists(filepath)
        return absent, f"File '{target}' {'absent' if absent else 'exists'} on disk"

    elif atype == "disk_command_succeeds":
        if not context or not context.get("temp_dir"):
            return False, "disk_command_succeeds requires temp_dir context"
        cmd = value
        cmd_timeout = int(assertion.get("timeout", 120))
        try:
            proc = subprocess.run(
                cmd,
                shell=True,
                cwd=context["temp_dir"],
                capture_output=True,
                text=True,
                timeout=cmd_timeout,
            )
            ok = proc.returncode == 0
            output = (proc.stdout + proc.stderr)[:200]
            return ok, f"Command '{cmd}' exit {proc.returncode}: {output}"
        except subprocess.TimeoutExpired:
            return False, f"Command '{cmd}' timed out after {cmd_timeout}s"
        except Exception as e:
            return False, f"disk_command_succeeds error: {e}"

    elif atype == "disk_diff_clean":
        if not context or not context.get("temp_dir"):
            return False, "disk_diff_clean requires temp_dir context"
        expected_files = set(assertion.get("expected_files", []))
        snapshot = context.get("file_snapshot", set())
        if not snapshot:
            return False, "No file snapshot available (run snapshot before claude)"
        current = set()
        for root, dirs, files in os.walk(context["temp_dir"]):
            for f in files:
                rel = os.path.relpath(os.path.join(root, f), context["temp_dir"])
                current.add(rel)
        changed = current.symmetric_difference(snapshot)
        unexpected = changed - expected_files
        if unexpected:
            return False, f"Unexpected file changes: {', '.join(sorted(unexpected)[:10])}"
        return True, f"Only expected files changed: {', '.join(sorted(expected_files))}"

    else:
        return False, f"Unknown assertion type: {atype}"


def grade(spec, result, context=None):
    """Grade a result against a spec.

    Args:
        spec: parsed YAML spec dict
        result: parsed claude -p output from parse_result()
        context: optional dict with 'temp_dir' for disk assertions

    Returns:
        Grading report dict
    """
    assertions = spec.get("assertions", [])
    if not assertions:
        return {"pass_rate": 1.0, "results": [], "error": "no assertions"}

    if result is None:
        return {
            "pass_rate": 0.0,
            "results": [
                {"type": a.get("type"), "passed": False, "evidence": "no result"}
                for a in assertions
            ],
        }

    results = []
    for assertion in assertions:
        passed, evidence = check_assertion(assertion, result, context)
        results.append(
            {
                "type": assertion.get("type", ""),
                "value": assertion.get("value", ""),
                "passed": passed,
                "evidence": evidence,
            }
        )

    passed_count = sum(1 for r in results if r["passed"])
    total = len(results)
    pass_rate = passed_count / total if total else 0
    threshold = spec.get("pass_threshold", 1.0)

    return {
        "pass_rate": pass_rate,
        "passed": passed_count,
        "total": total,
        "meets_threshold": pass_rate >= threshold,
        "threshold": threshold,
        "results": results,
        "cost_usd": result["cost_usd"],
        "duration_ms": result["duration_ms"],
    }
