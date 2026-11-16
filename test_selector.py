from fastapi.testclient import TestClient

import api
from selector import graph_for, select


def test_relative_module_and_api(tmp_path, monkeypatch):
    package = tmp_path / "pkg"
    package.mkdir()
    (package / "__init__.py").write_text("")
    (package / "worker.py").write_text("def run():\n    return 1\n")
    (package / "wrapper.py").write_text("from . import worker\n")
    (tmp_path / "test_worker.py").write_text("from pkg import wrapper\n")
    assert select(graph_for(tmp_path), ["pkg/worker.py"]) == ["test_worker.py"]
    monkeypatch.setattr(api, "ROOT", tmp_path)
    monkeypatch.delenv("CHANGE_KNOWLEDGE", raising=False)
    with TestClient(api.app) as client:
        response = client.post("/select", json={"paths": ["pkg/worker.py"]})
        assert response.json() == {"tests": ["test_worker.py"]}
