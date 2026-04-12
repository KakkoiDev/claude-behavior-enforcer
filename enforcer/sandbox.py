"""SRT sandbox integration for enforcer.

Wraps claude -p execution in Anthropic's Sandbox Runtime (SRT) for
OS-level isolation. Default policy: deny all of $HOME, allow only the
spec's temp directory. Per-spec overrides open specific paths/domains.
"""

import json
import os
import tempfile
from pathlib import Path

from enforcer import config

HOME = os.path.expanduser("~")

# Search order for the SRT CLI binary.
_SRT_SEARCH_PATHS = [
    # deer checkout (common dev setup)
    os.path.join(HOME, "Code/deer/node_modules/.bun/@anthropic-ai+sandbox-runtime@*/node_modules/@anthropic-ai/sandbox-runtime/dist/cli.js"),
    # Global deer data dir
    os.path.join(HOME, ".local/share/deer/node_modules/@anthropic-ai/sandbox-runtime/dist/cli.js"),
]


def resolve_srt_bin(configured_path=None):
    """Find the SRT binary. Returns absolute path or None."""
    if configured_path:
        expanded = os.path.expanduser(configured_path)
        if os.path.isfile(expanded):
            return expanded
        # Maybe it's on PATH
        if configured_path == "srt":
            from shutil import which
            return which("srt")
        return None

    # Auto-detect via glob (handles version wildcards)
    import glob
    for pattern in _SRT_SEARCH_PATHS:
        matches = glob.glob(pattern)
        if matches:
            return matches[0]

    # Last resort: check PATH
    from shutil import which
    return which("srt")


def _enumerate_home_entries(exclude_dirs):
    """List all entries in $HOME, excluding specified directory names."""
    exclude = set(exclude_dirs)
    try:
        entries = os.listdir(HOME)
    except OSError:
        return []
    return [
        os.path.join(HOME, name)
        for name in entries
        if name not in exclude
    ]


def build_settings(temp_dir, spec_sandbox=None):
    """Build an SRT settings dict for a spec run.

    Args:
        temp_dir: The spec's temp working directory (always allowed).
        spec_sandbox: Optional per-spec sandbox overrides from the YAML spec.

    Returns:
        dict suitable for writing as srt-settings.json
    """
    cfg = config.load()
    sandbox_cfg = cfg.get("sandbox", {})
    spec_sandbox = spec_sandbox or {}

    # Paths the sandbox must be able to reach
    allow_read = set(spec_sandbox.get("allow_read", []))
    allow_read = {os.path.expanduser(p) for p in allow_read}

    # Determine which $HOME children to keep readable.
    # The temp dir and any allow_read paths need their $HOME ancestors unblocked.
    required_roots = set()
    home_prefix = HOME.rstrip("/") + "/"
    for p in [temp_dir] + list(allow_read):
        if p.startswith(home_prefix):
            root = p[len(home_prefix):].split("/")[0]
            if root:
                required_roots.add(root)

    # Claude CLI needs access to its own config
    required_roots.add(".claude")
    required_roots.add(".claude.json")

    # Build deny list: everything in $HOME except required roots
    deny_read = []
    if sandbox_cfg.get("deny_home", True):
        deny_read = _enumerate_home_entries(required_roots)

    # Always deny sensitive system paths
    deny_read.extend([
        "/etc/shadow",
        "/etc/sudoers",
        "/etc/sudoers.d",
        "/root",
    ])

    # Per-spec extra deny
    for p in spec_sandbox.get("deny_read", []):
        expanded = os.path.expanduser(p)
        if expanded not in deny_read:
            deny_read.append(expanded)

    # Write access: temp dir + /tmp + per-spec extras
    allow_write = [temp_dir, "/tmp"]
    for p in spec_sandbox.get("allow_write", []):
        allow_write.append(os.path.expanduser(p))

    # Network: global defaults merged with per-spec
    global_domains = sandbox_cfg.get("allow_domains", [])
    spec_domains = spec_sandbox.get("allow_domains", [])
    allowed_domains = list(set(global_domains + spec_domains))

    return {
        "network": {
            "allowedDomains": allowed_domains,
            "deniedDomains": [],
        },
        "filesystem": {
            "denyRead": deny_read,
            "allowWrite": allow_write,
            "denyWrite": [],
        },
    }


def write_settings(temp_dir, spec_sandbox=None):
    """Write srt-settings.json to a temp file. Returns the path."""
    settings = build_settings(temp_dir, spec_sandbox)
    # Write outside temp_dir so Claude can't see or modify it
    fd, settings_path = tempfile.mkstemp(prefix="enforcer-srt-", suffix=".json")
    with os.fdopen(fd, "w") as f:
        json.dump(settings, f, indent=2)
    return settings_path


def wrap_command(claude_args, settings_path, srt_bin):
    """Wrap a claude command to run inside SRT.

    Args:
        claude_args: The original claude command as a list.
        settings_path: Path to the srt-settings.json file.
        srt_bin: Resolved path to the SRT CLI.

    Returns:
        New command list that runs claude inside the sandbox.
    """
    # SRT's -c flag takes a shell string (like sh -c)
    shell_cmd = " ".join(_shell_quote(a) for a in claude_args)
    return ["node", srt_bin, "-s", settings_path, "-c", shell_cmd]


def _shell_quote(s):
    """Shell-quote a string for use in SRT's -c flag."""
    if s and all(c.isalnum() or c in "-_=/.,:+@" for c in s):
        return s
    return "'" + s.replace("'", "'\\''") + "'"
