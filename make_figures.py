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
print("saved", FIG / "schema.png", FIG / "q3_window.png")
