from pathlib import Path

import pytest

from onlinekommentar.config import DEFAULT_CONFIG, OnlinekommentarConfig, load_config


def test_default_config_uses_public_api_defaults() -> None:
    assert DEFAULT_CONFIG == OnlinekommentarConfig()
    assert DEFAULT_CONFIG.base_url == "https://onlinekommentar.ch"
    assert DEFAULT_CONFIG.timeout == 30.0
    assert DEFAULT_CONFIG.rate_limit_delay == 0.2
    assert DEFAULT_CONFIG.default_language == "en"


def test_load_config_reads_onlinekommentar_section(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
onlinekommentar:
  base_url: "https://example.test"
  timeout: 5
  rate_limit_delay: 0
  default_language: "de"
""",
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.base_url == "https://example.test"
    assert config.timeout == 5.0
    assert config.rate_limit_delay == 0.0
    assert config.default_language == "de"


def test_load_config_rejects_unknown_keys(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
onlinekommentar:
  unknown: true
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Unknown config keys: unknown"):
        load_config(config_path)


@pytest.mark.parametrize(
    ("key", "value", "message"),
    [
        ("base_url", "ftp://example.test", "base_url must start with http"),
        ("base_url", "   ", "base_url must not be empty"),
        ("base_url", "https://", "base_url must include a host"),
        ("base_url", "https:///api", "base_url must include a host"),
        ("timeout", 0, "timeout must be greater than 0"),
        ("timeout", "nan", "timeout must be finite"),
        ("timeout", "inf", "timeout must be finite"),
        (
            "rate_limit_delay",
            -0.1,
            "rate_limit_delay must be greater than or equal to 0",
        ),
        ("rate_limit_delay", "nan", "rate_limit_delay must be finite"),
        ("rate_limit_delay", "inf", "rate_limit_delay must be finite"),
        ("default_language", "es", "default_language must be one of"),
    ],
)
def test_load_config_rejects_invalid_values(
    tmp_path: Path,
    key: str,
    value: object,
    message: str,
) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        f"""
onlinekommentar:
  {key}: {value!r}
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=message):
        load_config(config_path)
