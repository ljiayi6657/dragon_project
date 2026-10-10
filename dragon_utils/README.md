# dragon_utils 代码说明

仅覆盖本目录直属代码。子目录见各自 README。历史工具的原有路径/命名未经本任务迁移；推荐 companion 单轮入口为项目 scripts/run_companion.py。示例说明实际接口，不表示历史优化/外部数据环境已通过运行验收。

## companion.py

SSH/rsync 标准库传输与完整命令日志；run_command/execute 新增 capture=False，True 返回合并 stdout 字符串并仍完整写日志。非零退出抛 RuntimeError，upload/download 传单个确切文件，目标目录须存在。

输入输出与限制：输入参数列表/路径/日志，输出 CompletedProcess 或传输文件；默认 companion 地址见 HOST，无队列或自动重试。

示例（历史/实验代码须先修正依赖与路径，不在本任务中执行）：

```python
from dragon_utils.companion import execute
execute(["pwd"], "/home/ljiayi/dragon_project/logs/2026-10-10_12-00-00.md", capture=True)
```

主要接口：`run_command`, `execute`, `upload`, `download`。

实际导入：`datetime`, `pathlib`, `shlex`, `subprocess`, `zoneinfo`。

## dataanalysis.py

历史汇总库：插值、B/C 比值、太阳调制、χ² 与 pickle 写入；与 data_processing 存在重复版本。

输入输出与限制：输入观测/模型数组或谱字典，返回插值/统计值；saveresults 显式写入 pickle。新流程优先 data_processing，以免版本口径混用。

示例（历史/实验代码须先修正依赖与路径，不在本任务中执行）：

```python
from dragon_utils.dataanalysis import chisquare
value = chisquare([1.0], [1.0], [0.1])
```

主要接口：`interp`, `interBCratio`, `chisquare`, `solmod`, `SM_output`, `loglog_interp`, `makesecflx`, `saveresults`。

实际导入：`bisect`, `dragon_utils`, `math`, `numpy`, `os`, `pickle`, `scipy`, `sys`, `time`。

## datareader.py

历史实验数据与 DRAGON/GALPROP 文本 reader；EtoR/RtoE/PPtoPN 转换。与 CALETana_functions/datareader.py 并非同一核素质量约定（本文件 He 使用 3.667）。

输入输出与限制：输入 basepath、相对实验表或明确模拟文件，输出能量/刚度索引字典。旧绝对默认路径不保证存在；本流程使用专门绘图 reader。

示例（历史/实验代码须先修正依赖与路径，不在本任务中执行）：

```python
from dragon_utils.datareader import readamsproflxvals
values = readamsproflxvals("/home/ljiayi/dragon_project/data/experiment_data/expdata/", convtoE=False)
```

主要接口：`EtoR`, `RtoE`, `PPtoPN`, `readcaltotflxvals`, `readcalICRCflxvals`, `readcalPRLflxvals`, `readcalPRL2flxvals`, `readcalYA2020flxvals`, `readcalYA2022flxvals`, `readcalYA2022bflxvals` 等（完整签名见源码）。

实际导入：`ROOT`, `math`, `os`, `pickle`, `sys`, `time`。

## readDRAGON.py

旧 DRAGON ASCII reader 与核素求和；BCratio 此版本只使用 C-12/13，与当前默认绘图的 C-14-inclusive 口径有差异。

输入输出与限制：输入 DRAGON 文件/输出路径/corrfact，返回谱字典与旧固定位置数组。默认路径、列顺序和归一化必须核实，不用于单轮默认绘图。

示例（历史/实验代码须先修正依赖与路径，不在本任务中执行）：

```python
from dragon_utils.readDRAGON import BCratio
ratio = BCratio(1.0, 2.0, 10.0, 5.0)
```

主要接口：`readDragonBKGautoSiP`, `BCratio`, `readDragonBKGauto`, `readDragonfileauto`。

实际导入：`math`, `os`, `sys`, `time`。

## xmltools.py

从多个历史任务汇总的 XML 修改片段，重复定义 generate_xml/prepare 等，最后定义覆盖前面的同名定义；部分函数依赖未定义的全局名。

输入输出与限制：没有可靠 CLI，不能当作完整自动生成器使用。输入/输出依片段而异，可能写 XML/source/diff/状态；新工作使用 xml_manager/xml_modifier.py 和 scripts/xml_batch.py。

示例（历史/实验代码须先修正依赖与路径，不在本任务中执行）：

```bash
sed -n '1,100p' /home/ljiayi/dragon_project/dragon_utils/xmltools.py
```

主要接口：`modify_xml`, `generate_xml`, `dimz_for_l`, `replace_unique_tag`, `generate_xml`, `replace_unique_tag`, `generate_xml`, `replace_tag_value`, `ensure_delta_z`, `generate_xml` 等（完整签名见源码）。

实际导入：。
