"""Clear saved notebook outputs and execution counts before committing."""

import argparse
import json
from pathlib import Path


def clear_outputs(path: Path) -> bool:
    """Clear a trusted local notebook, returning whether it was changed."""
    if path.suffix != ".ipynb":
        raise ValueError("Expected an .ipynb file")
    notebook = json.loads(path.read_text(encoding="utf-8"))
    changed = False
    for cell in notebook["cells"]:
        if cell["cell_type"] == "code":
            if cell.get("outputs") or cell.get("execution_count") is not None:
                cell["outputs"] = []
                cell["execution_count"] = None
                changed = True
    if changed:
        path.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return changed


def main() -> int:
    """Clear every supplied notebook; signal modifications to pre-commit."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("notebooks", nargs="+", type=Path)
    paths = parser.parse_args().notebooks
    changed = [clear_outputs(path) for path in paths]
    return int(any(changed))


if __name__ == "__main__":
    raise SystemExit(main())
