"""Task 1 queries Q1-Q3 over the saved graph.

Usage:  python queries.py                    (runs the planned examples)
        python queries.py q2 --code 1700     (single query with other parameters)
Output: output/results/q*.csv and output/results/results.md
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta

import pandas as pd

from kg_common import OUT_DIR, load_graph, turbine_id

RES_DIR = OUT_DIR / "results"
FMT = "%Y-%m-%d %H:%M:%S"


def _events(G, tid):
    return [v for _, v, k in G.out_edges(tid, keys=True) if k == "HAS_EVENT"]


def _obs(G, tid):
    return (v for _, v, k in G.out_edges(tid, keys=True) if k == "HAS_OBSERVATION")


def _signal(G, oid):
    return next(v for _, v, k in G.out_edges(oid, keys=True) if k == "OF_SIGNAL")


_LOADED = {}


def loaded_days(G, tid):
    """Days for which SCADA rows of this turbine were imported (alarm days that start in 2021).
    Distinguishes 'not loaded' from 'loaded but NaN in SCADA'."""
    if tid not in _LOADED:
        _LOADED[tid] = {G.nodes[o]["time"][:10] for o in _obs(G, tid)}
    return _LOADED[tid]


def q1(G, turbine=6, day="2021-02-05", component="gearbox"):
    """Which <component> measurements are available for a turbine on an alarm day?
    Path: Component <-MEASURES_ON- Signal <-OF_SIGNAL- Observation <-HAS_OBSERVATION- Turbine."""
    tid, cid = turbine_id(turbine), f"component:{component}"
    if tid not in G or cid not in G:
        return pd.DataFrame(), f"Unknown turbine {tid} or component {cid}."
    signals = {u for u, _, k in G.in_edges(cid, keys=True) if k == "MEASURES_ON"}
    if not signals:
        return pd.DataFrame(), f"No selected signal is linked to {cid}; no measurements to return."
    if day not in loaded_days(G, tid):
        return pd.DataFrame(), (f"{day} was not loaded for {tid}: only days on which a Stop/Warning "
                                "event starts in 2021 are imported. This is not a missing value in SCADA.")
    rows = []
    for oid in _obs(G, tid):
        o = G.nodes[oid]
        if o["time"].startswith(day):
            sid = _signal(G, oid)
            if sid in signals:
                s = G.nodes[sid]
                rows.append({"turbine": G.nodes[tid]["name"], "time": o["time"], "signal": s["name"],
                             "value": o["value"], "unit": s["unit"], "component": component,
                             "source_file": o["source_file"], "source_line": o["source_line"]})
    df = pd.DataFrame(rows).sort_values(["signal", "time"]) if rows else pd.DataFrame()
    expected = 144 * len(signals)
    note = (f"{len(signals)} signals linked to {cid} via MEASURES_ON (manual starter table); "
            f"{len(df)} of {expected} ten-minute values present, {expected - len(df)} missing (NaN in SCADA).")
    return df, note


def q2(G, code=1050):
    """When did each turbine report alarm code <code>?  Path: Turbine -HAS_EVENT-> Event -HAS_CODE-> EventCode."""
    cid = f"code:{code}"
    if cid not in G:
        return pd.DataFrame(), f"{cid} does not occur in the selected Stop/Warning records."
    rows = []
    for eid, _, k in G.in_edges(cid, keys=True):
        if k != "HAS_CODE":
            continue
        tid = next(u for u, _, kk in G.in_edges(eid, keys=True) if kk == "HAS_EVENT")
        e = G.nodes[eid]
        rows.append({"turbine": G.nodes[tid]["name"], "event_id": eid, "status": e["status"],
                     "start": e["start"], "end": e["end"], "duration": e["duration"],
                     "code": code, "message": G.nodes[cid]["message"],
                     "source_file": e["source_file"], "source_line": e["source_line"]})
    df = pd.DataFrame(rows).sort_values(["turbine", "start"])
    counts = df.groupby("turbine").size().to_dict()
    missing = [G.nodes[t]["name"] for t in G if G.nodes[t]["type"] == "Turbine"
               and G.nodes[t]["name"] not in counts]
    note = f"Events per turbine: {counts}." + (f" No events for: {missing}." if missing else "")
    return df, note


def q3(G, turbine=6, event_start="2021-02-05 08:33:07", before_min=60, after_min=30):
    """What did the sensors record near a selected alarm?
    Path: Turbine -HAS_EVENT-> Event (time) ; Turbine -HAS_OBSERVATION-> Observation -OF_SIGNAL-> Signal."""
    tid = turbine_id(turbine)
    ev = [e for e in _events(G, tid) if G.nodes[e]["start"] == event_start]
    if not ev:
        return pd.DataFrame(), f"No Stop/Warning event of {tid} starts at {event_start}."
    t0 = datetime.strptime(event_start, FMT)
    lo, hi = (t0 - timedelta(minutes=before_min)).strftime(FMT), (t0 + timedelta(minutes=after_min)).strftime(FMT)
    window_days = sorted({lo[:10], hi[:10]})
    not_loaded = [d for d in window_days if d not in loaded_days(G, tid)]
    rows = []
    for oid in _obs(G, tid):
        o = G.nodes[oid]
        if lo <= o["time"] <= hi:
            s = G.nodes[_signal(G, oid)]
            rows.append({"time": o["time"], "signal": f"{s['name']} ({s['unit']})", "value": o["value"],
                         "source_line": o["source_line"]})
    if not rows:
        why = (f"day(s) {not_loaded} not loaded (only alarm days starting in 2021 are imported)"
               if not_loaded else "all values in the window are NaN in SCADA")
        return pd.DataFrame(), f"No observations of {tid} between {lo} and {hi}: {why}."
    long = pd.DataFrame(rows)
    wide = long.pivot(index="time", columns="signal", values="value").sort_index()
    lines = long.groupby("time").source_line.first()
    wide.insert(0, "scada_source_line", lines)
    e = G.nodes[ev[0]]
    code = next(v for _, v, k in G.out_edges(ev[0], keys=True) if k == "HAS_CODE")
    note = (f"Event {ev[0]} ({e['status']}, {G.nodes[code]['code']} '{G.nodes[code]['message']}', "
            f"status line {e['source_line']}). Window {lo} to {hi}; {len(wide)} SCADA timestamps x "
            f"{wide.shape[1] - 1} signals. Timestamps are the Greenbyte 10-minute stamps as exported; "
            "this is a time association only, not a cause."
            + (f" Part of the window falls on day(s) not loaded: {not_loaded}." if not_loaded else ""))
    return wide.reset_index(), note


def run_all(G):
    RES_DIR.mkdir(parents=True, exist_ok=True)
    md = ["# Task 1 query results", ""]
    for name, fn, kwargs, title in [
        ("q1_gearbox_kelmarsh6_2021-02-05", q1, {}, "Q1. Which gearbox measurements are available for Kelmarsh 6 on an alarm day (2021-02-05)?"),
        ("q2_code1050", q2, {}, "Q2. When did the turbines report alarm code 1050?"),
        ("q2_code1700", q2, {"code": 1700}, "Q2 (second example). When did the turbines report alarm code 1700?"),
        ("q3_kelmarsh6_2021-02-05_0833", q3, {}, "Q3. What did the sensors record near the Kelmarsh 6 alarm at 2021-02-05 08:33:07?"),
    ]:
        df, note = fn(G, **kwargs)
        df.to_csv(RES_DIR / f"{name}.csv", index=False, encoding="utf-8-sig")
        md += [f"## {title}", "", note, "", f"Saved: `output/results/{name}.csv` ({len(df)} rows)", ""]
        if len(df):
            md += [df.head(12).to_markdown(index=False), ""]
    (RES_DIR / "results.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("query", nargs="?", choices=["q1", "q2", "q3"])
    ap.add_argument("--turbine", type=int, default=6)
    ap.add_argument("--day", default="2021-02-05")
    ap.add_argument("--component", default="gearbox")
    ap.add_argument("--code", type=int, default=1050)
    ap.add_argument("--event-start", default="2021-02-05 08:33:07")
    a = ap.parse_args()
    G = load_graph()
    if a.query is None:
        run_all(G)
    else:
        df, note = {"q1": lambda: q1(G, a.turbine, a.day, a.component),
                    "q2": lambda: q2(G, a.code),
                    "q3": lambda: q3(G, a.turbine, a.event_start)}[a.query]()
        print(note)
        print(df.to_string(index=False))
