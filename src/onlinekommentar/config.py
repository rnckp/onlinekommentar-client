"""Configuration loading and validation for Onlinekommentar client defaults."""

import math
from pathlib import Path
from typing import Annotated, Any
from urllib.parse import urlparse

import yaml
from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    TypeAdapter,
    ValidationInfo,
    field_validator,
)

SUPPORTED_LANGUAGES = frozenset({"en", "de", "fr", "it"})


def _reject_boolean(value: Any) -> Any:
    if isinstance(value, bool):
        raise ValueError("Numeric settings must not be booleans")
    return value


def _validate_timeout(value: float) -> float:
    if not math.isfinite(value):
        raise ValueError("timeout must be finite")
    if value <= 0:
        raise ValueError("timeout must be greater than 0")
    return value


Timeout = Annotated[float, BeforeValidator(_reject_boolean), AfterValidator(_validate_timeout)]
_TIMEOUT_ADAPTER = TypeAdapter(Timeout)


def validate_timeout(value: float) -> float:
    """Validate a finite, positive, non-boolean HTTPX timeout."""
    return _TIMEOUT_ADAPTER.validate_python(value)


class OnlinekommentarConfig(BaseModel):
    """Validated runtime settings loaded from config.yaml when available."""

    model_config = ConfigDict(frozen=True, extra="forbid", hide_input_in_errors=True)

    base_url: str = "https://onlinekommentar.ch"
    timeout: Timeout = 30.0
    rate_limit_delay: float = 0.2
    default_language: str = "en"
    max_retries: int = Field(default=0, ge=0, le=10, strict=True)
    retry_backoff: float = Field(default=1.0, gt=0, allow_inf_nan=False)
    max_retry_delay: float = Field(default=60.0, gt=0, allow_inf_nan=False)

    @field_validator("base_url")
    @classmethod
    def _validate_base_url(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("base_url must not be empty")
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"}:
            raise ValueError("base_url must start with http or https")
        if not parsed.hostname:
            raise ValueError("base_url must include a host")
        try:
            _ = parsed.port  # Access validates the port range and syntax.
        except ValueError as error:
            raise ValueError("base_url must have a valid port") from error
        if parsed.query or parsed.fragment or "?" in value or "#" in value:
            raise ValueError("base_url must not include a query or fragment")
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("base_url must not include credentials")
        if any(character.isspace() or ord(character) < 32 for character in value):
            raise ValueError("base_url must not include whitespace or control characters")
        return value.rstrip("/")

    @field_validator("rate_limit_delay", "retry_backoff", "max_retry_delay", mode="before")
    @classmethod
    def _reject_boolean_numbers(cls, value: Any) -> Any:
        return _reject_boolean(value)

    @field_validator("rate_limit_delay")
    @classmethod
    def _validate_duration(cls, value: float, info: ValidationInfo) -> float:
        if not math.isfinite(value):
            raise ValueError(f"{info.field_name} must be finite")
        if info.field_name == "rate_limit_delay" and value < 0:
            raise ValueError("rate_limit_delay must be greater than or equal to 0")
        return value

    @field_validator("default_language")
    @classmethod
    def _validate_language(cls, value: str) -> str:
        value = value.strip()
        if value not in SUPPORTED_LANGUAGES:
            languages = ", ".join(sorted(SUPPORTED_LANGUAGES))
            raise ValueError(f"default_language must be one of: {languages}")
        return value


DEFAULT_CONFIG = OnlinekommentarConfig()


def load_config(
    config_path: Path | str | None = None, *, discover_config: bool = True
) -> OnlinekommentarConfig:
    """Load validated settings from an optional config.yaml file.

    Args:
        config_path: Settings file; defaults to config.yaml in the working directory.
        discover_config: Read the working-directory file when no explicit path is supplied.

    Returns:
        Validated settings. Missing files use package defaults. A top-level
        onlinekommentar section is supported for shared configuration files.

    Raises:
        ValueError: The document is not a mapping or contains invalid settings.
        yaml.YAMLError: The document contains invalid YAML.
        OSError: An existing file cannot be read.
    """
    if config_path is None and not discover_config:
        return DEFAULT_CONFIG
    path = Path(config_path) if config_path is not None else Path("config.yaml")
    try:
        with path.open(encoding="utf-8") as config_file:
            raw_config = yaml.safe_load(config_file)
    except FileNotFoundError:
        return DEFAULT_CONFIG

    if not isinstance(raw_config, dict):
        raise ValueError(f"Config file must contain a mapping: {path}")
    section = raw_config.get("onlinekommentar", raw_config)
    if not isinstance(section, dict):
        raise ValueError("The 'onlinekommentar' config section must be a mapping")
    if any(not isinstance(key, str) for key in section):
        raise ValueError("Config keys must be strings")
    return OnlinekommentarConfig.model_validate(section)
