from selector import graph_for, prioritize


def test_all_test_categories_and_knowledge(tmp_path):
    (tmp_path / "core.py").write_text("def value():\n    return 1\n")
    for directory in ("unit","integration","e2e"):
        folder = tmp_path / directory
        folder.mkdir()
        (folder / "test_flow.py").write_text("import core\n")
    (tmp_path / "test_dynamic.py").write_text("def test_dynamic():\n    pass\n")
    rows = prioritize(graph_for(tmp_path), ["core.py"], {"core.py":["test_dynamic.py"]})
    assert [row["category"] for row in rows] == ["unit","unit","integration","end_to_end"]
    assert {row["reason"] for row in rows} == {"dependency","knowledge"}
