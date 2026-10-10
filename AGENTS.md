# Codex CLI Project Rules & Guidelines

## 1. Interaction & Code Style

* **Response Language**: Always explain and communicate with the user in **Chinese (中文)**.
* **Code Comments**: Keep inline comments concise and strictly in **English**.
* **Naming Conventions**:
  * Keep all variable names and file names as concise as possible.
  * Standard names should contain **at most one underscore (`_`)** as a separator (e.g., `raw_data`, `plot_spectrum`).
  * If a name cannot be expressed clearly with a single `_` (requiring multiple underscores), **stop and discuss with the user** first.
* **Code Review Workflow**: If any code modifications are involved, always open/display the difference (diff) interface for user review immediately after completing all changes.
* **Script & Function Maintenance**:
  * **DO NOT** create or delete any Python functions/modules or bash scripts autonomously.
  * Function modules location: `~/dragon_project/dragon_utils/`.
  * Script files location: `~/dragon_project/scripts/`.
  * If a required script or function is missing, **stop and discuss with the user** before writing new ones.

## 2. Directory Structure & File Paths

* **Dragon Executable**: 本机 `/home/ljiayi/DRAGON2-Beta_version-master/DRAGON`；companion `/home/ljiayi/dragon/DRAGON2-Beta_version-master/DRAGON`，从各程序目录调用启动器。
* **DRAGON Output Data (`.txt`, `.fits.gz`)**: `~/dragon_project/data/dragon_output/`
* **Experiment data**: `~/dragon_project/data/experiment_data/`
* **Processed Data**: `~/dragon_project/data/processed/`，包括输入/生成 XML 与同主体 `.source.param`。
* **Utilities**: `~/dragon_project/dragon_utils/`
* **Scripts**: `~/dragon_project/scripts/`
* **Execution Logs**: `~/dragon_project/logs/`
* **Figures**: `/home/ljiayi/dragon_project/outputs/figures/`；所有图片直接存放，不新建图片子目录。
* **Workflow**: `/home/ljiayi/dragon_project/outputs/workflow/`；任务状态、哈希、文件对应清单。
* **Other Outputs (Tables/CSVs)**: `~/dragon_project/outputs/<subfolder>/`
* **Documentation**: `~/dragon_project/docs/`

### Companion Compute Host

* **SSH Address**: `ljiayi@192.168.72.54`; connect with `ssh ljiayi@192.168.72.54`.
* 用户提到在 **companion** 上执行任务时，指通过 SSH 连接上述实验室内网主机进行计算。
* 默认在本机准备和检查 XML，在 companion 上运行 DRAGON2，将本轮结果及全部运行日志同步回本机


## 3. Execution & Logging Rules

* **Dragon/Dragon2 Logs**: Every time `dragon` or `dragon2` is executed, copy all output logs into `~/dragon_project/logs/`.
  * Naming format: `YYYY-MM-DD_HH-MM-SS.md`.
* **DRAGON/DRAGON2 XML Parameters**:
  * All XML parameter files used, created, or stored by any task for DRAGON/DRAGON2 calculations must be kept in `/home/ljiayi/dragon_project/data/processed/`.
  * companion 单轮输入、原始模拟数据及状态记录统一主体 `YYYY-MM-DD_dimZ<N>`，不按图的种类分类，不接收 `--task`；N 是 XML 的实际整数 DimZ。XML 与 `.source.param` 同目录同主体，源丰度缺失必须报错，不替换模板。
  * 两张图片仍使用下述 BCratio/pHe 名称，允许图片主体中的两个下划线，覆盖旧单下划线限制；其他新变量、函数及文件名仍遵守原限制。
  * Asia/Tokyo 日期在每轮启动时固定，跨午夜不变。同日同 DimZ 使用统一状态与锁，默认拒绝覆盖，只有用户主动给 `--overwrite` 才替换本轮对应文件，不静默增加 UUID 或额外时间戳。历史 BCratio/pHe 主体仍可用于 `fetch`、`plot`，不自动改名或重算。
  * 原始 ASCII/fullstore FITS 归档到 `data/dragon_output/<stem>.txt` / `<stem>.fits.gz`；partialstore 原生 `<stem>_spectrum.fits.gz` 映射为 `<stem>-spectrum.fits.gz`，记录原始与归档名称。派生文件用简洁连字符后缀，区分空间分布与太阳位置谱。
* **Generated Plots**:
  * Save all generated plots directly in `/home/ljiayi/dragon_project/outputs/figures/`; do not create or use separate subfolders for plots.
  * companion 两张图分别为 `YYYY-MM-DD_BCratio_dimZ<N>.png` 和 `YYYY-MM-DD_pHe_dimZ<N>.png`；使用同轮数据，不重复模拟或复制两套原始数据。其他图片采用日期在前的 `YYYY-MM-DD_<description>.png`；显式输出路径优先。
* **Other Generated Outputs**:
  * Save all generated images, tables, CSVs, etc., into corresponding subdirectories inside `~/dragon_project/outputs/`, unless the user specifies another location.
  * Naming format: `YYYY-MM-DD_<description>.<ext>` (use concise English for `<description>`, respecting the single-underscore limit where possible).
  * Plots follow the dedicated plot rule above instead of these general output rules.

## 4. Special Triggers & Workflows

### Trigger A: Task Notes

* **Condition**: Trigger ONLY when the user explicitly asks to summarize the task (e.g., "总结这个任务并输出notes").
* **Action**: Generate a task summary covering what was done, main results obtained, and future directions or next steps.
* **Storage Path**: `~/dragon_project/docs/notes/`.
* **Outputs**: Generate two separate files: `YYYY-MM-DD_<summary_cn>.md` and `YYYY-MM-DD_<summary_en>.md`.

### Trigger B: Prompt Generation

* **Condition**: Trigger when the user requests generating prompts for subsequent tasks.
* **Action**: Write down the prompts without executing them.
* **Storage Path**: `~/dragon_project/docs/prompts/`.
* **Outputs**: Generate two separate files: `YYYY-MM-DD_<summary_cn>.md` and `YYYY-MM-DD_<summary_en>.md`.

### Trigger C: B/C and p/He Comparison / Fitting

* **B/C**: When the user requests B/C or BC ratio comparison / fitting (e.g., "对比BC ratio" or "BC fitting"), directly call `python3 /home/ljiayi/dragon_project/dragon_utils/plotting/BCfitting.py [source]`.
  * Function: Sum boron and carbon isotope fluxes from DRAGON/DRAGON2 ASCII output, compare B/C with AMS-02, and plot B/C, Model/Data, and fractional residuals. This is a diagnostic comparison of unmodulated model LIS with observed TOA data.
* **p/He**: When the user requests proton/helium or pHe comparison / fitting (e.g., "pHe对比" or "pHe fitting"), directly call `python3 /home/ljiayi/dragon_project/dragon_utils/plotting/pHefitting.py [source]`.
  * Function: Apply the existing fixed solar modulation, compare proton and total helium (He-3 + He-4) TOA spectra and the equal-rigidity p/He ratio with AMS-02, and report raw chi-square for proton and helium separately; no p/He ratio chi-square is calculated.
* **Input**: `[source]` is an optional `.txt` spectrum path or directory. Prefer the user-specified or current-task spectrum; when omitted, both scripts select the latest `.txt` in `/home/ljiayi/dragon_project/data/dragon_output/`. Report the actual input file used.
* **Scope**: Reuse these existing scripts for comparison; neither script performs automatic parameter optimization.
* **Plot Files**: 两脚本支持 `[source] --output /absolute/path/figure.png`。优先在调用时指定 Section 3 的精确图片路径，避免默认分钟名称碰撞，不在执行后猜测或选择最新图片。companion 入口始终传入本轮确切 TXT 和两张规范图片路径。
* **Single Round**: 用户先手动检查 XML，再执行 `python3 /home/ljiayi/dragon_project/scripts/run_companion.py run /absolute/path/model.xml`；一次调用只模拟一遍并自动输出 BCratio、pHe 两张图。用 `--preview` 无写入预览，`fetch YYYY-MM-DD_dimZ<N>` 只查询/取回，`plot YYYY-MM-DD_dimZ<N> --overwrite` 只重做两张图。用户没有选择实际 XML 时只实现、构建和无模拟验证，不自行运行历史模型。
* **Completion**: 按真实进程退出码、XML 输出清单及哈希判定，失败也同步日志；断线先查状态，禁止盲目重跑，不以文件出现/大小稳定作为成功。均匀网格才记录 `2L/(DimZ-1)`，非均匀网格单独识别。固定 L 及物理参数，由用户选择 DimZ；实验 χ² 的改善不能替代网格收敛验证。

## 5. Research Goal: Reference Only

Read and apply this section **only when the user explicitly mentions this research goal**. It is a direction for evaluating proposed work, not authorization to begin or expand implementation. The user defines the scope of each individual request. Do not continue the full goal, modify code, or run simulations merely because this goal exists in `AGENTS.md`.

基于已实现空间依赖扩散指数的 3D DRAGON2 模型，使用贝叶斯优化在物理合理的参数范围内搜索；对每组候选参数计算宇宙线原子核能谱及相关次级／初级比值，并与观测数据比较，找出能够描述质子、氦及相关比值观测的优选参数区域。随后迭代细化参数空间与数值设置，验证计算误差满足观测精度要求，最终确定优选或最佳拟合传播参数及其不确定性和相关性。

研究范围止于修论计划书中参数空间与数值精度迭代细化的阶段。MCMC、独立机器学习模型、长期维护和更复杂的空间依赖形式不是预设必需项。相关任务表见项目根目录的 `tasks_cn.md` 和 `tasks_en.md`；任务表同样只供用户明确提到时参考，不自动授权其中任何一项工作。


## 6. 可复用入口与维护

| 路径 | 用途及推荐调用 | 范围 |
| --- | --- | --- |
| `scripts/run_companion.py` | `python3 scripts/run_companion.py run <xml> [--preview]`；`fetch <stem>`、`plot <stem>`，主体 `YYYY-MM-DD_dimZ<N>` | 推荐 companion 单轮入口；一次模拟、两张图；不自动编辑参数/搜索/排队 |
| `dragon_utils/companion.py` | `from dragon_utils.companion import run_command, execute, upload, download`；参数列表、log、可选 host；前两函数可 `capture=True` | SSH/rsync、合并 stdout/stderr 与真实退出码；不调度模型 |
| `scripts/xml_batch.py` | `from scripts.xml_batch import ModelSpec, prepare_models, file_hash, copy_baseline, save_state` | 本机手动准备输入和记录；库模块，无 CLI |
| `dragon_utils/xml_manager/xml_modifier.py` | `load_xml/get_param` 只读；`modify_xml(template, params, output, diff)` 编辑 | 推荐 XML 接口；运行入口只读，物理参数编辑在用户检查之前 |
| `dragon_utils/xml_manager/parameter_map.py` | 导入 `PARAM_MAP`、`NODE_MAP` | L、DimZ、核素链和其他参数 XPath；输出开关由节点存在性决定 |
| `dragon_utils/plotting/BCfitting.py` | `python3 .../BCfitting.py <txt> --output <png>` | B/C 同位素和；未调制 LIS 与 TOA 诊断 |
| `dragon_utils/plotting/pHefitting.py` | `python3 .../pHefitting.py <txt> --output <png>` | p、He-3+He-4 调制后刚度谱，原始 p/He 各自 χ²，无比值 χ² |
| `dragon_utils/plotting/pHefitting27.py` | `python3 .../pHefitting27.py <txt>` | 独立 R^2.7 展示版本，非单轮默认入口 |
| `dragon_utils/data_processing/{flux,physics,statistic_analysis}.py` | 导入 `interp`、`SM_output`、`chisquare` | 推荐插值、调制和统计工具；保留既有单位/口径 |
| `dragon_utils/xmltools.py`、旧 `readDRAGON.py`、`CALETana_functions/` | 见各目录唯一 README | 历史或实验性接口，不替代推荐入口 |
| `dragon_utils/prop/` | 见本目录与各子目录 README | 独立优化/代理模型实验；当前 BayesOpt 有本机 1–2 轮任务接口，其他包含旧自动提交链路，不由 companion 入口调用 |
| 旧 `/home/ljiayi/Scripts/calcDRAGONauto.py`、`calcmodlist.txt` 与 `optim_copy.py` | 历史队列/自动搜索 | 与单轮任务独立，禁止向旧队列提交或部署新轮询流程 |

本次任务明确授权新增 `scripts/run_companion.py` 及本流程必要函数、修改相关传输/绘图接口、创建或更新 README 与 AGENTS.md；此授权不扩大为其他 Python/脚本重构。

**长期维护规则：如果脚本/代码所在目录有 README，完成代码修改后必须同步更新 README 中受影响的说明；同时检查并更新 AGENTS.md 中可能相关的用途、入口、调用方式、路径、命名和规则。** 新脚本加入已有目录时必须补充该目录 README。每个包含直属代码（Python、Shell、Notebook 或其他脚本）的目录只保留一个 README，更新已有大小写名称，不另建变体；有多个时合并保留有用内容。子目录各自说明直属脚本，不把所有详情混入父目录。缓存、虚拟环境及纯数据归档不算脚本目录。远端新增/修改自有运行脚本也遵守该规则。代码注释用简洁英文，文档与用户沟通用中文。
