# Task 1 graph check report

Graph built at 2026-11-16T10:56:56+00:00 from `D:\Antigravity\项目优化\kelmarsh_kg\raw_data\Kelmarsh_SCADA_2021_4456`.

## Statistics

- Nodes: 414,506; edges: 828,863
- Nodes by type: {'Turbine': 2, 'Signal': 13, 'Component': 7, 'EventCode': 58, 'Event': 547, 'Observation': 413879}
- Edges by type: {'HAS_EVENT': 547, 'HAS_OBSERVATION': 413879, 'MEASURES_ON': 11, 'HAS_CODE': 547, 'OF_SIGNAL': 413879}
- Alarm days loaded (Stop/Warning start in 2021): {'Kelmarsh_1': 109, 'Kelmarsh_6': 118}

| Turbine | Status | Events |
|---|---|---|
| Kelmarsh 1 | Stop | 132 |
| Kelmarsh 1 | Warning | 179 |
| Kelmarsh 6 | Stop | 117 |
| Kelmarsh 6 | Warning | 119 |

| Signal | Observations | Missing (NaN) slots |
|---|---|---|
| signal:drive_train_acceleration | 32,205 | 483 |
| signal:gear_oil_inlet_pressure | 32,222 | 466 |
| signal:gear_oil_inlet_temperature | 30,975 | 1,713 |
| signal:gear_oil_temperature | 30,975 | 1,713 |
| signal:gearbox_speed | 30,975 | 1,713 |
| signal:generator_bearing_front_temperature | 32,222 | 466 |
| signal:generator_bearing_rear_temperature | 32,222 | 466 |
| signal:generator_rpm | 32,222 | 466 |
| signal:power | 32,222 | 466 |
| signal:rotor_bearing_temperature | 32,222 | 466 |
| signal:rotor_speed | 32,222 | 466 |
| signal:tower_acceleration_x | 30,975 | 1,713 |
| signal:wind_speed | 32,220 | 468 |

## Integrity checks

- Unique ids: guaranteed by graph keys; conflicting re-inserts of an existing id: 0 (includes code-message conflicts)
- Node problems (id prefix / required properties / provenance): 0
- Edge problems (allowed types / existing endpoints / provenance): 0
- Edges rejected during build: 0
- Cardinality violations: none
- Exact duplicate Stop/Warning rows skipped: 0
- Identical repeated inserts absorbed: {'nodes': 493, 'edges': 0}
- Records outside the schema scope (not imported):
  - Status_Kelmarsh_1_2021-01-01_-_2022-01-01_228.csv: status 'Informational' outside scope (9671 rows)
  - Status_Kelmarsh_1_2021-01-01_-_2022-01-01_228.csv: status 'Communication' outside scope (15 rows)
  - Status_Kelmarsh_6_2021-01-01_-_2022-01-01_233.csv: status 'Communication' outside scope (17 rows)
  - Status_Kelmarsh_6_2021-01-01_-_2022-01-01_233.csv: status 'Informational' outside scope (13780 rows)

## Repeated import

```
{
  "rebuild_identical_nodes": true,
  "rebuild_identical_edges": true,
  "rebuild_nodes_with_different_properties": 0,
  "rebuild_edges_with_different_properties": 0,
  "nodes_after_reimport": [
    414506,
    414506
  ],
  "edges_after_reimport": [
    828863,
    828863
  ],
  "conflicts_after_reimport": 0
}
```

## Fact sample against sources

50 facts (seed 42, stratified by relationship) were re-read from the cited source line: 50/50 match automatically.

Manual check by a person (`human_verdict` in `fact_verification_sample.csv`): 50/50 filled; 50 marked correct, 0 marked wrong.
