# Kelmarsh Wind Farm Knowledge Graph — Task 1 (initial graph from structured data)

Author: Wu Haoyang. Course: Knowledge Engineering and Knowledge Management.

The graph connects 2021 Stop/Warning alarms, their codes and the 10-minute SCADA readings of
two turbines (Kelmarsh 1 and Kelmarsh 6), so that a maintenance analyst can ask which
measurements were recorded around an alarm and on which part of the turbine they were taken.

| What | Where |
|---|---|
| Task 1 report (English / Chinese / side by side) | `TASK1_REPORT.pdf`, `TASK1_REPORT_ZH.md`, `TASK1_REPORT_EN_ZH.pdf` |
| Code | `build.py`, `checks.py`, `queries.py` (+ `kg_common.py`) |
| Saved graph, checks, query results | `output/` |
| Web front end for this graph (pages, query forms, evidence panel) | separate repository [kelmarsh-kg-web](https://github.com/y2947392676/kelmarsh-kg-web) |

## Quick start (no raw data needed)

The saved graph export (`output/nodes.csv.gz`, `output/edges.csv.gz`) is in the repository, so the
queries run directly after cloning. On the first run the graph is rebuilt from the export
(about 10 s) and cached as `output/graph_task1.pkl`; the rebuilt graph is identical to the one
made by `build.py` (same nodes, edges and properties).

```bash
git clone https://github.com/y2947392676/kelmarsh-wind-farm-kg.git
cd kelmarsh-wind-farm-kg
pip install -r requirements.txt
python queries.py
```

On Windows, run these commands in PowerShell, cmd or the Anaconda Prompt.

**What works without the raw data**

| Task | Without raw data | With raw data (section 1) |
|---|---|---|
| `python queries.py` (Q1–Q3, also with other parameters) | yes | yes |
| Saved graph, checks and query results in `output/` | yes (already in the repository) | yes |
| Web front end ([kelmarsh-kg-web](https://github.com/y2947392676/kelmarsh-kg-web)) | yes, except the source-line panel | yes |
| `python build.py` (rebuild the graph from the source files) | no | yes |
| `python checks.py` (integrity checks, rebuild test, fact sample) | no | yes |
| Open a cited source line (e.g. Status file, line 842) | no | yes |

**If it does not run**

- `python` or `pip` is not found, or a module such as `pandas` is missing: the terminal is not using
  the Python that has the packages. Use the Anaconda Prompt, or call that Python directly, e.g.
  `D:\anaconda3\python.exe queries.py` and `D:\anaconda3\python.exe -m pip install -r requirements.txt`.
- `FileNotFoundError ... run python build.py first`: the folder `output/` with `nodes.csv.gz` and
  `edges.csv.gz` is missing; clone the repository again instead of copying single files.
- `build.py` or `checks.py` cannot find the Kelmarsh files: download the raw data (section 1).

## 1. Data and access

Kelmarsh wind farm data, v4 — Plumley, C., & Takeuchi, R. (2025), Zenodo,
https://doi.org/10.5281/zenodo.16807551, CC BY 4.0. The raw data are not stored in this repository.

1. Download `Kelmarsh_SCADA_2021_4456.zip` (467 MB; 1.2 GB unzipped, all six turbines) from
   https://zenodo.org/records/16807551 and unzip it to `raw_data/Kelmarsh_SCADA_2021_4456/`
   (the default location; not stored in git). Only the four files listed below (about 416 MB) are used.
2. Or point the scripts at another folder (set it in the same terminal before running the scripts):

```bash
$env:KELMARSH_DATA_DIR="C:\path\to\Kelmarsh_SCADA_2021_4456"   # Windows PowerShell
set KELMARSH_DATA_DIR=C:\path\to\Kelmarsh_SCADA_2021_4456      # Windows cmd
export KELMARSH_DATA_DIR=/path/to/Kelmarsh_SCADA_2021_4456     # macOS / Linux
```

Files used: `Turbine_Data_Kelmarsh_{1,6}_2021-01-01_-_2022-01-01_{228,233}.csv` and
`Status_Kelmarsh_{1,6}_2021-01-01_-_2022-01-01_{228,233}.csv`.
`data/manual_signal_component.csv` is the small hand-made starter table (13 rows) that links the
selected SCADA columns to components; every row states its justification.

## 2. Rebuild

```bash
pip install -r requirements.txt
python build.py     # ~20 s; writes output/graph_task1.pkl, nodes.csv.gz, edges.csv.gz, build_log/
python checks.py    # integrity checks, statistics, rebuild test, 50-fact source sample
python queries.py   # Q1-Q3, saved to output/results/
```

Single queries with other parameters:

```bash
python queries.py q1 --turbine 1 --day 2021-01-21 --component generator_bearing
python queries.py q2 --code 1700
python queries.py q3 --turbine 6 --event-start "2021-01-21 08:08:49"
```

## 3. Schema

| Node type | Stable id | Key properties | Source |
|---|---|---|---|
| Turbine | `turbine:Kelmarsh_6` | name, model, greenbyte_file_id | SCADA file header |
| Signal | `signal:drive_train_acceleration` | name, unit, scada_column | SCADA column header |
| Component | `component:gearbox` | name | manual starter table |
| EventCode | `code:1050` | code, message | Status file |
| Event | `event:Kelmarsh_6:L842` (file line) | start, end, duration, status | Status file |
| Observation | `obs:Kelmarsh_6:2021-02-05T08:30:00:drive_train_acceleration` | time, value | SCADA row |

| Relationship | From → To | Evidence |
|---|---|---|
| HAS_EVENT | Turbine → Event | Status row |
| HAS_CODE | Event → EventCode | Status row |
| HAS_OBSERVATION | Turbine → Observation | SCADA row |
| OF_SIGNAL | Observation → Signal | SCADA row + column |
| MEASURES_ON | Signal → Component | manual table (`evidence=manual`) |

Every node and edge stores `source_file` and `source_line` (1-based line in the original file).
`MEASURES_ON` means "the signal measures a quantity of that subsystem"; it does not claim where a
sensor is physically mounted.

**Node or property?**
- EventCode is a node because 547 events share 58 codes and the code's message is one fixed text per
  code; Task 2 will attach extracted components and conditions to the code once.
- Signal and Component are nodes because several observations share one signal, and several signals
  share one component (gearbox has four).
- Observation is a node because each value has its own time and source row.
- Units, timestamps, status, duration and values are properties because nothing else links to them.

**Ambiguous names.** "Generator bearing", "Rotor bearing" and the alarm text "gear bearing 1"
(code 1700) are separate entities; no Task 1 signal is linked to a gear bearing.

## 4. Scope and handling of data problems

- Events: only `Stop` and `Warning` rows (Informational and Communication rows are counted in
  `output/build_log/rejected_records.csv` and not imported). One event per turbine starts in 2020 (still open
  in 2021) and is kept with `starts_in_scope=False`.
- Observations: all 144 ten-minute rows of every day on which a Stop/Warning event starts in 2021
  (109 days for Kelmarsh 1, 118 for Kelmarsh 6), 13 channels.
- Missing values: NaN readings create no Observation and are listed in
  `build_log/missing_values.csv` (11,065 slots).
- Duplicates: exact duplicate Stop/Warning rows and duplicate SCADA timestamps are skipped and
  logged (none occurred in the selected scope).
- Repeated imports: ids are deterministic. Re-adding the same record is ignored; re-adding an id
  with different values is logged as a conflict.
- Invalid records: edges with missing endpoints or disallowed types are rejected and logged.

## 5. Results (from `output/`)

- Graph size: 414,506 nodes and 828,863 edges. Detailed statistics are in `output/checks/check_report.md`.
- Checks:
  - 0 node problems, 0 edge problems, 0 cardinality violations.
  - Rebuilding from the raw files gives an identical graph.
  - Re-importing the Status files changes nothing.
- Fact sample: 50 facts (seed 42) were re-read from the cited source lines, and all 50 match.
  - Manual check: the author opened each cited cell of the original CSV files in Excel next to
    `output/checks/fact_verification_sample.csv` and recorded a verdict in `human_verdict`:
    50 of 50 correct (see report, Figure 2).
  - `output/checks/manual_check_jump_list.csv` lists the cell to open for each fact.
  - Re-running `checks.py` keeps the verdicts.
- Saved graph for submission: `output/nodes.csv.gz` and `output/edges.csv.gz` (all properties,
  including provenance). The 88 MB `output/graph_task1.pkl` is rebuilt by `build.py` and is not in git.
- Queries:
  - Q1: gearbox signals of Kelmarsh 6 on 2021-02-05. Path: Turbine → Observation → Signal → Component.
  - Q2: events of code 1050. Path: Turbine → Event → EventCode. Kelmarsh 6 has 10 Warning events, starting
    08:33:07 to 08:46:16; Kelmarsh 1 has none.
  - Q3: all 13 channels from 60 min before to 30 min after the Kelmarsh 6 alarm at 2021-02-05 08:33:07.

## 6. Limitations

- Alarm and sensor readings are related in time only; the data contain no repairs or confirmed root
  causes, and all turbines share one model and owner.
- Greenbyte 10-minute timestamps are used as exported (UTC); the window in Q3 compares them
  directly with alarm start times.
- Signal ids are derived from SCADA column names. The signal-mapping CSV (manufacturer names,
  numeric ids) and the static turbine CSV (aliases such as KWF6 / SEN 93425) are not used in this build.
- Q1 depends on the manual starter table; automatic Signal→Component linking is Task 2.

## 7. Use of LLMs

| Tool | Model / version | Date | Role |
|---|---|---|---|
| Claude Code (Claude desktop app, Code tab) | Claude Opus 5.5 (`claude-opus-5-5`); app version not recorded | 2026-11-15, 2026-11-16 | Wrote `build.py`, `checks.py`, `queries.py`, `make_figures.py`, `make_pdf.py` and the manual table draft; drafted README and report |
| ChatGPT / Codex | model and version not recorded | 2026-11-16 | Reviewed the code and report against Task.pdf. Found the `requirements.txt` error, the Q1/Q3 "not loaded" bug and wording problems; these were then fixed |

**Settings.** Default tool settings. No temperature or other sampling parameter was set by the author.

**Example prompts** (actual prompts, translated from Chinese):

- "This is my data: `Kelmarsh_SCADA_2021_4456.zip`". The task was to build the Task 1 graph
  within the scope of the proposal.
- "Don't write the Task 2 parts yet; write the Task 1 material first."
- "Check the report and code against the five Task 1 requirements and list what is missing.
  Use the numbers in `output/` and do not change them." (review prompt drafted for ChatGPT;
  the exact text the author sent was not recorded)

**Checking model output.** Each step was checked as follows:

- Code ran on the raw files; `checks.py` must report 0 problems.
- Q2 and Q3 results were compared with the Status and SCADA lines cited in the proposal
  (lines 842 and 5102).
- 50 sampled facts were re-read from their source lines.

**What the models did not do.**

- No model created graph facts. The graph is rebuilt from the CSV files without any model
  call.
- The `human_verdict` column is filled in by the author, not by a model. The author made each
  verdict by opening the cited cell in the original CSV file.
