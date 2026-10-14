import tomllib
from pathlib import Path


def test_python_312_is_the_supported_minimum() -> None:
    root = Path(__file__).resolve().parents[1]
    metadata = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    assert metadata["project"]["requires-python"] == ">=3.12"
    assert metadata["tool"]["ruff"]["target-version"] == "py312"
    assert (root / ".python-version").read_text().strip() == "3.12"


def test_jupyter_is_not_a_runtime_dependency() -> None:
    metadata = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    dependencies = metadata["project"]["dependencies"]
    dev_dependencies = metadata["dependency-groups"]["dev"]

    assert not any(dependency.startswith("jupyter") for dependency in dependencies)
    assert any(dependency.startswith("jupyter") for dependency in dev_dependencies)


def test_demo_notebook_starts_with_installed_package_setup_note() -> None:
    import json

    notebook_path = Path("examples/onlinekommentar_demo.ipynb")
    notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    first_markdown_cell = notebook["cells"][0]
    first_code_cell = next(cell for cell in notebook["cells"] if cell["cell_type"] == "code")
    source = "".join(first_code_cell["source"])

    assert "Run `uv sync` from the repo root" in source
    assert "select the repo `.venv`" in source
    assert "sys.path" not in source
    assert "import onlinekommentar" in source
    assert "independently developed" in "".join(first_markdown_cell["source"])
