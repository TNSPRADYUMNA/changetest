"""Run selected and full pytest suites against seeded mutations."""
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from selector import graph_for, select


def run(root, files):
    start = time.perf_counter()
    proc = subprocess.run([sys.executable, "-m", "pytest", "-q", "--import-mode=prepend", *files],
                          cwd=root, capture_output=True, text=True, timeout=60)
    if proc.returncode not in (0,1):
        raise RuntimeError(proc.stdout + proc.stderr)
    failed = sorted(line.split()[1].split("::")[0] for line in proc.stdout.splitlines()
                    if line.startswith("FAILED "))
    return set(failed), time.perf_counter() - start


def benchmark():
    report = []
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        for i in range(6):
            (root / f"component{i}.py").write_text(f"def quote():\n    return {i}\n")
            (root / f"test_component{i}.py").write_text(
                f"from component{i} import quote\ndef test_quote():\n    assert quote() == {i}\n")
        # A dynamic integration dependency is supplied through the knowledge base.
        (root / "test_contract.py").write_text(
            "from importlib import import_module\ndef test_contract():\n    assert import_module('component0').quote() == 0\n")
        g = graph_for(root)
        tests = sorted(node for node, attrs in g.nodes(data=True) if attrs["kind"]=="test")
        for i in range(6):
            file = f"component{i}.py"
            target = root / file
            healthy = target.read_text()
            target.write_text("def quote():\n    return -1\n")
            try:
                actual, full_secs = run(root, tests)
                for method, kb in (("imports", {}), ("knowledge", {"component0.py":["test_contract.py"]})):
                    chosen = select(g, [file], kb)
                    caught, secs = run(root, chosen)
                    assert caught <= actual
                    report.append({"change": file, "method": method, "selected": chosen,
                                   "failed_full": sorted(actual), "caught": sorted(caught),
                                   "precision": len(caught)/len(chosen), "recall": len(caught)/len(actual),
                                   "selected_seconds": secs, "full_seconds": full_secs})
            finally:
                target.write_text(healthy)
    Path("results.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print({method: sum(len(r["caught"]) for r in report if r["method"]==method) for method in ("imports","knowledge")})


if __name__ == "__main__":
    benchmark()
