"""Task 1: build the initial Kelmarsh knowledge graph from structured CSV records.

Usage:  python build.py
Output: output/graph_task1.pkl, output/nodes.csv.gz, output/edges.csv.gz,
        output/build_log/*.csv (rejected / duplicate / missing records), output/build_summary.json
"""
from __future__ import annotations

import csv
import json
import math
from collections import Counter
from datetime import datetime, timezone

import networkx as nx
import pandas as pd

from kg_common import (DATA_DIR, EDGE_SCHEMA, EVENT_STATUSES, ID_PREFIX, MANUAL_TABLE,
                       NODE_SCHEMA, OUT_DIR, SCOPE_YEAR, TURBINES, find_file, read_header,
                       save_graph, turbine_id)


class GraphBuilder:
    """Wraps a MultiDiGraph and enforces the schema on every insert.

    Node ids are deterministic, so importing the same record twice changes nothing
    (repeated imports are idempotent). Conflicting re-imports are logged, not overwritten.
    """

    def __init__(self):
        self.G = nx.MultiDiGraph()
        self.log = {"rejected_edges": [], "node_conflicts": [], "rejected_records": [],
                    "duplicate_records": [], "missing_values": []}
        self.repeat_node = 0
        self.repeat_edge = 0

    def add_node(self, nid: str, ntype: str, source_file: str, source_line: int, **props):
        assert ntype in NODE_SCHEMA and nid.startswith(ID_PREFIX[ntype]), (nid, ntype)
        attrs = {"type": ntype, "source_file": source_file, "source_line": source_line, **props}
        if nid in self.G:
            old = self.G.nodes[nid]
            diff = {k: (old.get(k), v) for k, v in props.items() if old.get(k) != v}
            if diff:
                self.log["node_conflicts"].append({"id": nid, "diff": json.dumps(diff, default=str),
                                                   "kept_source_line": old["source_line"],
                                                   "ignored_source_line": source_line})
            else:
                self.repeat_node += 1
            return
        self.G.add_node(nid, **attrs)

    def add_edge(self, u: str, rel: str, v: str, source_file: str, source_line: int,
                 evidence: str = "csv_field", **props) -> bool:
        reason = None
        if rel not in EDGE_SCHEMA:
            reason = "unknown relationship"
        elif u not in self.G or v not in self.G:
            reason = "endpoint missing"
        elif (self.G.nodes[u]["type"], self.G.nodes[v]["type"]) != EDGE_SCHEMA[rel]:
            reason = f"type mismatch {self.G.nodes[u]['type']}->{self.G.nodes[v]['type']}"
        if reason:
            self.log["rejected_edges"].append({"u": u, "rel": rel, "v": v, "reason": reason,
                                               "source_file": source_file, "source_line": source_line})
            return False
        if self.G.has_edge(u, v, key=rel):
            self.repeat_edge += 1
            return True
        self.G.add_edge(u, v, key=rel, type=rel, source_file=source_file,
                        source_line=source_line, evidence=evidence, **props)
        return True


# ------------------------------------------------------------------ loaders
def load_turbines(b: GraphBuilder):
    for n in TURBINES:
        path = find_file("Turbine_Data", n)
        meta, _, _ = read_header(path)
        name, line = meta["Turbine"]
        model, model_line = meta["Turbine type"]
        tz, tz_line = meta.get("Time zone", ("", 0))
        b.add_node(turbine_id(n), "Turbine", path.name, line, name=name, model=model,
                   greenbyte_file_id=path.stem.rsplit("_", 1)[-1], time_zone=tz,
                   # header line of each property (greenbyte_file_id comes from the file name)
                   property_source_lines=f"name:{line};model:{model_line};time_zone:{tz_line}")


def load_signals_and_components(b: GraphBuilder):
    """Signals = the 13 selected SCADA columns; Signal->Component from the manual starter table."""
    table = pd.read_csv(MANUAL_TABLE, dtype=str, keep_default_na=False)
    ref_file = find_file("Turbine_Data", TURBINES[0])
    _, hdr_line, cols = read_header(ref_file)
    for i, row in table.iterrows():
        line = i + 2  # header is line 1 of the manual table
        col = row.scada_column
        if col not in cols:
            b.log["rejected_records"].append({"source_file": MANUAL_TABLE.name, "source_line": line,
                                              "reason": f"column not in SCADA header: {col}"})
            continue
        name, unit = col.rsplit(" (", 1)
        b.add_node(row.signal_id, "Signal", ref_file.name, hdr_line, name=name,
                   unit=unit.rstrip(")"), scada_column=col, column_index=cols.index(col))
        if row.component_id:
            b.add_node(row.component_id, "Component", MANUAL_TABLE.name, line,
                       name=row.component_name)
            b.add_edge(row.signal_id, "MEASURES_ON", row.component_id, MANUAL_TABLE.name, line,
                       evidence="manual", justification=row.justification)
    return table


def load_events(b: GraphBuilder) -> dict[int, set]:
    """Stop/Warning rows -> Event + EventCode. Returns alarm days per turbine."""
    alarm_days = {}
    for n in TURBINES:
        path = find_file("Status", n)
        _, hdr_line, _ = read_header(path)
        df = pd.read_csv(path, skiprows=hdr_line - 1, skip_blank_lines=False, dtype=str,
                         keep_default_na=False)
        df["_line"] = df.index + hdr_line + 1
        out_of_scope = Counter(df.loc[~df.Status.isin(EVENT_STATUSES), "Status"])
        for st, cnt in out_of_scope.items():
            b.log["rejected_records"].append({"source_file": path.name, "source_line": "",
                                              "reason": f"status '{st}' outside scope ({cnt} rows)"})
        df = df[df.Status.isin(EVENT_STATUSES)]
        seen, days = {}, set()
        tid = turbine_id(n)
        for r in df.to_dict("records"):
            line = int(r["_line"])
            t0, t1 = r["Timestamp start"], r["Timestamp end"]
            try:
                start = datetime.strptime(t0, "%Y-%m-%d %H:%M:%S")
                datetime.strptime(t1, "%Y-%m-%d %H:%M:%S")
                code = int(r["Code"])
            except (ValueError, TypeError) as e:
                b.log["rejected_records"].append({"source_file": path.name, "source_line": line,
                                                  "reason": f"unparsable row: {e}"})
                continue
            key = (t0, t1, r["Status"], code)
            if key in seen:  # exact duplicate of an earlier row -> same real event
                b.log["duplicate_records"].append({"source_file": path.name, "source_line": line,
                                                   "duplicate_of_line": seen[key]})
                continue
            seen[key] = line
            cid = f"code:{code}"
            b.add_node(cid, "EventCode", path.name, line, code=code, message=r["Message"])
            eid = f"event:Kelmarsh_{n}:L{line}"
            b.add_node(eid, "Event", path.name, line, start=t0, end=t1, duration=r["Duration"],
                       status=r["Status"], starts_in_scope=(start.year == SCOPE_YEAR))
            b.add_edge(tid, "HAS_EVENT", eid, path.name, line)
            b.add_edge(eid, "HAS_CODE", cid, path.name, line)
            if start.year == SCOPE_YEAR:
                days.add(start.date())
        alarm_days[n] = days
    return alarm_days


def load_observations(b: GraphBuilder, alarm_days: dict[int, set]):
    """One Observation per (turbine, 10-min timestamp, signal) on days with a Stop/Warning event."""
    signals = [(nid, d["column_index"], d["scada_column"]) for nid, d in b.G.nodes(data=True)
               if d["type"] == "Signal"]
    for n in TURBINES:
        path = find_file("Turbine_Data", n)
        _, hdr_line, cols = read_header(path)
        idx = [0] + [ci for _, ci, _ in signals]
        df = pd.read_csv(path, skiprows=hdr_line, header=None, usecols=idx,
                         skip_blank_lines=False, low_memory=False)
        df["_line"] = df.index + hdr_line + 1
        df["_ts"] = pd.to_datetime(df[0], format="%Y-%m-%d %H:%M:%S")
        dup = df["_ts"].duplicated(keep="first")
        for line, first in zip(df.loc[dup, "_line"], df.loc[dup, 0]):
            b.log["duplicate_records"].append({"source_file": path.name, "source_line": int(line),
                                               "duplicate_of_line": f"timestamp {first}"})
        df = df[~dup & df["_ts"].dt.date.isin(alarm_days[n])]
        tid = turbine_id(n)
        G = b.G
        for sid, ci, col in signals:
            slug = sid.split(":", 1)[1]
            for ts, val, line in zip(df[0], df[ci], df["_line"]):
                line = int(line)
                if val is None or (isinstance(val, float) and math.isnan(val)):
                    b.log["missing_values"].append({"turbine": tid, "time": ts, "signal": sid,
                                                    "source_file": path.name, "source_line": line})
                    continue
                oid = f"obs:Kelmarsh_{n}:{ts.replace(' ', 'T')}:{slug}"
                # direct inserts for speed; ids/types are guaranteed by construction and checked later
                if oid in G:
                    b.repeat_node += 1
                    continue
                G.add_node(oid, type="Observation", time=ts, value=float(val),
                           source_file=path.name, source_line=line)
                G.add_edge(tid, oid, key="HAS_OBSERVATION", type="HAS_OBSERVATION",
                           source_file=path.name, source_line=line, evidence="csv_field")
                G.add_edge(oid, sid, key="OF_SIGNAL", type="OF_SIGNAL",
                           source_file=path.name, source_line=line, evidence="csv_field")


def export(b: GraphBuilder, alarm_days):
    OUT_DIR.mkdir(exist_ok=True)
    save_graph(b.G)
    nodes = pd.DataFrame([{"id": n, **d} for n, d in b.G.nodes(data=True)])
    nodes.to_csv(OUT_DIR / "nodes.csv.gz", index=False)
    edges = pd.DataFrame([{"source": u, "target": v, **d} for u, v, d in b.G.edges(data=True)])
    edges.to_csv(OUT_DIR / "edges.csv.gz", index=False)
    logdir = OUT_DIR / "build_log"
    logdir.mkdir(exist_ok=True)
    for name, rows in b.log.items():
        pd.DataFrame(rows).to_csv(logdir / f"{name}.csv", index=False)
    summary = {
        "built_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "data_dir": str(DATA_DIR),
        "nodes": b.G.number_of_nodes(), "edges": b.G.number_of_edges(),
        "nodes_by_type": dict(Counter(d["type"] for _, d in b.G.nodes(data=True))),
        "edges_by_type": dict(Counter(d["type"] for *_, d in b.G.edges(data=True))),
        "alarm_days": {f"Kelmarsh_{n}": len(d) for n, d in alarm_days.items()},
        "log_counts": {k: len(v) for k, v in b.log.items()},
        "repeated_identical_inserts": {"nodes": b.repeat_node, "edges": b.repeat_edge},
    }
    (OUT_DIR / "build_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def build() -> GraphBuilder:
    b = GraphBuilder()
    load_turbines(b)
    load_signals_and_components(b)
    days = load_events(b)
    load_observations(b, days)
    return b, days


if __name__ == "__main__":
    b, days = build()
    print(json.dumps(export(b, days), indent=2))
