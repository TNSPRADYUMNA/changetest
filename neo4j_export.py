"""Publish the local dependency graph to an explicitly configured Neo4j database."""
import argparse
import os
from pathlib import Path

from neo4j import GraphDatabase

from selector import graph_for


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--project", required=True)
    args = parser.parse_args()
    graph = graph_for(args.root)
    with GraphDatabase.driver(os.environ["NEO4J_URI"],
                              auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"])) as driver:
        driver.execute_query("UNWIND $rows AS row MERGE (n:ChangeNode {project:$project,path:row.path}) SET n.kind=row.kind",
                             project=args.project, rows=[{"path": key, **attrs} for key, attrs in graph.nodes(data=True)])
        driver.execute_query(
            "UNWIND $rows AS r MATCH (a:ChangeNode {project:$project,path:r.a}), (b:ChangeNode {project:$project,path:r.b}) "
            "MERGE (a)-[:DEPENDS {kind:r.kind}]->(b)", project=args.project,
            rows=[{"a": a,"b": b,**attrs} for a,b,attrs in graph.edges(data=True)])
