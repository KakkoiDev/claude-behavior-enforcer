"""Hook installation and system setup."""

import json
import os
import shutil
import stat
import sys

ENFORCER_DIR = os.path.expanduser("~/.claude-behavior-enforcer")
SETTINGS_PATH = os.path.expanduser("~/.claude/settings.json")
DEFAULT_PREFIX = os.path.expanduser("~/.local/bin")


def check_dependencies():
    """Check required tools are available. Returns list of missing deps."""
    missing = []
    for cmd in ["python3", "jq", "claude"]:
        if not shutil.which(cmd):
            missing.append(cmd)
    try:
        import yaml  # noqa: F401
    except ImportError:
        missing.append("PyYAML (pip install pyyaml)")
    return missing


def install_hooks():
    """Add enforcer hooks to ~/.claude/settings.json (additive merge)."""
    if not os.path.exists(SETTINGS_PATH):
        print(f"  settings.json not found at {SETTINGS_PATH}")
        return False

    with open(SETTINGS_PATH) as f:
        settings = json.load(f)

    hooks = settings.setdefault("hooks", {})
    pre_tool = hooks.setdefault("PreToolUse", [])

    # Check if already installed
    enforcer_hook_cmd = "~/.claude-behavior-enforcer/hooks/block-enforcer-access.sh"
    already_installed = any(
        enforcer_hook_cmd in str(entry.get("hooks", [{}]))
        for entry in pre_tool
    )

    if already_installed:
        print("  Hooks already installed (skipped)")
        return True

    # Add hook entry
    pre_tool.append({
        "matcher": "Read|Glob|Grep|Bash",
        "hooks": [{
            "type": "command",
            "command": enforcer_hook_cmd,
        }],
    })

    # Write back
    with open(SETTINGS_PATH, "w") as f:
        json.dump(settings, f, indent=2)
        f.write("\n")

    print(f"  Added holdout hook to {SETTINGS_PATH}")
    return True


def install_symlink(prefix=None):
    """Symlink bin/enforcer to PATH location."""
    prefix = prefix or DEFAULT_PREFIX
    os.makedirs(prefix, exist_ok=True)

    source = os.path.join(ENFORCER_DIR, "bin", "enforcer")
    target = os.path.join(prefix, "enforcer")

    if os.path.exists(target) or os.path.islink(target):
        os.remove(target)

    os.symlink(source, target)

    # Ensure executable
    st = os.stat(source)
    os.chmod(source, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    print(f"  Symlinked {target} -> {source}")
    return True


def verify():
    """Verify installation state. Returns list of issues."""
    issues = []

    # Check deps
    missing = check_dependencies()
    for dep in missing:
        issues.append(f"Missing dependency: {dep}")

    # Check hooks
    if os.path.exists(SETTINGS_PATH):
        with open(SETTINGS_PATH) as f:
            settings = json.load(f)
        hooks = settings.get("hooks", {}).get("PreToolUse", [])
        enforcer_hook_cmd = "~/.claude-behavior-enforcer/hooks/block-enforcer-access.sh"
        found = any(
            enforcer_hook_cmd in str(entry.get("hooks", [{}]))
            for entry in hooks
        )
        if not found:
            issues.append("Holdout hook not found in settings.json")
    else:
        issues.append(f"settings.json not found at {SETTINGS_PATH}")

    # Check hook script exists
    hook_script = os.path.join(ENFORCER_DIR, "hooks", "block-enforcer-access.sh")
    if not os.path.exists(hook_script):
        issues.append(f"Hook script missing: {hook_script}")

    # Check symlink
    for prefix_dir in [DEFAULT_PREFIX, "/usr/local/bin"]:
        target = os.path.join(prefix_dir, "enforcer")
        if os.path.exists(target):
            break
    else:
        issues.append("enforcer not found on PATH")

    return issues


def install(prefix=None):
    """Full installation: deps, hooks, symlink."""
    print("Installing claude-behavior-enforcer...")

    # Check deps
    missing = check_dependencies()
    if missing:
        print(f"  Missing dependencies: {', '.join(missing)}")
        print("  Install them and retry.")
        return False

    print("  Dependencies: OK")

    # Install hooks
    install_hooks()

    # Install symlink
    install_symlink(prefix)

    # Verify
    issues = verify()
    if issues:
        print("\n  Verification issues:")
        for issue in issues:
            print(f"    - {issue}")
        return False

    print("\n  Installation complete.")
    return True
