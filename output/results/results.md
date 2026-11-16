# Task 1 query results

## Q1. Which gearbox measurements are available for Kelmarsh 6 on an alarm day (2021-02-05)?

4 signals linked to component:gearbox via MEASURES_ON (manual starter table); 576 of 576 ten-minute values present, 0 missing (NaN in SCADA).

Saved: `output/results/q1_gearbox_kelmarsh6_2021-02-05.csv` (576 rows)

| turbine    | time                | signal                  |   value | unit   | component   | source_file                                             |   source_line |
|:-----------|:--------------------|:------------------------|--------:|:-------|:------------|:--------------------------------------------------------|--------------:|
| Kelmarsh 6 | 2021-02-05 00:00:00 | Gear oil inlet pressure | 86.806  | bar    | gearbox     | Turbine_Data_Kelmarsh_6_2021-01-01_-_2022-01-01_233.csv |          5051 |
| Kelmarsh 6 | 2021-02-05 00:10:00 | Gear oil inlet pressure | 86.2014 | bar    | gearbox     | Turbine_Data_Kelmarsh_6_2021-01-01_-_2022-01-01_233.csv |          5052 |
| Kelmarsh 6 | 2021-02-05 00:20:00 | Gear oil inlet pressure | 84.7301 | bar    | gearbox     | Turbine_Data_Kelmarsh_6_2021-01-01_-_2022-01-01_233.csv |          5053 |
| Kelmarsh 6 | 2021-02-05 00:30:00 | Gear oil inlet pressure | 85.2918 | bar    | gearbox     | Turbine_Data_Kelmarsh_6_2021-01-01_-_2022-01-01_233.csv |          5054 |
| Kelmarsh 6 | 2021-02-05 00:40:00 | Gear oil inlet pressure | 86.1143 | bar    | gearbox     | Turbine_Data_Kelmarsh_6_2021-01-01_-_2022-01-01_233.csv |          5055 |
| Kelmarsh 6 | 2021-02-05 00:50:00 | Gear oil inlet pressure | 86.574  | bar    | gearbox     | Turbine_Data_Kelmarsh_6_2021-01-01_-_2022-01-01_233.csv |          5056 |
| Kelmarsh 6 | 2021-02-05 01:00:00 | Gear oil inlet pressure | 86.8368 | bar    | gearbox     | Turbine_Data_Kelmarsh_6_2021-01-01_-_2022-01-01_233.csv |          5057 |
| Kelmarsh 6 | 2021-02-05 01:10:00 | Gear oil inlet pressure | 86.865  | bar    | gearbox     | Turbine_Data_Kelmarsh_6_2021-01-01_-_2022-01-01_233.csv |          5058 |
| Kelmarsh 6 | 2021-02-05 01:20:00 | Gear oil inlet pressure | 88.4779 | bar    | gearbox     | Turbine_Data_Kelmarsh_6_2021-01-01_-_2022-01-01_233.csv |          5059 |
| Kelmarsh 6 | 2021-02-05 01:30:00 | Gear oil inlet pressure | 86.7173 | bar    | gearbox     | Turbine_Data_Kelmarsh_6_2021-01-01_-_2022-01-01_233.csv |          5060 |
| Kelmarsh 6 | 2021-02-05 01:40:00 | Gear oil inlet pressure | 88.5298 | bar    | gearbox     | Turbine_Data_Kelmarsh_6_2021-01-01_-_2022-01-01_233.csv |          5061 |
| Kelmarsh 6 | 2021-02-05 01:50:00 | Gear oil inlet pressure | 87.8311 | bar    | gearbox     | Turbine_Data_Kelmarsh_6_2021-01-01_-_2022-01-01_233.csv |          5062 |

## Q2. When did the turbines report alarm code 1050?

Events per turbine: {'Kelmarsh 6': 10}. No events for: ['Kelmarsh 1'].

Saved: `output/results/q2_code1050.csv` (10 rows)

| turbine    | event_id              | status   | start               | end                 | duration   |   code | message                 | source_file                                       |   source_line |
|:-----------|:----------------------|:---------|:--------------------|:--------------------|:-----------|-------:|:------------------------|:--------------------------------------------------|--------------:|
| Kelmarsh 6 | event:Kelmarsh_6:L842 | Warning  | 2021-02-05 08:33:07 | 2021-02-05 08:33:09 | 00:00:02   |   1050 | Drivetrain oscillations | Status_Kelmarsh_6_2021-01-01_-_2022-01-01_233.csv |           842 |
| Kelmarsh 6 | event:Kelmarsh_6:L844 | Warning  | 2021-02-05 08:33:14 | 2021-02-05 08:33:16 | 00:00:02   |   1050 | Drivetrain oscillations | Status_Kelmarsh_6_2021-01-01_-_2022-01-01_233.csv |           844 |
| Kelmarsh 6 | event:Kelmarsh_6:L846 | Warning  | 2021-02-05 08:33:16 | 2021-02-05 08:33:18 | 00:00:02   |   1050 | Drivetrain oscillations | Status_Kelmarsh_6_2021-01-01_-_2022-01-01_233.csv |           846 |
| Kelmarsh 6 | event:Kelmarsh_6:L848 | Warning  | 2021-02-05 08:33:34 | 2021-02-05 08:33:36 | 00:00:02   |   1050 | Drivetrain oscillations | Status_Kelmarsh_6_2021-01-01_-_2022-01-01_233.csv |           848 |
| Kelmarsh 6 | event:Kelmarsh_6:L850 | Warning  | 2021-02-05 08:33:41 | 2021-02-05 08:33:43 | 00:00:02   |   1050 | Drivetrain oscillations | Status_Kelmarsh_6_2021-01-01_-_2022-01-01_233.csv |           850 |
| Kelmarsh 6 | event:Kelmarsh_6:L852 | Warning  | 2021-02-05 08:33:44 | 2021-02-05 08:33:46 | 00:00:02   |   1050 | Drivetrain oscillations | Status_Kelmarsh_6_2021-01-01_-_2022-01-01_233.csv |           852 |
| Kelmarsh 6 | event:Kelmarsh_6:L855 | Warning  | 2021-02-05 08:33:55 | 2021-02-05 08:33:57 | 00:00:02   |   1050 | Drivetrain oscillations | Status_Kelmarsh_6_2021-01-01_-_2022-01-01_233.csv |           855 |
| Kelmarsh 6 | event:Kelmarsh_6:L863 | Warning  | 2021-02-05 08:40:36 | 2021-02-05 08:40:38 | 00:00:02   |   1050 | Drivetrain oscillations | Status_Kelmarsh_6_2021-01-01_-_2022-01-01_233.csv |           863 |
| Kelmarsh 6 | event:Kelmarsh_6:L872 | Warning  | 2021-02-05 08:46:14 | 2021-02-05 08:46:16 | 00:00:02   |   1050 | Drivetrain oscillations | Status_Kelmarsh_6_2021-01-01_-_2022-01-01_233.csv |           872 |
| Kelmarsh 6 | event:Kelmarsh_6:L873 | Warning  | 2021-02-05 08:46:16 | 2021-02-08 13:43:43 | 76:57:27   |   1050 | Drivetrain oscillations | Status_Kelmarsh_6_2021-01-01_-_2022-01-01_233.csv |           873 |

## Q2 (second example). When did the turbines report alarm code 1700?

Events per turbine: {'Kelmarsh 6': 3}. No events for: ['Kelmarsh 1'].

Saved: `output/results/q2_code1700.csv` (3 rows)

| turbine    | event_id                | status   | start               | end                 | duration   |   code | message                   | source_file                                       |   source_line |
|:-----------|:------------------------|:---------|:--------------------|:--------------------|:-----------|-------:|:--------------------------|:--------------------------------------------------|--------------:|
| Kelmarsh 6 | event:Kelmarsh_6:L593   | Warning  | 2021-01-21 08:08:49 | 2021-01-21 08:39:04 | 00:30:15   |   1700 | High temp. gear bearing 1 | Status_Kelmarsh_6_2021-01-01_-_2022-01-01_233.csv |           593 |
| Kelmarsh 6 | event:Kelmarsh_6:L1661  | Warning  | 2021-03-27 05:18:50 | 2021-03-27 06:27:02 | 01:08:12   |   1700 | High temp. gear bearing 1 | Status_Kelmarsh_6_2021-01-01_-_2022-01-01_233.csv |          1661 |
| Kelmarsh 6 | event:Kelmarsh_6:L13351 | Warning  | 2021-12-03 06:21:34 | 2021-12-03 06:42:18 | 00:20:44   |   1700 | High temp. gear bearing 1 | Status_Kelmarsh_6_2021-01-01_-_2022-01-01_233.csv |         13351 |

## Q3. What did the sensors record near the Kelmarsh 6 alarm at 2021-02-05 08:33:07?

Event event:Kelmarsh_6:L842 (Warning, 1050 'Drivetrain oscillations', status line 842). Window 2021-02-05 07:33:07 to 2021-02-05 09:03:07; 9 SCADA timestamps x 13 signals. Timestamps are the Greenbyte 10-minute stamps as exported; this is a time association only, not a cause.

Saved: `output/results/q3_kelmarsh6_2021-02-05_0833.csv` (9 rows)

| time                |   scada_source_line |   Drive train acceleration (mm/ss) |   Gear oil inlet pressure (bar) |   Gear oil inlet temperature (°C) |   Gear oil temperature (°C) |   Gearbox speed (RPM) |   Generator RPM (RPM) |   Generator bearing front temperature (°C) |   Generator bearing rear temperature (°C) |   Power (kW) |   Rotor bearing temp (°C) |   Rotor speed (RPM) |   Tower Acceleration X (mm/ss) |   Wind speed (m/s) |
|:--------------------|--------------------:|-----------------------------------:|--------------------------------:|----------------------------------:|----------------------------:|----------------------:|----------------------:|-------------------------------------------:|------------------------------------------:|-------------:|--------------------------:|--------------------:|-------------------------------:|-------------------:|
| 2021-02-05 07:40:00 |                5097 |                            3.13887 |                        91.9594  |                           53.1237 |                     54.0026 |            1071.45    |           1068.12     |                                    37.5263 |                                   39.5711 |    115.35    |                   26.3842 |            8.99835  |                       36.6441  |            4.08764 |
| 2021-02-05 07:50:00 |                5098 |                            3.16499 |                        91.5895  |                           53.185  |                     54.015  |            1071.46    |           1068.69     |                                    38.5375 |                                   39.8375 |    119.16    |                   26.395  |            8.99875  |                       45.357   |            4.09645 |
| 2021-02-05 08:00:00 |                5099 |                            3.21806 |                        91.2799  |                           53.18   |                     53.885  |            1072.6     |           1069.61     |                                    39.495  |                                   40.0875 |     26.5156  |                   26.4    |            9.00654  |                       45.4532  |            2.91025 |
| 2021-02-05 08:10:00 |                5100 |                            3.96108 |                        91.7478  |                           53.01   |                     53.725  |            1073.42    |           1070.85     |                                    40.435  |                                   40.5425 |     31.2723  |                   26.395  |            9.02037  |                       45.1618  |            3.04299 |
| 2021-02-05 08:20:00 |                5101 |                            5.95124 |                        80.2734  |                           52.39   |                     53.465  |             812.774   |            809.452    |                                    41.37   |                                   41.15   |     45.2989  |                   26.385  |            6.83709  |                       40.4423  |            3.65248 |
| 2021-02-05 08:30:00 |                5102 |                            6.24254 |                        58.683   |                           50.8675 |                     52.4825 |             333.134   |            331.49     |                                    42.26   |                                   41.8075 |      4.30959 |                   26.17   |            2.77575  |                       30.3154  |            3.5667  |
| 2021-02-05 08:40:00 |                5103 |                            6.29403 |                        57.1569  |                           50.2875 |                     51.795  |             272.406   |            269.438    |                                    42.565  |                                   41.47   |     18.963   |                   25.9325 |            2.2893   |                       24.2438  |            3.87909 |
| 2021-02-05 08:50:00 |                5104 |                            5.57238 |                        10.636   |                           46.7875 |                     50.125  |               6.47357 |              3.14826  |                                    42.7    |                                   41.2875 |     -1.18917 |                   25.6    |            0.014916 |                        6.00988 |            3.43894 |
| 2021-02-05 09:00:00 |                5105 |                            3.62396 |                         2.11994 |                           44.3375 |                     48.365  |               4.64849 |              0.976589 |                                    42.7    |                                   41.015  |     -1.09581 |                   25.18   |            0        |                        4.08114 |            3.01457 |
