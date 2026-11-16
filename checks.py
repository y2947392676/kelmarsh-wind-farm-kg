"""Task 1 graph checks.

Usage:  python checks.py
Output: output/checks/check_report.md, output/checks/fact_verification_sample.csv
"""
from __future__ import annotations

import csv
import json
import random
from collections import Counter, defaultdict

import pandas as pd

from build import build, load_events
from kg_common import (DATA_DIR, EDGE_SCHEMA, ID_PREFIX, MANUAL_TABLE, NODE_SCHEMA, OUT_DIR,
                       load_graph)

CHECK_DIR = OUT_DIR / "checks"
SAMPLE_SIZE = 50
SEED = 42


def check_nodes(G):
    problems = []
    for nid, d in G.nodes(data=True):
        t = d.get("type")
        if t not in NODE_SCHEMA:
            problems.append((nid, f"unknown type {t}"))
            continue
        if not nid.startswith(ID_PREFIX[t]):
            problems.append((nid, f"id prefix does not match type {t}"))
        for p in NODE_SCHEMA[t] + ["source_file", "source_line"]:
            if d.get(p) in (None, ""):
                problems.append((nid, f"missing required property '{p}'"))
    return problems


def check_edges(G):
    problems = []
    for u, v, k, d in G.edges(keys=True, data=True):
        rel = d.get("type")
        if rel not in EDGE_SCHEMA or k != rel:
            problems.append((u, rel, v, "unknown relationship / key mismatch"))
            continue
        if (G.nodes[u].get("type"), G.nodes[v].get("type")) != EDGE_SCHEMA[rel]:
            problems.append((u, rel, v, "endpoint types not allowed"))
        if not d.get("source_file") or not d.get("source_line"):
            problems.append((u, rel, v, "missing provenance"))
    return problems


def check_cardinality(G):
    """Every Observation: 1 turbine, 1 signal. Every Event: 1 turbine, 1 code."""
    bad = Counter()
    for nid, d in G.nodes(data=True):
        if d["type"] == "Observation":
            ins = [k for _, _, k in G.in_edges(nid, keys=True)]
            outs = [k for _, _, k in G.out_edges(nid, keys=True)]
            if ins != ["HAS_OBSERVATION"] or outs != ["OF_SIGNAL"]:
                bad["Observation"] += 1
        elif d["type"] == "Event":
            ins = [k for _, _, k in G.in_edges(nid, keys=True)]
            outs = [k for _, _, k in G.out_edges(nid, keys=True)]
            if ins != ["HAS_EVENT"] or outs != ["HAS_CODE"]:
                bad["Event"] += 1
    return dict(bad)


def check_idempotency(G_saved):
    """Rebuild from the raw files twice; re-import events into an already built graph."""
    b, _ = build()
    same_nodes = set(b.G.nodes) == set(G_saved.nodes)
    same_edges = (set(b.G.edges(keys=True)) == set(G_saved.edges(keys=True)))
    # compare every property, not only the id sets
    node_attr_diff = sum(1 for n, d in b.G.nodes(data=True) if G_saved.nodes.get(n) != d) if same_nodes else None
    edge_attr_diff = (sum(1 for u, v, k, d in b.G.edges(keys=True, data=True)
                          if G_saved.edges[u, v, k] != d) if same_edges else None)
    n0, e0 = b.G.number_of_nodes(), b.G.number_of_edges()
    load_events(b)  # second import of the same Status files
    return {"rebuild_identical_nodes": same_nodes, "rebuild_identical_edges": same_edges,
            "rebuild_nodes_with_different_properties": node_attr_diff,
            "rebuild_edges_with_different_properties": edge_attr_diff,
            "nodes_after_reimport": (n0, b.G.number_of_nodes()),
            "edges_after_reimport": (e0, b.G.number_of_edges()),
            "conflicts_after_reimport": len(b.log["node_conflicts"])}


def read_lines(path, wanted: set[int]) -> dict[int, str]:
    out = {}
    with open(path, encoding="utf-8") as fh:
        for i, line in enumerate(fh, start=1):
            if i in wanted:
                out[i] = line.rstrip("\n")
                if len(out) == len(wanted):
                    break
    return out


def sample_facts(G):
    """Stratified random sample of graph facts, each re-read from the cited source line."""
    rng = random.Random(SEED)
    by_type = defaultdict(list)
    for u, v, k, d in G.edges(keys=True, data=True):
        by_type[k].append((u, v, d))
    plan = {"HAS_OBSERVATION": 25, "HAS_EVENT": 10, "HAS_CODE": 10, "MEASURES_ON": 5}
    facts = []
    for rel, n in plan.items():
        for u, v, d in rng.sample(sorted(by_type[rel], key=lambda x: (x[0], x[1])), n):
            facts.append((rel, u, v, d))

    wanted = defaultdict(set)
    for _, _, _, d in facts:
        wanted[d["source_file"]].add(int(d["source_line"]))
    raw = {}
    for fname, lines in wanted.items():
        path = MANUAL_TABLE if fname == MANUAL_TABLE.name else DATA_DIR / fname
        raw[fname] = read_lines(path, lines)

    rows = []
    for rel, u, v, d in facts:
        line = raw[d["source_file"]][int(d["source_line"])]
        fields = next(csv.reader([line]))
        if rel == "HAS_OBSERVATION":
            o = G.nodes[v]
            sig = next(iter(G.successors(v)))
            ci = G.nodes[sig]["column_index"]
            claim = f"{G.nodes[u]['name']} @ {o['time']} {G.nodes[sig]['name']} = {o['value']}"
            ok = fields[0] == o["time"] and abs(float(fields[ci]) - o["value"]) < 1e-9
            where = f"column 1 (Date and time) | column {ci + 1} ({G.nodes[sig]['scada_column']})"
            shown = f"{fields[0]} | {fields[ci]}"
        elif rel == "HAS_EVENT":
            e = G.nodes[v]
            claim = f"{G.nodes[u]['name']} {e['status']} event starting {e['start']}"
            ok = fields[0] == e["start"] and fields[3] == e["status"]
            where, shown = "column 1 (Timestamp start) | column 4 (Status)", f"{fields[0]} | {fields[3]}"
        elif rel == "HAS_CODE":
            c = G.nodes[v]
            claim = f"event {u} has code {c['code']} '{c['message']}'"
            ok = int(fields[4]) == c["code"] and fields[5] == c["message"]
            where, shown = "column 5 (Code) | column 6 (Message)", f"{fields[4]} | {fields[5]}"
        else:  # MEASURES_ON, manual table
            claim = f"{u} MEASURES_ON {v}"
            ok = fields[1] == u and fields[2] == v
            where = "column 2 (signal_id) | column 3 (component_id) | column 5 (justification)"
            shown = f"{fields[1]} | {fields[2]} | {fields[4]}"
        rows.append({"relationship": rel, "graph_claim": claim, "source_file": d["source_file"],
                     "source_line": d["source_line"], "evidence": d["evidence"],
                     "source_columns": where, "source_values": shown,
                     "raw_line_excerpt": line[:160], "auto_match": ok,
                     "human_verdict": "", "human_note": ""})
    return pd.DataFrame(rows)


def statistics(G):
    obs_per_signal = Counter()
    for nid, d in G.nodes(data=True):
        if d["type"] == "Observation":
            obs_per_signal[next(iter(G.successors(nid)))] += 1
    events = Counter()
    for u, v, k in G.edges(keys=True):
        if k == "HAS_EVENT":
            events[(G.nodes[u]["name"], G.nodes[v]["status"])] += 1
    miss = pd.read_csv(OUT_DIR / "build_log" / "missing_values.csv")
    return obs_per_signal, events, miss.groupby("signal").size().to_dict()


def main():
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    G = load_graph()
    summary = json.loads((OUT_DIR / "build_summary.json").read_text(encoding="utf-8"))
    node_p, edge_p, card = check_nodes(G), check_edges(G), check_cardinality(G)
    idem = check_idempotency(G)
    sample = sample_facts(G)
    old_path = CHECK_DIR / "fact_verification_sample.csv"
    if old_path.exists():  # never overwrite verdicts a person already entered
        old = pd.read_csv(old_path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
        key = ["relationship", "graph_claim", "source_file", "source_line"]
        sample["source_line"] = sample["source_line"].astype(str)
        kept = old[key + ["human_verdict", "human_note"]]
        sample = sample.drop(columns=["human_verdict", "human_note"]).merge(kept, on=key, how="left")
        sample[["human_verdict", "human_note"]] = sample[["human_verdict", "human_note"]].fillna("")
    sample.to_csv(CHECK_DIR / "fact_verification_sample.csv", index=False, encoding="utf-8-sig")
    obs_per_signal, events, miss = statistics(G)
    rejected = pd.read_csv(OUT_DIR / "build_log" / "rejected_records.csv")

    L = ["# Task 1 graph check report", "",
         f"Graph built at {summary['built_at_utc']} from `{summary['data_dir']}`.", "",
         "## Statistics", "",
         f"- Nodes: {summary['nodes']:,}; edges: {summary['edges']:,}",
         f"- Nodes by type: {summary['nodes_by_type']}",
         f"- Edges by type: {summary['edges_by_type']}",
         f"- Alarm days loaded (Stop/Warning start in 2021): {summary['alarm_days']}",
         "", "| Turbine | Status | Events |", "|---|---|---|"]
    L += [f"| {t} | {s} | {c} |" for (t, s), c in sorted(events.items())]
    L += ["", "| Signal | Observations | Missing (NaN) slots |", "|---|---|---|"]
    L += [f"| {s} | {c:,} | {miss.get(s, 0):,} |" for s, c in sorted(obs_per_signal.items())]
    L += ["", "## Integrity checks", "",
          f"- Unique ids: guaranteed by graph keys; conflicting re-inserts of an existing id: "
          f"{summary['log_counts']['node_conflicts']} (includes code-message conflicts)",
          f"- Node problems (id prefix / required properties / provenance): {len(node_p)}",
          f"- Edge problems (allowed types / existing endpoints / provenance): {len(edge_p)}",
          f"- Edges rejected during build: {summary['log_counts']['rejected_edges']}",
          f"- Cardinality violations: {card or 'none'}",
          f"- Exact duplicate Stop/Warning rows skipped: {summary['log_counts']['duplicate_records']}",
          f"- Identical repeated inserts absorbed: {summary['repeated_identical_inserts']}",
          "- Records outside the schema scope (not imported):"]
    L += [f"  - {r.source_file}: {r.reason}" for r in rejected.itertuples()]
    L += ["", "## Repeated import", "", f"```\n{json.dumps(idem, indent=2)}\n```", "",
          "## Fact sample against sources", "",
          f"{len(sample)} facts (seed {SEED}, stratified by relationship) were re-read from the "
          f"cited source line: {int(sample.auto_match.astype(str).eq('True').sum())}/{len(sample)} "
          "match automatically.", "",
          f"Manual check by a person (`human_verdict` in `fact_verification_sample.csv`): "
          f"{int(sample.human_verdict.astype(str).str.strip().ne('').sum())}/{len(sample)} filled; "
          f"{int(sample.human_verdict.astype(str).str.lower().str.strip().eq('correct').sum())} marked correct, "
          f"{int(sample.human_verdict.astype(str).str.lower().str.strip().eq('wrong').sum())} marked wrong.", ""]
    for p in node_p[:20] + edge_p[:20]:
        L.append(f"- PROBLEM: {p}")
    (CHECK_DIR / "check_report.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
