"""Shared configuration, schema and file helpers for the Kelmarsh Task 1 graph."""
from __future__ import annotations

import csv
import glob
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


def load_graph(path: Path = GRAPH_PICKLE):
    if not path.exists():
        raise FileNotFoundError(f"{path} not found - run `python build.py` first")
    with open(path, "rb") as fh:
        return pickle.load(fh)
