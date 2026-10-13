"""Verify that output cleanup preserves notebook content and is idempotent."""

import json
import runpy
from pathlib import Path


def test_clear_outputs_preserves_cells_and_metadata(tmp_path: Path) -> None:
    script = Path(__file__).resolve().parents[1] / "scripts" / "clear_notebook_outputs.py"
    clear_outputs = runpy.run_path(str(script))["clear_outputs"]
    notebook = {
        "cells": [
            {"cell_type": "markdown", "source": ["Example"], "metadata": {}},
            {
                "cell_type": "code",
                "source": ["print('example')"],
                "metadata": {"tags": ["demo"]},
                "outputs": [{"output_type": "stream", "text": ["example"]}],
                "execution_count": 1,
            },
        ],
        "metadata": {"kernelspec": {"name": "python3"}},
        "nbformat": 4,
    }
    path = tmp_path / "example.ipynb"
    path.write_text(json.dumps(notebook), encoding="utf-8")
    assert clear_outputs(path)
    expected = {
        **notebook,
        "cells": [
            notebook["cells"][0],
            {
                **notebook["cells"][1],
                "outputs": [],
                "execution_count": None,
            },
        ],
    }
    assert json.loads(path.read_text(encoding="utf-8")) == expected
    first_content = path.read_bytes()
    assert not clear_outputs(path)
    assert path.read_bytes() == first_content
