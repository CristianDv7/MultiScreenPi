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


def set_value(*keys, value):
    """Actualiza un valor en memoria y lo persiste en config/config.yaml."""
    cfg = load_config()
    node = cfg
    for key in keys[:-1]:
        node = node.setdefault(key, {})
    node[keys[-1]] = value
    _save(cfg)


def _save(cfg):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)
