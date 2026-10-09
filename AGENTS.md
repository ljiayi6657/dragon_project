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

* **Dragon Executable**: `~/`
* **DRAGON Output Data (`.txt`, `.fits.gz`)**: `~/dragon_project/data/dragon_output/`
* **Experiment data**: `~/dragon_project/data/experiment_data/`
* **Processed Data**: `~/dragon_project/data/processed/`
* **Utilities**: `~/dragon_project/dragon_utils/`
* **Scripts**: `~/dragon_project/scripts/`
* **Execution Logs**: `~/dragon_project/logs/`
* **Outputs (Figures/Tables/CSVs)**: `~/dragon_project/outputs/<subfolder>/`
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
  * Naming format: `YYYY-MM-DD_<task>.xml`.
* **Generated Plots**:
  * Save all generated plots directly in `/home/ljiayi/dragon_project/outputs/figures/`; do not create or use separate subfolders for plots.
  * Naming format: `<task>_YYYY-MM-DD.png`.
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
* **Plot Files**: Both scripts save in `/home/ljiayi/dragon_project/outputs/figures/`. After running, rename only the newly generated plot to `<task>_YYYY-MM-DD.png` using the Asia/Tokyo date, following the plot rule in Section 3.

## 5. Research Goal: Reference Only

Read and apply this section **only when the user explicitly mentions this research goal**. It is a direction for evaluating proposed work, not authorization to begin or expand implementation. The user defines the scope of each individual request. Do not continue the full goal, modify code, or run simulations merely because this goal exists in `AGENTS.md`.

基于已实现空间依赖扩散指数的 3D DRAGON2 模型，使用贝叶斯优化在物理合理的参数范围内搜索；对每组候选参数计算宇宙线原子核能谱及相关次级／初级比值，并与观测数据比较，找出能够描述质子、氦及相关比值观测的优选参数区域。随后迭代细化参数空间与数值设置，验证计算误差满足观测精度要求，最终确定优选或最佳拟合传播参数及其不确定性和相关性。

研究范围止于修论计划书中参数空间与数值精度迭代细化的阶段。MCMC、独立机器学习模型、长期维护和更复杂的空间依赖形式不是预设必需项。相关任务表见项目根目录的 `tasks_cn.md` 和 `tasks_en.md`；任务表同样只供用户明确提到时参考，不自动授权其中任何一项工作。
