# 项目脚本

从 `/home/ljiayi/dragon_project/` 使用 Python 3.10+。本目录只说明直属脚本；库接口见 `../dragon_utils/` 各目录 README。

## run_companion.py

用户检查 XML 后主动执行一轮：校验输入、复制规范文件、SSH/rsync 同步、在 companion 启动一次 DRAGON2、等待退出状态、回传清单数据与日志、生成两张诊断图。不会修改物理参数，不连接旧 `calcmodlist.txt`，也不会提交下一轮。

```bash
python3 scripts/run_companion.py run /absolute/path/model.xml --preview
python3 scripts/run_companion.py run /absolute/path/model.xml
python3 scripts/run_companion.py fetch 2026-10-10_dimZ81
python3 scripts/run_companion.py plot 2026-10-10_dimZ81 --overwrite
```

示例 `model.xml` 必须是用户实际选择的文件，并有同目录同主体的 `model.source.param`；不自动使用丰度模板。示例 stem 的日期与 DimZ 应替换为该轮记录的值。`fetch` 只查询状态、下载日志，并在远端成功退出后取回结果；然后用 `plot` 作图。它不启动模拟。`plot` 不使用 SSH，只读取已成功取回且哈希未变的本轮数据。

`run --preview` 只读取输入、检查参数并打印 JSON 计划，不创建副本/日志/状态，不连接远端，不检查远端冲突。缺失源丰度、非法参数或核素范围返回非零退出码。均匀网格记录 `dz=2L/(DimZ-1)`；有 `DimZ_division` 时记录非均匀网格和原始 points，要求点数等于 XML 的 DimZ，不给出错误的统一 dz。各空间维度至少三个点，能量网格有限、递增；核素链需 `Zmin=1,Zmax>=6`。丰度行校验 UID、非负丰度、有限值与注入列结构，必须包含 p、He-3/4、B-10/11、C-12/13/14。拒绝 `OnlyPrimaries` 和首版清单不支持的 `timestepstore`。这些校验不替代用户对传播物理和数值参数的检查。

入口不再按 BCratio/pHe 分类，也不接收 `--task`。一次 `run` 只提交一次模拟，成功回传后自动生成 B/C 与 pHe 两张图；一次 `plot` 用同一份本轮数据重做两张图。既有 `YYYY-MM-DD_BCratio_dimZ<N>` / `YYYY-MM-DD_pHe_dimZ<N>` 记录仍可用原主体执行 `fetch`、`plot`，不自动改名或重新计算。

日期在启动时按 Asia/Tokyo 固定，XML、源丰度、原始数据与状态记录统一主体 `YYYY-MM-DD_dimZ<N>`；N 从 XML 读取。同一原始数据生成两张分别命名的图：

| 产物 | 路径 |
| --- | --- |
| XML、源丰度 | `data/processed/<stem>.xml`、`<stem>.source.param`；字节复制，保留原始输入 |
| ASCII | `data/dragon_output/<stem>.txt` |
| fullstore | `data/dragon_output/<stem>.fits.gz`；完整空间分布 |
| partialstore | `data/dragon_output/<stem>-spectrum.fits.gz`；原生 `<stem>_spectrum.fits.gz` 为太阳位置谱 |
| 两张图 | `outputs/figures/YYYY-MM-DD_BCratio_dimZ<N>.png`、`YYYY-MM-DD_pHe_dimZ<N>.png` |
| 状态与哈希 | `outputs/workflow/<stem>.json`；同名 `.lock` 用于排斥并发 |
| 命令/运行日志 | `logs/YYYY-MM-DD_HH-MM-SS.md`；完整合并 stdout/stderr，分开保存控制命令与远端运行日志 |

同日同 DimZ 的已有输入副本、状态、数据或图片默认拒绝覆盖。原文件本身已是规范位置时直接读取，不重复复制。只有明确传入 `--overwrite` 才替换对应本轮文件；它仍不能覆盖或重启 `prepared/launching/running/finalizing/unknown` 远端任务。同日同 DimZ 使用统一状态与锁，重复或并发调用不能通过改变图的分类再提交一次。日志永不复用旧文件名。

远端固定地址 `ljiayi@192.168.72.54`，输入同本机 `data/processed/` 路径，程序目录 `/home/ljiayi/dragon/DRAGON2-Beta_version-master/`，从该目录调用 `DRAGON` 启动器。运行 worker 是通过 SSH 传入的标准库 Python 代码，不部署常驻队列或新的远端脚本。它脱离 SSH 会话，原子记录任务状态、PID/进程起始标识/主机 boot ID、输入及源码（含 cparamlib C 源文件）/程序/共享库 SHA256、开始结束时间、真实退出码、原生与归档文件对应关系。

完成条件是进程退出码为零且 XML 开启的各输出非空。取回暂存文件后核对 SHA256 与长度，复用两个绘图 reader 检查 ASCII 列、能量轴与通量，并解析所有 FITS HDU、读取 gzip 至末尾检查完整性，然后归档。不根据文件出现或大小稳定判断成功。失败也取回可取得的完整运行日志；作图失败保留原始数据及 `plotFailed` 状态，可以 `plot --overwrite` 重做。图片先在 figures/ 直属临时 PNG 文件中生成，再替换正式路径并清理临时文件，不创建图片子目录。

SSH 中断或 Ctrl-C 后保留远端任务，使用同一 stem 的 `fetch` 检查，再决定下一步。远端仍在运行时 `fetch` 下载当前日志并非零退出，不拉模拟结果；稍后再次执行。worker 消失、重启或身份变化时标记 `unknown`，缺少完整退出记录时不会宣称成功。输入上传中断而还没有 launch 时尽力标记失败；若连接阻断导致 `prepared/launching/unknown` 残留，需 SSH 检查 JSON、日志与实际进程，人工确认终止状态后再考虑显式覆盖。入口不自动取消模型。

依赖：本机 `ssh`、`rsync`、lxml、NumPy、SciPy、Matplotlib、Astropy，以及 `data/experiment_data/expdata/` 中现有 AMS 数据；远端 Python 3.9+、rsync 和可运行 DRAGON2。库接口 `inspect_xml`、`make_plan`、`rpc`、`pull`、`draw` 供入口复用；复制、哈希、状态复用下方模块。两个诊断保留各自物理/统计口径，实验 χ² 改善不等于网格收敛。

远端构建记录在 `outputs/workflow/2026-10-10_build.json` 和对应 `logs/`。依赖用 Ubuntu jammy 的 GSL/CFITSIO 包解包到 `/home/ljiayi/.local/dragon/usr/`，不需要 sudo。配置需给该 include、multiarch 库目录及 rpath，`--with-gsl-path=<prefix>/bin --with-cfitsio=<prefix> --with-numcpu=4`，链接参数还需 `-Wl,--disable-new-dtags -Wl,-rpath,<prefix>/lib/x86_64-linux-gnu`，让依赖的间接共享库也能解析；以及 `CPPFLAGS=-I<prefix>/include -DNUMTHREADS=4`；随后 `make clean`、`make -j4`。运行 worker 显式提供该依赖库目录和程序 `.libs` 路径。数值模型端到端验收需用户选择 XML。

## xml_batch.py

本机批量输入准备库，没有 CLI 主循环；不运行 DRAGON。`ModelSpec(name, params, drops=())` 描述一组手动参数，`prepare_models(...)` 用 `xml_manager.modify_xml` 生成 XML、同名源丰度、文本 diff、日志及 JSON 状态。`copy_baseline` 保持字节内容，`file_hash` 返回 SHA256，`check_new` 默认拒绝覆盖，`save_state` 保存 JSON。依赖 Python 3.10+ 与 lxml。

```python
from scripts.xml_batch import ModelSpec, prepare_models
prepare_models(
    [ModelSpec("2026-10-10_dimZ81", {"DimZ": 81})],
    baseline="/home/ljiayi/dragon_project/data/processed/model.xml",
    source="/home/ljiayi/dragon_project/data/processed/model.source.param",
    xml_dir="/home/ljiayi/dragon_project/data/processed",
    diff_dir="/home/ljiayi/dragon_project/outputs/workflow",
    log_dir="/home/ljiayi/dragon_project/logs",
    state="/home/ljiayi/dragon_project/outputs/workflow/batch.json",
)
```

此库旧的批量日志和 diff 使用其自身 timestamp/prefix 格式，未改成运行入口的日志格式；本次只复用无参数修改的辅助函数。批量准备后的 XML 仍须用户检查，并由 `run_companion.py` 规范命名及核验，不能据 `prepare_models` 成功推断模型可运行。
