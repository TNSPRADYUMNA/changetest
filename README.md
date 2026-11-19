# ChangeTest

Select Python test files from a change set. Tree-sitter parses imports, classes and functions. NetworkX follows reverse import dependencies from edited modules to tests. A JSON knowledge file adds coverage relationships that static imports miss, such as dynamic imports and integration contracts. Unknown or unparseable changes and shared pytest configuration trigger a wider test selection.

## Reproduce and use

```sh
python -m pip install -r requirements.txt
python benchmark.py
python selector.py /path/to/repo module.py --knowledge links.json
python selector.py /path/to/repo --base HEAD~1 --knowledge links.json
python -m uvicorn api:app --host 127.0.0.1 --port 8050
```

A knowledge file maps repository-relative paths to known tests, for example `{"module.py":["tests/test_contract.py"]}`. Set `CHANGE_ROOT` and `CHANGE_KNOWLEDGE` for the API and POST `{"paths":["module.py"]}` to `/select`. The optional `neo4j_export.py` writes nodes and relationships to a configured Neo4j database. It requires `NEO4J_URI`, `NEO4J_USER` and `NEO4J_PASSWORD`. The graph includes symbol definitions, with test selection operating at file granularity.

## Verified mutation results

Use `--explain` on the selector or POST a change set to `/plan` for a prioritized plan with a reason and dependency distance. Tests in `unit/`, `integration/`, and `e2e/` or `end_to_end/` are classified by directory. Unit tests are scheduled first, followed by integration and end-to-end tests, with nearer dependencies first within each category. Explicit knowledge links can supply dynamic coverage. Category conventions and static imports must be maintained for the repository.

The graph records import edges and function/class definitions. This is a partial program graph; it does not resolve arbitrary dynamic calls or provide a complete code property graph. The published evaluation measures test-file selection and missed failing files on the mutation fixture.

| Selection | Failed test files caught | Files scheduled across six changes |
| --- | ---: | ---: |
| Full pytest | 7 / 7 | 42 |
| Static imports | 6 / 7 | 6 |
| Imports plus knowledge | 7 / 7 | 7 |

The knowledge-based selector scheduled **83.3% fewer files** and took **8.58 s versus 9.60 s** across the local pytest subprocesses. It recovered the dynamic contract test, which static imports missed. File-level precision on this narrow fixture is 7/7. This result will change with fixture breadth and graph completeness. FastAPI and Neo4j are additional interfaces. The reported mutation tests ran through the CLI selector and pytest fixture. [Per-mutation report](results.json)
