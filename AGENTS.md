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

* **Dragon Executable**: 本机 `/home/ljiayi/DRAGON2-Beta_version-master/DRAGON`；companion、yellowgiant、bluegiant、redgiant 均为 `/home/ljiayi/dragon/DRAGON2-Beta_version-master/DRAGON`，从各程序目录调用启动器。
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
* **计算线程**：companion 当前构建为 48 个 OpenMP 线程。配置同时使用 `--with-numcpu=48` 与 `CPPFLAGS=-I<prefix>/include -DNUMTHREADS=48`，生成的 `NUMTHREADS`、`OMP_NUM_THREADS` 宏均为 48。修改计算线程数需在无运行中模型时重新配置、编译；不自动终止既有计算。`make -j4` 仅控制编译并行度。主机有 24 个物理核心、48 个逻辑 CPU。
* **构建记录**：最新 CFITSIO 大 FITS 修复见 `outputs/workflow/2026-10-14_fits.json`，48 线程构建基础见 `outputs/workflow/2026-10-10_threads48.json`，完整构建/验证日志在 `logs/`；`2026-10-10_threads.json`、`2026-10-10_build.json` 分别保留历史 24、4 线程构建记录。24 线程运行记录另存 `outputs/workflow/2026-10-10_cpu24.json`，同一 XML 的 24/48 线程原生耗时比较见 `2026-10-10_speed.json`，不覆盖历史源码/程序哈希。
* **FITS 库**：companion 的 CFITSIO 4.7.0 独立安装在 `/home/ljiayi/.local/dragon/cfitsio47/`，重建优先使用其 include/lib/rpath；原 `/home/ljiayi/.local/dragon/usr/` 保留旧库及当前 GSL。worker 的 LD_LIBRARY_PATH 包含新 CFITSIO 的 lib。旧 CFITSIO 4.0.0 的 gzip 写出可能将超过 4 GiB 的 fullstore 截断，不能回退后继续此类大文件计算；升级不恢复已有损坏文件。更换库后核验运行时链接、48 线程宏和物理源码哈希，使用无 DRAGON 模拟的 FITS 回归验证。

### Yellowgiant Compute Host

* **SSH Address**: alias `yellowgiant`，即 `ljiayi@192.168.72.45`。
* yellowgiant 当前 DRAGON2 构建为 32 个 OpenMP 线程，使用与 companion 相同的物理源码、默认丰度表、程序目录和 CFITSIO 4.7.0 路径；二进制因线程数不同而不同。
* yellowgiant 的物理内存限制要求 BayesianOptimization 候选统一使用 `Zmax=8`。四台主机的 Z=8 ASCII 谱均按 `data/2026-10-28_z14-z8-coefficient.csv` 逐能量、逐列转换为 Z=14 预测，只有该预测进入太阳调制和评分。
* BayesianOptimization 使用异步四主机共享优化池：companion、yellowgiant、bluegiant、redgiant 任一完成、回传、Z=14 转换和评分后立即更新同一优化器并领取下一候选，不等待其他主机；运行中候选以 constant-liar 计入提议且全局去重。

### Bluegiant Compute Host

* **SSH Address**: alias `bluegiant`，即 `ljiayi@192.168.72.46`；使用 `ssh bluegiant` 免密连接。
* **Operating System**: Ubuntu 20.04。
* bluegiant 的硬件配置、BayesianOptimization 程序目录、项目绝对路径与32线程构建配置均与 yellowgiant 相同。系统 Python 保持3.8不变；BayesianOptimization 远端 worker 使用用户目录 `/home/ljiayi/.local/python3.12.3/bin/python3.12`，与 yellowgiant 的 Python 3.12.3 对齐。

### Redgiant Compute Host

* **SSH Address**: alias `redgiant`，即 `ljiayi@192.168.72.47`；使用 `ssh redgiant` 免密连接。
* **Operating System**: Ubuntu 20.04。
* redgiant 的硬件配置、BayesianOptimization 程序目录、项目绝对路径与32线程构建配置均与 yellowgiant 相同。系统 Python 保持3.8不变；BayesianOptimization 远端 worker 使用用户目录 `/home/ljiayi/.local/python3.12.3/bin/python3.12`，与 yellowgiant 的 Python 3.12.3 对齐。


## 3. Execution & Logging Rules

* **Dragon/Dragon2 Logs**: Every time `dragon` or `dragon2` is executed, copy all output logs into `~/dragon_project/logs/`.
  * Naming format: `YYYY-MM-DD_HH-MM-SS.md`.
  * 单轮 companion 入口每次新计算启动后，在 muon 自动创建或复用 `dragon_log` tmux 会话并新增本轮窗口。BayesianOptimization 是明确例外：主控固定使用 `BayesOpt:main.0`，四台主机日志分别固定使用 `companion_log:log.0`、`yellowgiant_log:log.0`、`bluegiant_log:log.0`、`redgiant_log:log.0`；新批次只 respawn 对应窗格、清空上一轮日志历史，不新建窗口。日志查看失败只警告，不取消模型；无模拟预检不创建日志窗口。
  * 运算结束并取回日志后，`run`、`fetch` 在脚本终端各打印一次 DRAGON 原生的 `Solution found in ... s.` 文本，并记录 `duration`；禁止用 Python 或开始/结束时间差替代该耗时。原生耗时行缺失时如实报告，不编造。
* **DRAGON/DRAGON2 XML Parameters**:
  * All XML parameter files used, created, or stored by any task for DRAGON/DRAGON2 calculations must be kept in `/home/ljiayi/dragon_project/data/processed/`.
  * companion 单轮输入、原始模拟数据及状态记录统一主体 `YYYY-MM-DD_dimZ<N>`，不按图的种类分类，不接收 `--task`；N 是 XML 的实际整数 DimZ。优先读取用户 XML 同目录同主体的 `.source.param`；该文件缺失时使用固定默认表 `/home/ljiayi/DRAGON2-Beta_version-master/config_files/template.source.param`。所选表按字节复制成 `data/processed/<stem>.source.param`，与规范 XML 同目录同主体并一同上传；预览/状态记录 `sourceDefault`、实际来源及 SHA256，使用默认表时终端和命令日志注明来源。同名表存在但无效时不得替换；默认表缺失/无效仍报错。不改动原始 XML 或丰度模板。
  * 先完成本机规范 XML/丰度副本的全部复制及哈希、DimZ 核验，再上传这些副本；远端只用 `runXml` 指定的规范 XML 启动 DRAGON2，启动前核验上传文件名、同名丰度表、实际 DimZ、本轮主体与哈希一致。终端/命令日志显示本机准备路径、DimZ、远端启动路径，不依赖原文件名中的旧 DimZ。
  * 两张图片仍使用下述 BCratio/pHe 名称，允许图片主体中的两个下划线，覆盖旧单下划线限制；其他新变量、函数及文件名仍遵守原限制。
  * BayesianOptimization 候选按用户指定主体 `YYYY-MM-DD_BayesOpt_D<值>_dA<值>_dB<值>_dZ<值>_a<值>` 命名；该主体的多个下划线是显式例外。`a` 是 `InjectionIndexAllNuclei` 下 `alpha_0` 至 `alpha_3` 的共同值，保留但不调整 `rho_0` 至 `rho_2`，不引入 injection breaking。日期取候选 XML 实际生成时的 Asia/Tokyo 日期，不能固定为整个优化启动日；名称中的参数值最多保留 4 位有效数字，XML、JSON、CSV 与优化器内部数值保持完整精度。候选 XML 与同名丰度表在 `data/processed/`，主机交叉结果以连字符主机后缀区分。
  * Asia/Tokyo 日期在每轮启动时固定，跨午夜不变。同日同 DimZ 使用统一状态与锁，重新运行直接覆盖对应的输入副本、状态、数据和图片；`fetch`、`plot` 同样直接替换对应文件，无需 `--overwrite`（旧参数仅作兼容）。仍拒绝并发提交以及覆盖 `prepared/launching/running/finalizing/unknown` 远端任务，日志每轮独立保留。不静默增加 UUID 或额外时间戳。历史 BCratio/pHe 主体仍可用于 `fetch`、`plot`，不自动改名或重算。
  * 原始 ASCII/fullstore FITS 归档到 `data/dragon_output/<stem>.txt` / `<stem>.fits.gz`；partialstore 原生 `<stem>_spectrum.fits.gz` 映射为 `<stem>-spectrum.fits.gz`，记录原始与归档名称。派生文件用简洁连字符后缀，区分空间分布与太阳位置谱。
  * ASCII 与 XML 开启的 fullstore/partialstore FITS 同轮生成、核验并回传；入口完成后明确打印所有已回传原始数据的本机路径。DRAGON 只打印 ASCII 写入提示不代表 FITS 缺失；入口不自动修改 XML 输出开关。
* **Generated Plots**:
  * Save all generated plots directly in `/home/ljiayi/dragon_project/outputs/figures/`; do not create or use separate subfolders for plots.
  * companion 两张图分别为 `YYYY-MM-DD_BCratio_dimZ<N>.png` 和 `YYYY-MM-DD_pHe_dimZ<N>.png`；使用同轮数据，不重复模拟或复制两套原始数据。其他图片采用日期在前的 `YYYY-MM-DD_<description>.png`；显式输出路径优先。
  * 每个 BayesianOptimization 候选完成 Z=14 修正和太阳调制评分后，必须分别生成带候选主体及主机后缀的 `BCfitting`、`pHefitting27` 图片；后者必须展示 `R>=30 GV` 的 p、He 独立正归一化拟合。
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
  * Function: Apply the existing fixed 0.64 GV solar modulation separately to B-10, B-11, C-12, C-13, and C-14, sum the isotope TOA fluxes by element, compare TOA B/C with AMS-02 TOA, and plot B/C, Model/Data, and fractional residuals. This is a diagnostic comparison and does not perform automatic parameter optimization.
* **p/He**: For a proton/helium comparison call `python3 /home/ljiayi/dragon_project/dragon_utils/plotting/pHefitting27.py [source]`. For an explicit flux-normalization fit call the same command with `--fit`; use `--fit-min <GV>` only when the requested threshold differs from the 10 GV default.
  * Function: Apply the existing fixed solar modulation, compare proton and total helium (He-3 + He-4) TOA spectra and the equal-rigidity p/He ratio with AMS-02. All panels display only R > 5 GV. Weight model flux, observations and uncertainties by R^2.7 in the first two panels for display; chi-square always uses unweighted flux. `--fit` independently fits positive post-processing constants for the whole proton TOA flux and the combined He-3 + He-4 TOA flux above the rigidity threshold. It verifies the analytic weighted-least-squares solution at six nearby constants and adopts a grid value only if its chi-square is lower. The p/He ratio remains unweighted and has no chi-square.
* **Input**: `[source]` is an optional `.txt` spectrum path or directory. Prefer the user-specified or current-task spectrum; when omitted, both scripts select the latest `.txt` in `/home/ljiayi/dragon_project/data/dragon_output/`. Report the actual input file used.
* **Scope**: Reuse these existing scripts for comparison. `pHefitting27.py --fit` only fits two output-flux normalization constants; it does not edit XML/source abundances, optimize propagation parameters, or run DRAGON. BCfitting remains diagnostic only.
* **Plot Files**: 两脚本支持 `[source] --output /absolute/path/figure.png`。优先在调用时指定 Section 3 的精确图片路径，避免默认分钟名称碰撞，不在执行后猜测或选择最新图片。companion 入口始终传入本轮确切 TXT 和两张规范图片路径。
* **Single Round**: 用户先手动检查 XML，再执行 `python3 /home/ljiayi/dragon_project/scripts/run_companion.py run /absolute/path/model.xml`；一次调用只模拟一遍并自动输出 BCratio、pHe 两张图。用 `--preview` 无写入预览，`fetch YYYY-MM-DD_dimZ<N>` 只查询/取回，`plot YYYY-MM-DD_dimZ<N>` 只重做两张图。用户没有选择实际 XML 时只实现、构建和无模拟验证，不自行运行历史模型。
* **Completion**: 按真实进程退出码、XML 输出清单及哈希判定，失败也同步日志；断线先查状态，禁止盲目重跑，不以文件出现/大小稳定作为成功。均匀网格才记录 `2L/(DimZ-1)`，非均匀网格单独识别。固定 L 及物理参数，由用户选择 DimZ；实验 χ² 的改善不能替代网格收敛验证。
  * 回传/校验中断且未生成本轮图片时，不把仍留在目录中的旧 DimZ 图片当作本轮结果；已成功的远端任务可用 `fetch <stem>`、`plot <stem>` 恢复，不重复模拟。

## 5. Research Goal: Reference Only

Read and apply this section **only when the user explicitly mentions this research goal**. It is a direction for evaluating proposed work, not authorization to begin or expand implementation. The user defines the scope of each individual request. Do not continue the full goal, modify code, or run simulations merely because this goal exists in `AGENTS.md`.

基于已实现空间依赖扩散指数的 3D DRAGON2 模型，使用贝叶斯优化在物理合理的参数范围内搜索；对每组候选参数计算宇宙线原子核能谱及相关次级／初级比值，并与观测数据比较，找出能够描述质子、氦及相关比值观测的优选参数区域。随后迭代细化参数空间与数值设置，验证计算误差满足观测精度要求，最终确定优选或最佳拟合传播参数及其不确定性和相关性。

研究范围止于修论计划书中参数空间与数值精度迭代细化的阶段。MCMC、独立机器学习模型、长期维护和更复杂的空间依赖形式不是预设必需项。相关任务表见项目根目录的 `tasks_cn.md` 和 `tasks_en.md`；任务表同样只供用户明确提到时参考，不自动授权其中任何一项工作。


## 6. 可复用入口与维护

| 路径 | 用途及推荐调用 | 范围 |
| --- | --- | --- |
| `scripts/run_companion.py` | `python3 scripts/run_companion.py run <xml> [--preview]`；缺少同名丰度表时使用固定默认表；`fetch <stem>`、`plot <stem>`，主体 `YYYY-MM-DD_dimZ<N>`；首次日志查看 `tmux attach -t dragon_log`，已连接时自动切换新日志 | 推荐 companion 单轮入口；一次模拟、两张图、XML 开启的 FITS；丰度来源/哈希、自动日志窗口、切换和原生耗时；不自动编辑参数/搜索/排队 |
| `scripts/zgrid_convergence.py` | `python3 scripts/zgrid_convergence.py [--input <directory>] [--output <csv>] [--points 200]`；默认读取 `data/dragon_output/`、原子重算 `outputs/csv/zgrid_convergence.csv` | 离线复用 B/C LIS、p/He TOA 函数；最大相对差异（百分比）仅取动能 0.1–50000 GeV/n 与所有模拟共同覆盖的交集：B/C 限制 LIS 能量，p/He 限制 TOA 能量并按核素换算刚度，总氦取 He-3/He-4 允许刚度的交集；按 DimZ 比较相邻及最大网格参考；只读均匀网格元数据求 dz，保留质子及等刚度总氦太阳调制（当前 0.64 GV），完整 LIS 供调制插值；只输出 CSV，不生成异常报告／图或自动边缘截断，不运行 DRAGON/SSH，不给出收敛判定；此固定 CSV 名称按任务要求保留，字段名称遵循指定列头 |
| `dragon_utils/companion.py` | `from dragon_utils.companion import run_command, execute, upload, download`；参数列表、log、可选 host；前两函数可 `capture=True` | SSH/rsync、合并 stdout/stderr 与真实退出码；不调度模型 |
| `scripts/xml_batch.py` | `from scripts.xml_batch import ModelSpec, prepare_models, file_hash, copy_baseline, save_state` | 本机手动准备输入和记录；库模块，无 CLI |
| `dragon_utils/xml_manager/xml_modifier.py` | `load_xml/get_param` 只读；`modify_xml(template, params, output, diff)` 编辑 | 推荐 XML 接口；运行入口只读，物理参数编辑在用户检查之前 |
| `dragon_utils/xml_manager/parameter_map.py` | 导入 `PARAM_MAP`、`NODE_MAP` | L、DimZ、核素链和其他参数 XPath；输出开关由节点存在性决定 |
| `dragon_utils/plotting/BCfitting.py` | `python3 .../BCfitting.py <txt> --output <png>` | B-10/11、C-12/13/14 分别以固定 0.64 GV 调制后求和；TOA B/C 与 AMS-02 TOA 诊断；默认 `load_model()` 仍保留 LIS 比值供网格收敛复用 |
| `dragon_utils/plotting/pHefitting.py` | `python3 .../pHefitting.py <txt> --output <png>` | 未加展示权重的调制后刚度谱；保留 Z 网格分析等依赖，不作为 companion 默认绘图 |
| `dragon_utils/plotting/pHefitting27.py` | 对比：`python3 .../pHefitting27.py <txt> [--output <png>]`；归一化拟合：追加 `--fit [--fit-min <GV>]`；默认图分别为 `YYYY-MM-DD_pHe27.png`、`YYYY-MM-DD_pHefit.png` | companion 默认仍为不拟合的 R^2.7 展示版；三图仅显示 R>5 GV；`--fit` 默认以 R≥10 GV 分别拟合整体 p/He TOA 常数，解析解经六点邻域网格验证，图内标注常数与 χ²并输出唯一 `FIT_RESULT=<JSON>`；不改 XML/丰度、不运行 DRAGON |
| `dragon_utils/data_processing/{flux,physics,statistic_analysis}.py` | 导入 `interp`、`SM_output`、`chisquare`、`fit_constant` | 推荐插值、调制和统计工具；`fit_constant` 给单一正乘法常数的解析解并可验证邻域扫描；保留既有单位/口径 |
| `dragon_utils/xmltools.py`、旧 `readDRAGON.py`、`CALETana_functions/` | 见各目录唯一 README | 历史或实验性接口，不替代推荐入口 |
| `dragon_utils/prop/BayesianOptimization/BayesOpt.py` | `bash dragon_utils/prop/BayesianOptimization/start_BayesOpt.sh --check`；四主机一轮测试用 `--test`；已有远端成功状态只续取用 `--resume-test`；正式搜索用全局成功候选总数 `--calls N` | 从指定 Zmax=8 XML 搜索 D0/deltaA/deltaB/deltaZ/共同 nuclei alpha，固定 DiffusionThresholdZ=0；旧四维历史从 XML 核验共同 alpha 后升为五维、离线重新评分并计入总数，最优历史点作为 incumbent；候选名称按 XML 生成日并将参数限制为最多 4 位有效数字，物理值保持完整精度；companion/yellowgiant/bluegiant/redgiant 异步共享优化池、运行点 constant-liar 与全局去重；Z=14 系数修正、R≥30 GV 独立归一化后的 p/He χ²加 B/C χ²、每候选双图与 `outputs/csv/YYYY-MM-DD_BayesOpt.csv`；`BayesOpt` 每周期显示四主机状态及 4 位有效数字的当前最佳；正式主控和四主机日志分别固定使用五个单窗口 session |
| `dragon_utils/prop/` 其他目录 | 见各子目录 README | 独立优化/代理模型实验；其他包含旧自动提交链路，不由 companion 或 BayesOpt 入口调用 |
| 旧 `/home/ljiayi/Scripts/calcDRAGONauto.py`、`calcmodlist.txt` 与 `optim_copy.py` | 历史队列/自动搜索 | 与单轮任务独立，禁止向旧队列提交或部署新轮询流程 |

本次任务明确授权新增 `scripts/run_companion.py` 及本流程必要函数、修改相关传输/绘图接口、创建或更新 README 与 AGENTS.md；此授权不扩大为其他 Python/脚本重构。

**长期维护规则：如果脚本/代码所在目录有 README，完成代码修改后必须同步更新 README 中受影响的说明；同时检查并更新 AGENTS.md 中可能相关的用途、入口、调用方式、路径、命名和规则。** 新脚本加入已有目录时必须补充该目录 README。每个包含直属代码（Python、Shell、Notebook 或其他脚本）的目录只保留一个 README，更新已有大小写名称，不另建变体；有多个时合并保留有用内容。子目录各自说明直属脚本，不把所有详情混入父目录。缓存、虚拟环境及纯数据归档不算脚本目录。远端新增/修改自有运行脚本也遵守该规则。代码注释用简洁英文，文档与用户沟通用中文。
