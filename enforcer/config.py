"""Config management for enforcer."""

import os
import yaml

ENFORCER_DIR = os.path.expanduser("~/.claude-behavior-enforcer")
CONFIG_PATH = os.path.join(ENFORCER_DIR, "config.yaml")


def load():
    """Load config.yaml. Returns default config if file missing."""
    if not os.path.exists(CONFIG_PATH):
        return {
            "version": 1,
            "defaults": {
                "max_turns": 20,
                "timeout": 600,
                "model": None,
                "cost_warn_threshold": 5.0,
            },
            "disabled": [],
            "categories": {
                "base": "enabled",
                "agents": "enabled",
                "skills": "enabled",
                "fixtures": "enabled",
            },
        }
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def save(cfg):
    """Write config back to disk."""
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(cfg, f, default_flow_style=False, sort_keys=False)


def disable_spec(name):
    """Add spec to disabled list."""
    cfg = load()
    if name not in cfg.get("disabled", []):
        cfg.setdefault("disabled", []).append(name)
        save(cfg)
    return cfg


def enable_spec(name):
    """Remove spec from disabled list."""
    cfg = load()
    disabled = cfg.get("disabled", [])
    if name in disabled:
        disabled.remove(name)
        save(cfg)
    return cfg


def is_disabled(name, cfg=None):
    """Check if a spec is disabled."""
    if cfg is None:
        cfg = load()
    return name in cfg.get("disabled", [])
