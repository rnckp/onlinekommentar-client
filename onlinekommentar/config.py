"""Configuration loading for Onlinekommentar client defaults."""

from dataclasses import dataclass, fields
import math
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

SUPPORTED_LANGUAGES = {"en", "de", "fr", "it"}


@dataclass(frozen=True)
class OnlinekommentarConfig:
    """Runtime settings loaded from config.yaml when available."""

    base_url: str = "https://onlinekommentar.ch"
    timeout: float = 30.0
    rate_limit_delay: float = 0.2
    default_language: str = "en"


DEFAULT_CONFIG = OnlinekommentarConfig()


def _normalize_config_values(values: dict[str, Any]) -> dict[str, Any]:
    normalized = values.copy()
    normalized["base_url"] = str(normalized["base_url"]).strip()
    normalized["timeout"] = float(normalized["timeout"])
    normalized["rate_limit_delay"] = float(normalized["rate_limit_delay"])
    normalized["default_language"] = str(normalized["default_language"]).strip()

    parsed_base_url = urlparse(normalized["base_url"])
    if not normalized["base_url"]:
        raise ValueError("base_url must not be empty")
    if parsed_base_url.scheme not in {"http", "https"}:
        raise ValueError("base_url must start with http or https")
    if not parsed_base_url.netloc:
        raise ValueError("base_url must include a host")
    normalized["base_url"] = normalized["base_url"].rstrip("/")
    if not math.isfinite(normalized["timeout"]):
        raise ValueError("timeout must be finite")
    if normalized["timeout"] <= 0:
        raise ValueError("timeout must be greater than 0")
    if not math.isfinite(normalized["rate_limit_delay"]):
        raise ValueError("rate_limit_delay must be finite")
    if normalized["rate_limit_delay"] < 0:
        raise ValueError("rate_limit_delay must be greater than or equal to 0")
    if normalized["default_language"] not in SUPPORTED_LANGUAGES:
        languages = ", ".join(sorted(SUPPORTED_LANGUAGES))
        raise ValueError(f"default_language must be one of: {languages}")
    return normalized


def load_config(config_path: Path | str | None = None) -> OnlinekommentarConfig:
    """
    Load runtime settings from config.yaml.

    Missing config files are treated as an instruction to use package defaults.
    A top-level ``onlinekommentar`` section is supported for shared config files.
    """
    path = Path(config_path) if config_path is not None else Path("config.yaml")
    if not path.exists():
        return DEFAULT_CONFIG

    with path.open(encoding="utf-8") as config_file:
        raw_config = yaml.safe_load(config_file) or {}

    if not isinstance(raw_config, dict):
        raise ValueError(f"Config file must contain a mapping: {path}")

    section = raw_config.get("onlinekommentar", raw_config)
    if not isinstance(section, dict):
        raise ValueError("The 'onlinekommentar' config section must be a mapping")

    allowed_keys = {field.name for field in fields(OnlinekommentarConfig)}
    unknown_keys = sorted(set(section) - allowed_keys)
    if unknown_keys:
        raise ValueError(f"Unknown config keys: {', '.join(unknown_keys)}")

    values = _normalize_config_values(DEFAULT_CONFIG.__dict__.copy() | section)
    return OnlinekommentarConfig(**values)
