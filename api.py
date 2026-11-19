import json
import os
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

from selector import graph_for, select, prioritize

app = FastAPI(title="ChangeTest")
ROOT = Path(os.environ.get("CHANGE_ROOT", ".")).resolve()


class Changes(BaseModel):
    paths: list[str]


@app.post("/select")
def recommendation(request: Changes):
    kb = os.getenv("CHANGE_KNOWLEDGE")
    links = json.loads(Path(kb).read_text()) if kb else {}
    graph = graph_for(ROOT)
    return {"tests": select(graph, request.paths, links)}


@app.post("/plan")
def plan(request: Changes):
    kb = os.getenv("CHANGE_KNOWLEDGE")
    links = json.loads(Path(kb).read_text()) if kb else {}
    return {"tests": prioritize(graph_for(ROOT), request.paths, links)}
