<div class="head"><p>彼得大帝圣彼得堡理工大学</p><p>课程《知识工程与知识管理》</p></div>

# 任务 1 报告：基于结构化记录的初始知识图谱

<p class="sub">项目：以报警为中心的 Kelmarsh 风电场知识图谱<br>学生：Wu Haoyang</p>

<!-- contents -->

## 1 数据与范围

任务 1 的目标是用结构化记录构建知识图谱的第一个版本。图谱把风机报警、报警代码和 10 分钟 SCADA 读数连接起来，使维护分析人员能够查询：某次报警前后记录了哪些测量值，这些测量值取自风机的哪个部件。

数据来源是 Kelmarsh 风电场数据集第 4 版 [1]。开题报告中确定的范围是：两台风机（Kelmarsh 1 和 Kelmarsh 6）、2021 年、Stop 和 Warning 两种事件状态，以及 303 个 SCADA 列中的 13 列。所用文件见表 1。

<p class="cap">表 1 – 数据文件</p>

| 文件 | 使用内容 |
|---|---|
| `Turbine_Data_Kelmarsh_1_…_228.csv`、`Turbine_Data_Kelmarsh_6_…_233.csv` | 303 列中的 13 列；报警日的 10 分钟数据行 |
| `Status_Kelmarsh_1_…_228.csv`、`Status_Kelmarsh_6_…_233.csv` | Stop（停机）和 Warning（警告）行 |
| `data/manual_signal_component.csv`（自建，13 行） | 信号 → 部件初始对应表，每行附一条依据 |

报警日是指 2021 年内有 Stop 或 Warning 事件开始的日子。Kelmarsh 1 有 109 个报警日，Kelmarsh 6 有 118 个。这些日子的全部 144 个 10 分钟数据行都被加载。

## 2 设计

### 2.1 图谱结构

图谱结构包含六类节点和五类关系（图 1）。风机有事件，每个事件有一个事件代码；风机也有测量值，每个测量值属于一个信号，信号测量某个部件的某个量。

![Schema](figures/schema.png)

<p class="cap">图 1 – 任务 1 图谱结构（括号内为节点数）</p>

### 2.2 稳定标识符

标识符只由原始数据中的值构成（表 2），因此再次构建会得到相同的标识符。每个节点和每条边还保存 `source_file`（来源文件）和 `source_line`（来源行号）。

<p class="cap">表 2 – 节点类型与标识符</p>

| 节点类型 | 标识符的构成 | 示例 |
|---|---|---|
| Turbine（风机） | 文件头中的风机名 | `turbine:Kelmarsh_6` |
| Event（事件） | 风机 + Status 文件中的行号 | `event:Kelmarsh_6:L842` |
| EventCode（事件代码） | 制造商代码 | `code:1050` |
| Observation（测量值） | 风机 + 时间戳 + 信号 | `obs:Kelmarsh_6:2021-02-05T08:30:00:drive_train_acceleration` |
| Signal（信号） | 规范化的 SCADA 列名 | `signal:drive_train_acceleration` |
| Component（部件） | 手工表中的名称 | `component:gearbox` |

### 2.3 节点与属性的划分

如果某项内容被其他内容引用或共享，就作为节点，否则作为属性。EventCode 是节点：547 个事件共用 58 个代码，在这些文件中每个代码恰好只有一条固定描述，这条描述只在代码节点上保存一次。Signal 和 Component 是节点，因为它们被共享：每个信号有数千个测量值，齿轮箱有四个信号（齿轮箱转速、齿轮油温度、齿轮油入口温度和齿轮油入口压力）。Observation 是节点，因为每个值都有自己的时间和自己的来源行，而且查询会从某个时间或某个部件出发，而不只是从风机出发。时间、数值、单位、状态和持续时间是属性，因为没有其他实体指向它们。

### 2.4 信号–部件关系与易混淆名称

MEASURES_ON 表示该信号测量的是这个子系统的某个量，并不说明传感器安装在哪里。这些关系来自手工初始表，并标记 `evidence=manual`。风速和功率两个信号没有对应部件。名称相近的部件作为不同实体保存：发电机轴承有两个温度信号，转子轴承有一个，报警代码 1700 中出现的齿轮轴承则没有任何所选信号测量它。

## 3 构建

### 3.1 构建过程

脚本 `build.py` 用 pandas [3] 读取原始 CSV 文件，约 20 秒构建出一个 NetworkX `MultiDiGraph`（有向多重图）[2]。Turbine、Signal、Component、Event 和 EventCode 节点通过专门的函数插入，这些函数在插入时检查标识符前缀以及每条边两端节点的类型。413,879 个测量值为了速度直接写入；它们的标识符和类型由构造方式固定，之后由 `checks.py` 与所有其他节点和边一起检查（第 4 节）。风机属性在 `property_source_lines` 中保存每个属性所在的文件头行号（名称：第 3 行；型号：第 4 行；时区：第 5 行）。

### 3.2 数据问题的处理

表 3 列出了任务要求中提到的每类问题的处理方式，以及本次构建中出现的次数。

<p class="cap">表 3 – 数据问题及其处理</p>

| 问题 | 处理方式 | 数量（本次构建） |
|---|---|---|
| 缺失值（SCADA 中的 `NaN`） | 不创建测量值；记录文件和行号 | 11,065 个 |
| 重复的 Stop/Warning 行 / 重复的 SCADA 时间戳 | 保留第一条，其余记入日志 | 0 / 0 |
| 同一记录被重复导入 | 标识符确定，忽略重复 | 493 次相同的重复插入 |
| 已有标识符出现冲突值（如一个代码两条描述） | 保留第一个，记录冲突 | 0 |
| 超出图谱结构的记录 | Informational 和 Communication 状态行不导入，只计数 | 23,451 + 32 行 |
| 端点缺失或类型错误的边 | 拒绝并记录 | 0 |
| 在 2021 年之前开始的事件 | 保留，`starts_in_scope = False` | 每台风机 1 个 |

493 次相同的重复插入中，489 次来自 EventCode 节点（547 个事件共用 58 个代码，547 − 58 = 489），其余 4 次来自被多个信号共用的 Component 节点（13 − 2 − 7 = 4）。

## 4 检查

### 4.1 图谱统计

脚本 `checks.py` 生成 `output/checks/check_report.md`。图谱规模见表 4，各风机的事件数见表 5。

<p class="cap">表 4 – 图谱统计</p>

| 项目 | 数量 |
|---|---|
| 节点 | 414,506 |
| 边 | 828,863 |
| Observation / HAS_OBSERVATION / OF_SIGNAL | 各 413,879 |
| Event / HAS_EVENT / HAS_CODE | 各 547 |
| EventCode | 58 |
| Signal / Component / MEASURES_ON | 13 / 7 / 11 |

<p class="cap">表 5 – 各风机的事件数</p>

| 风机 | Stop（停机） | Warning（警告） |
|---|---|---|
| Kelmarsh 1 | 132 | 179 |
| Kelmarsh 6 | 117 | 119 |

### 4.2 完整性检查

完整性检查的结果见表 6。

<p class="cap">表 6 – 完整性检查</p>

| 检查项 | 结果 |
|---|---|
| 标识符前缀与节点类型一致；必填属性齐全；来源信息齐全 | 0 个问题 |
| 每条边都连接已存在且类型允许的节点 | 0 个问题 |
| 每个测量值对应一台风机和一个信号；每个事件对应一台风机和一个代码 | 0 处违反 |
| 从原始文件重新构建，得到相同的节点、边及其全部属性 | 是（0 处差异） |
| 再次导入 Status 文件是否改变图谱 | 否（前后均为 414,506 / 828,863） |

### 4.3 对照原始数据核对事实

用随机种子 42 分层抽取 50 条事实：25 条测量值、10 条事件、10 条事件代码、5 条部件关系。对每条事实，重新打开所引用的来源行，并把所引用的字段与图谱进行比较。自动比较的结果是 50 条中 50 条一致。人工比较由作者逐条打开所引用的行，把结果记录在 `output/checks/fact_verification_sample.csv` 的 `human_verdict` 列。已填写和判为正确的数量显示在 `output/checks/check_report.md` 中。重新运行检查会保留这些判断。

## 5 查询

脚本 `queries.py` 运行计划中的问题，并把答案保存到 `output/results/`。

### 5.1 Q1. Kelmarsh 6 在一个报警日（2021-02-05）有哪些齿轮箱测量值？

该查询经过三种领域关系：Turbine → Observation → Signal → Component。结果为 4 个齿轮箱信号 × 144 个 10 分钟值 = 576 个值，无缺失。每个值都引用其 SCADA 行（5051–5194）。

### 5.2 Q2. 风机在什么时候报出过报警代码 1050？

查询路径为 Turbine → Event → EventCode。Kelmarsh 6 有 10 个 Warning 事件 “Drivetrain oscillations”（传动链振荡），开始时间在 2021-02-05 的 08:33:07 到 08:46:16 之间（Status 文件第 842–873 行）。Kelmarsh 1 没有此类事件。对代码 1700（“High temp. gear bearing 1”，齿轮轴承 1 温度高）做同样查询，得到 Kelmarsh 6 的 3 个 Warning 事件（第 593、1661 和 13351 行）。

### 5.3 Q3. 在 Kelmarsh 6 于 2021-02-05 08:33:07 的报警前后，传感器记录了什么？

该查询把 Turbine → Event（报警时间）与 Turbine → Observation → Signal 结合起来，时间窗为报警前 60 分钟到报警后 30 分钟。结果为 9 个时间点 × 13 个信号（SCADA 第 5097–5105 行）。传动链加速度从 08:00 的 3.22 mm/ss（第 5099 行）升到 08:30 的 6.24（第 5102 行）。转子转速从 08:10 的 9.0 RPM（第 5100 行）降到 08:50 的 0.01 RPM（第 5104 行）（图 2）。

![Q3 window](figures/q3_window.png)

<p class="cap">图 2 – 报警前后的传动链加速度与转子转速（Q3）</p>

### 5.4 局限

报警与传感器变化之间的联系只是时间上的关联；数据中没有维修记录，也没有已确认的根本原因。SCADA 时间戳是导出的 10 分钟时间戳（UTC），因此 08:33 的报警与时间戳为 08:30 和 08:40 的行进行比较。只加载 2021 年内开始的报警日；对其他任何日子，Q1 和 Q3 回答“未加载”（not loaded），而不是报告缺失值，这也包括每台风机那个在 2020 年开始的事件所在的日子。信号 → 部件关系只覆盖所选的 13 个信号，并且是手工建立的。信号标识符来自 SCADA 列名；数据集中的信号映射文件和风机静态文件（制造商信号名、KWF6 等风机别名）尚未纳入。两台风机型号相同（Senvion MM92），所有者也相同，因此比较制造商、型号或公司的问题无法用这些数据回答。

## 6 可复现性与大语言模型的使用

用以下命令重建图谱：

```bash
pip install -r requirements.txt
set KELMARSH_DATA_DIR=<解压 Kelmarsh_SCADA_2021_4456.zip 后的文件夹>
python build.py && python checks.py && python queries.py && python make_figures.py
```

本报告的 PDF 由 `python make_pdf.py` 生成，需要 Microsoft Edge 或 Google Chrome。

代码于 2026-11-15 和 2026-11-16 使用 Claude Code（模型 Claude Opus 5.5）编写，随后于 2026-11-16 由 ChatGPT/Codex 和作者审查。工具、作用、示例提示词和设置列在 `README.md` 第 7 节。没有任何模型输出被存为图谱事实：每个节点和每条边都来自所引用的 CSV 行或手工表，构建过程不调用任何模型。

## 7 结论

1. 用 2021 年 Kelmarsh 1 和 Kelmarsh 6 的记录构建了包含 414,506 个节点和 828,863 条边的知识图谱，每个节点和每条边都有确定的标识符和来源引用。
2. 缺失值、重复记录、重复导入和超出结构的记录都已处理并记录在日志中；完整性检查报告 0 个问题，重新构建得到完全相同的图谱。
3. 抽样的 50 条事实在自动比较中全部与来源行一致；人工判断记录在 `fact_verification_sample.csv` 中。
4. 三个计划中的问题都由可运行的查询回答，结果已保存；Q1 经过三种领域关系。

## 参考文献

1. Plumley C., Takeuchi R. Kelmarsh wind farm data. Version 4. Zenodo, 2025. DOI: 10.5281/zenodo.16807551. Licence CC BY 4.0.
2. Hagberg A. A., Schult D. A., Swart P. J. Exploring network structure, dynamics, and function using NetworkX // Proceedings of the 7th Python in Science Conference (SciPy 2008). 2008. P. 11–15.
3. McKinney W. Data structures for statistical computing in Python // Proceedings of the 9th Python in Science Conference (SciPy 2010). 2010. P. 56–61.
