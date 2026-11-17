"""Shared configuration, schema and file helpers for the Kelmarsh Task 1 graph."""
from __future__ import annotations

import csv
import glob
import gzip
import os
import pickle
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("KELMARSH_DATA_DIR",
                               ROOT / "raw_data" / "Kelmarsh_SCADA_2021_4456"))
MANUAL_TABLE = ROOT / "data" / "manual_signal_component.csv"
OUT_DIR = ROOT / "output"
GRAPH_PICKLE = OUT_DIR / "graph_task1.pkl"

# Scope agreed in the proposal
TURBINES = [1, 6]                    # Kelmarsh 1 and Kelmarsh 6
EVENT_STATUSES = {"Stop", "Warning"}
SCOPE_YEAR = 2021

# ---------------------------------------------------------------- schema
# required properties per node type (source_file / source_line are required for all)
NODE_SCHEMA = {
    "Turbine": ["name", "model"],
    "Signal": ["name", "unit"],
    "Component": ["name"],
    "EventCode": ["code", "message"],
    "Event": ["start", "end", "status"],
    "Observation": ["time", "value"],
}
ID_PREFIX = {
    "Turbine": "turbine:", "Signal": "signal:", "Component": "component:",
    "EventCode": "code:", "Event": "event:", "Observation": "obs:",
}
# relationship type -> (allowed source type, allowed target type)
EDGE_SCHEMA = {
    "HAS_OBSERVATION": ("Turbine", "Observation"),
    "OF_SIGNAL": ("Observation", "Signal"),
    "HAS_EVENT": ("Turbine", "Event"),
    "HAS_CODE": ("Event", "EventCode"),
    "MEASURES_ON": ("Signal", "Component"),
}


def turbine_id(n: int) -> str:
    return f"turbine:Kelmarsh_{n}"


def find_file(kind: str, n: int) -> Path:
    """kind = 'Turbine_Data' or 'Status'."""
    hits = glob.glob(str(DATA_DIR / f"{kind}_Kelmarsh_{n}_*.csv"))
    if len(hits) != 1:
        raise FileNotFoundError(
            f"Expected one {kind} file for Kelmarsh {n} in {DATA_DIR}, found {hits}. "
            "Set KELMARSH_DATA_DIR to the folder with the unzipped Kelmarsh_SCADA_2021_4456.zip")
    return Path(hits[0])


def read_header(path: Path):
    """Return (metadata dict, header line number (1-based), column names).

    Greenbyte exports start with '#' comment lines. In SCADA files the column
    header itself is also commented ('# Date and time,...').
    """
    meta = {}
    with open(path, encoding="utf-8") as fh:
        for i, line in enumerate(fh, start=1):
            s = line.rstrip("\n")
            if s.startswith("# Date and time") or s.startswith("Timestamp start"):
                cols = next(csv.reader([s.lstrip("# ") if s.startswith("#") else s]))
                return meta, i, cols
            if s.startswith("# ") and ":" in s:
                k, v = s[2:].split(":", 1)
                meta.setdefault(k.strip(), (v.strip(), i))
    raise ValueError(f"No column header found in {path}")


def save_graph(G, path: Path = GRAPH_PICKLE):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as fh:
        pickle.dump(G, fh, protocol=pickle.HIGHEST_PROTOCOL)


NODES_EXPORT = OUT_DIR / "nodes.csv.gz"
EDGES_EXPORT = OUT_DIR / "edges.csv.gz"
# property types in the CSV export (columns that are empty for some node types are written as floats)
INT_PROPS = {"source_line", "column_index", "code"}
BOOL_PROPS = {"starts_in_scope"}
FLOAT_PROPS = {"value"}
INT_TEXT_PROPS = {"greenbyte_file_id"}   # text of an integer, e.g. "228"


def _typed(col: str, text: str):
    if col in INT_PROPS:
        return int(float(text))
    if col in BOOL_PROPS:
        return text == "True"
    if col in FLOAT_PROPS:
        return float(text)          # the export holds repr() of the float, so this is exact
    if col in INT_TEXT_PROPS:
        return str(int(float(text)))
    return text


def graph_from_export(nodes_path: Path = NODES_EXPORT, edges_path: Path = EDGES_EXPORT):
    """Rebuild the graph from the saved export (nodes.csv.gz, edges.csv.gz) without the raw data.
    Empty cells are properties the node or edge does not have."""
    import networkx as nx
    G = nx.MultiDiGraph()
    with gzip.open(nodes_path, "rt", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            nid = row.pop("id")
            G.add_node(nid, **{k: _typed(k, v) for k, v in row.items() if v != ""})
    with gzip.open(edges_path, "rt", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            u, v = row.pop("source"), row.pop("target")
            G.add_edge(u, v, key=row["type"], **{k: _typed(k, x) for k, x in row.items() if x != ""})
    return G


def load_graph(path: Path = GRAPH_PICKLE):
    """The saved graph. Without the pickle (e.g. in a fresh clone of the repository) the graph is
    rebuilt from the committed export and cached as the pickle for the next start."""
    if path.exists():
        with open(path, "rb") as fh:
            return pickle.load(fh)
    if path == GRAPH_PICKLE and NODES_EXPORT.exists() and EDGES_EXPORT.exists():
        G = graph_from_export()
        save_graph(G, path)
        return G
    raise FileNotFoundError(f"{path} not found - run `python build.py` first")
