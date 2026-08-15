"""
Config loading utility.

Loads configs/config.yaml into a simple attribute-accessible object so the
rest of the codebase can do `cfg.training.lr` instead of `cfg["training"]["lr"]`.
"""

from __future__ import annotations
import yaml
from pathlib import Path


class AttrDict(dict):
    """dict that also supports attribute access, recursively."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key, value in self.items():
            if isinstance(value, dict):
                self[key] = AttrDict(value)

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name, value):
        self[name] = value


def load_config(path: str | Path = "configs/config.yaml") -> AttrDict:
    path = Path(path)
    if not path.exists():
        # allow running scripts from within scripts/ or utils/ directories
        candidate = Path(__file__).resolve().parent.parent / "configs" / "config.yaml"
        if candidate.exists():
            path = candidate
        else:
            raise FileNotFoundError(f"Config file not found at {path} or {candidate}")

    with open(path, "r") as f:
        raw = yaml.safe_load(f)

    return AttrDict(raw)


def get_project_root() -> Path:
    """Returns the LungInsight-AI project root, regardless of caller's cwd."""
    return Path(__file__).resolve().parent.parent
