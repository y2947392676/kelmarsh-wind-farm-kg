"""Figures for the Task 1 report (black and white). Run after build.py and queries.py.

Usage:  python make_figures.py   -> figures/schema.png, figures/q3_window.png
"""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import FancyBboxPatch

from kg_common import OUT_DIR, ROOT

FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)
summary = json.loads((OUT_DIR / "build_summary.json").read_text(encoding="utf-8"))
NB, EB = summary["nodes_by_type"], summary["edges_by_type"]

# ---------------------------------------------------------------- schema
boxes = {  # name: (x, y, property line)
    "Turbine": (0.5, 0.8, "name, model"),
    "Event": (0.18, 0.47, "start, end, status"),
    "EventCode": (0.18, 0.12, "code, message"),
    "Observation": (0.82, 0.47, "time, value"),
    "Signal": (0.82, 0.12, "name, unit"),
    "Component": (0.5, -0.16, "name"),
}
edges = [("Turbine", "Event", "HAS_EVENT"), ("Event", "EventCode", "HAS_CODE"),
         ("Turbine", "Observation", "HAS_OBSERVATION"), ("Observation", "Signal", "OF_SIGNAL"),
         ("Signal", "Component", "MEASURES_ON")]
fig, ax = plt.subplots(figsize=(8, 5.6))
ax.set_xlim(-0.05, 1.05); ax.set_ylim(-0.3, 0.95); ax.axis("off")
W, H = 0.31, 0.13
for n, (x, y, props) in boxes.items():
    ax.add_patch(FancyBboxPatch((x - W / 2, y - H / 2), W, H, boxstyle="round,pad=0.01",
                                fc="white", ec="black", lw=1.2))
    ax.text(x, y + 0.025, f"{n}  ({NB.get(n, 0):,})", ha="center", va="center", fontsize=10.5, weight="bold")
    ax.text(x, y - 0.03, props, ha="center", va="center", fontsize=9)
for a, b, rel in edges:
    (x1, y1, _), (x2, y2, _) = boxes[a], boxes[b]
    dy = H / 2 + 0.012
    sy, ey = (y1 - dy, y2 + dy) if y1 > y2 else (y1, y2)
    if a == "Signal":
        sx, sy, ex, ey = x1, y1 - H / 2 - 0.01, x2 + W / 2 + 0.01, y2
        style = "--"
    else:
        sx, ex, style = x1 + (x2 - x1) * 0.15, x2, "-"
    ax.annotate("", xy=(ex, ey), xytext=(sx, sy),
                arrowprops=dict(arrowstyle="-|>", color="black", lw=1.2, linestyle=style))
    ax.text((sx + ex) / 2 + 0.02, (sy + ey) / 2, f"{rel}\n({EB.get(rel, 0):,})", fontsize=8.5,
            ha="left", va="center", bbox=dict(fc="white", ec="none", pad=1))
ax.text(0.5, -0.29, "Solid: from CSV fields.  Dashed: manual starter table (evidence=manual).  "
        "Counts from output/build_summary.json.", ha="center", fontsize=8.5)
fig.tight_layout()
fig.savefig(FIG / "schema.png", dpi=200)
plt.close(fig)

# ---------------------------------------------------------------- Q3 window
q3 = pd.read_csv(OUT_DIR / "results" / "q3_kelmarsh6_2021-02-05_0833.csv", encoding="utf-8-sig")
q2 = pd.read_csv(OUT_DIR / "results" / "q2_code1050.csv", encoding="utf-8-sig")
t = pd.to_datetime(q3["time"])
cols = [c for c in q3.columns if c.startswith("Drive train acceleration")] + \
       [c for c in q3.columns if c.startswith("Power")] + \
       [c for c in q3.columns if c.startswith("Rotor speed")]
fig, axes = plt.subplots(len(cols), 1, figsize=(8, 5.5), sharex=True)
starts = pd.to_datetime(q2["start"])
for ax, c in zip(axes, cols):
    ax.plot(t, q3[c], color="black", marker="o", ms=3, lw=1.2)
    ax.axvspan(starts.min(), starts.max(), color="0.85", lw=0)
    ax.set_ylabel(c.replace(" (", "\n("), fontsize=8.5)
    ax.grid(alpha=0.3)
axes[0].set_title("Kelmarsh 6, 2021-02-05: SCADA 10-minute values around the code 1050 warnings\n"
                  "(grey = start times of the 10 warnings, 08:33:07-08:46:16; SCADA lines "
                  f"{q3.scada_source_line.min()}-{q3.scada_source_line.max()})", fontsize=9.5)
axes[-1].xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%H:%M"))
fig.tight_layout()
fig.savefig(FIG / "q3_window.png", dpi=200)
plt.close(fig)
# ---------------------------------------------------------------- query paths (Q1-Q3)
def draw_path(fname, boxes, arrows, start, notes):
    """boxes: list of (node type, [id lines], count line); arrows: (from, to, relationship),
    drawn in the stored edge direction; start: index of the box where the query starts."""
    n = len(boxes)
    fig, ax = plt.subplots(figsize=(8.0, 2.4))
    ax.set_xlim(0, n); ax.set_ylim(-0.62, 1.12); ax.axis("off")
    w, h = 0.70, 0.86
    for i, (ntype, ids, count) in enumerate(boxes):
        lw = 2.4 if i == start else 1.1
        ax.add_patch(FancyBboxPatch((i + (1 - w) / 2, 0.05), w, h, boxstyle="round,pad=0.02",
                                    fc="white", ec="black", lw=lw))
        ax.text(i + 0.5, 0.80, ntype, ha="center", va="center", fontsize=10, weight="bold")
        ax.text(i + 0.5, 0.50, "\n".join(ids), ha="center", va="center", fontsize=7.1,
                family="monospace", linespacing=1.25)
        ax.text(i + 0.5, 0.15, count, ha="center", va="center", fontsize=8, style="italic")
        if i == start:
            ax.text(i + 0.5, 1.03, "query starts here", ha="center", va="bottom", fontsize=8.5, weight="bold")
    for a, b, rel in arrows:
        left, right = min(a, b), max(a, b)
        x1, x2 = left + 0.5 + w / 2 + 0.02, right + 0.5 - w / 2 - 0.02
        xs, xe = (x1, x2) if a < b else (x2, x1)
        ax.annotate("", xy=(xe, 0.48), xytext=(xs, 0.48),
                    arrowprops=dict(arrowstyle="-|>", color="black", lw=1.2))
        ax.text((x1 + x2) / 2, 0.56, rel.replace("_", "_\n", 1), ha="center", va="bottom",
                fontsize=6.6, linespacing=1.1)
    for k, line in enumerate(notes):
        ax.text(0.02, -0.18 - 0.2 * k, line, ha="left", va="center", fontsize=8.5)
    fig.tight_layout()
    fig.savefig(FIG / fname, dpi=200)
    plt.close(fig)


q1 = pd.read_csv(OUT_DIR / "results" / "q1_gearbox_kelmarsh6_2021-02-05.csv", encoding="utf-8-sig")
draw_path("q1_path.png",
          [("Turbine", ["turbine:Kelmarsh_6"], "1 turbine"),
           ("Observation", ["obs:Kelmarsh_6:", "2021-02-05T00:00:00:", "gearbox_speed"],
            f"{len(q1)} on 2021-02-05"),
           ("Signal", ["signal:gearbox_speed"], f"{q1.signal.nunique()} gearbox signals"),
           ("Component", ["component:gearbox"], "1 component")],
          [(0, 1, "HAS_OBSERVATION"), (1, 2, "OF_SIGNAL"), (2, 3, "MEASURES_ON")], start=3,
          notes=["Arrows show the stored edge direction; the query walks from right to left.",
                 "Filter: only observations of turbine:Kelmarsh_6 with a time on 2021-02-05."])

draw_path("q2_path.png",
          [("Turbine", ["turbine:Kelmarsh_6"], f"{q2.turbine.nunique()} turbine with this code"),
           ("Event", [q2.event_id.iloc[0], "...", q2.event_id.iloc[-1]], f"{len(q2)} Warning events"),
           ("EventCode", ["code:1050", "Drivetrain oscillations"], "1 code node")],
          [(0, 1, "HAS_EVENT"), (1, 2, "HAS_CODE")], start=2,
          notes=["Arrows show the stored edge direction; the query walks from right to left.",
                 "turbine:Kelmarsh_1 has no event linked to code:1050."])

draw_path("q3_path.png",
          [("Event", ["event:Kelmarsh_6:L842", "start 08:33:07"], "the alarm"),
           ("Turbine", ["turbine:Kelmarsh_6"], "1 turbine"),
           ("Observation", ["obs:Kelmarsh_6:", "2021-02-05T08:30:00:", "drive_train_", "acceleration"],
            f"{len(q3)} times x {len(q3.columns) - 2} signals"),
           ("Signal", ["signal:", "drive_train_", "acceleration"], f"{len(q3.columns) - 2} signals")],
          [(1, 0, "HAS_EVENT"), (1, 2, "HAS_OBSERVATION"), (2, 3, "OF_SIGNAL")], start=1,
          notes=["Step 1: from the turbine, read the alarm start time of the event (08:33:07).",
                 "Step 2: from the same turbine, take the observations from 07:33:07 to 09:03:07 and their signals."])

print("saved", FIG / "schema.png", FIG / "q3_window.png", "q1_path.png", "q2_path.png", "q3_path.png")
