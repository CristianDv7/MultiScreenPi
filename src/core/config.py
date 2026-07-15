import os
from pathlib import Path

import yaml

CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"
CONFIG_FILE = CONFIG_DIR / "config.yaml"
CONFIG_EXAMPLE_FILE = CONFIG_DIR / "config.example.yaml"

_config = None


def load_config():
    global _config
    if _config is not None:
        return _config

    path = CONFIG_FILE if CONFIG_FILE.exists() else CONFIG_EXAMPLE_FILE
    with open(path, "r", encoding="utf-8") as f:
        _config = yaml.safe_load(f)
    return _config


def get(*keys, default=None):
    cfg = load_config()
    node = cfg
    for key in keys:
        if not isinstance(node, dict) or key not in node:
            return default
        node = node[key]
    return node
