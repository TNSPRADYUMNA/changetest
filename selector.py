"""Build a Python import/test impact graph with Tree-sitter and NetworkX."""
import argparse
import json
import subprocess
from pathlib import Path

import networkx as nx
from tree_sitter import Language, Parser
import tree_sitter_python

PARSER = Parser(Language(tree_sitter_python.language()))


def graph_for(root):
    g = nx.DiGraph()
    modules = {}
    for file in sorted(root.rglob("*.py")):
        relative = file.relative_to(root)
        if any(p.startswith(".") or p in {"__pycache__", "venv"} for p in relative.parts):
            continue
        name = ".".join(relative.with_suffix("").parts).removesuffix(".__init__")
        modules[name] = relative.as_posix()
        g.add_node(relative.as_posix(), kind="test" if file.name.startswith("test_") else "module")
    for name, path in modules.items():
        payload = (root / path).read_bytes()
        tree = PARSER.parse(payload)
        stack = [tree.root_node]
        if tree.root_node.has_error:
            g.nodes[path]["uncertain"] = True
        while stack:
            node = stack.pop()
            stack.extend(node.named_children)
            if node.type in {"function_definition", "class_definition"}:
                label = node.child_by_field_name("name").text.decode()
                symbol = f"{path}:{node.start_point.row+1}:{label}"
                g.add_node(symbol, kind=node.type)
                g.add_edge(path, symbol, kind="defines")
            if node.type == "import_from_statement":
                imported = node.child_by_field_name("module_name")
                if imported:
                    target = imported.text.decode()
                    if target.startswith("."):
                        level = len(target) - len(target.lstrip("."))
                        parts = name.split(".")[:-level]
                        target = ".".join([*parts, target.lstrip(".")]).rstrip(".")
                    if target in modules:
                        g.add_edge(modules[target], path, kind="import")
            if node.type == "import_statement":
                for child in node.named_children:
                    target = child.text.decode().split(" as ")[0]
                    if target in modules:
                        g.add_edge(modules[target], path, kind="import")
    return g


def select(g, changes, links=None):
    tests = {k for k, v in g.nodes(data=True) if v["kind"] == "test"}
    if not changes:
        return []
    if any(path not in g or g.nodes[path].get("uncertain") or Path(path).name in {"conftest.py", "__init__.py"}
           for path in changes) or any(attrs.get("uncertain") for _, attrs in g.nodes(data=True)):
        return sorted(tests)
    impacted = set(changes)
    for path in changes:
        impacted.update(nx.descendants(g, path))
        impacted.update((links or {}).get(path, []))
    return sorted(impacted & tests)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("changed", nargs="*")
    parser.add_argument("--base", help="Git base revision for comparing committed files with HEAD")
    parser.add_argument("--knowledge", type=Path)
    args = parser.parse_args()
    links = json.loads(args.knowledge.read_text()) if args.knowledge else {}
    changes = args.changed
    if args.base:
        revision = subprocess.check_output(["git", "rev-parse", "--verify", "--end-of-options",
                                            args.base + "^{commit}"], cwd=args.root, text=True).strip()
        raw = subprocess.check_output(["git", "diff", "--name-only", "-z", revision, "HEAD", "--"],
                                      cwd=args.root)
        changes = raw.decode().strip("\0").split("\0") if raw else []
    print(json.dumps(select(graph_for(args.root), changes, links)))


if __name__ == "__main__":
    main()
