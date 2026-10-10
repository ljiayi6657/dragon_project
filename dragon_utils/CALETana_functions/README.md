# CALETana_functions 代码说明

仅覆盖本目录直属代码。子目录见各自 README。历史工具的原有路径/命名未经本任务迁移；推荐 companion 单轮入口为项目 scripts/run_companion.py。示例说明实际接口，不表示历史优化/外部数据环境已通过运行验收。

## datareader.p2

历史保存/编辑备份，内容对应同名 Python 模块的较旧版本；不作为推荐入口，不自动删除。仅供文本比较，输入输出及依赖以对应版本内容为准，不能用它替代当前 .py。

```bash
less /home/ljiayi/dragon_project/dragon_utils/CALETana_functions/datareader.p2
```

## datareader.py

CALET/AMS/PAMELA 等本地实验表 reader 与单位转换；He 核素约定为 A=4，不能替代当前显式 He-3/4 混合谱处理。

输入输出与限制：输入 basepath 和选项，返回按能量/刚度索引的字典。只读取本地文件；旧 DRAGON/GALPROP 默认绝对路径须检查，不提供稳定 CLI。

示例（历史/实验代码须先修正依赖与路径，不在本任务中执行）：

```python
from dragon_utils.CALETana_functions.datareader import readamsproflxvals
values = readamsproflxvals("/home/ljiayi/dragon_project/data/experiment_data/expdata/", convtoE=False)
```

主要接口：`EtoR`, `RtoE`, `PPtoPN`, `readcaltotflxvals`, `readcalICRCflxvals`, `readcalPRLflxvals`, `readcalPRL2flxvals`, `readcalYA2020flxvals`, `readcalYA2022flxvals`, `readcalYA2022bflxvals` 等（完整签名见源码）。

实际导入：`ROOT`, `math`, `os`, `pickle`, `sys`, `time`。

## datareader.py~

历史保存/编辑备份，内容对应同名 Python 模块的较旧版本；不作为推荐入口，不自动删除。仅供文本比较，输入输出及依赖以对应版本内容为准，不能用它替代当前 .py。

```bash
less /home/ljiayi/dragon_project/dragon_utils/CALETana_functions/datareader.py~
```

## fluxfunctions.p2

历史保存/编辑备份，内容对应同名 Python 模块的较旧版本；不作为推荐入口，不自动删除。仅供文本比较，输入输出及依赖以对应版本内容为准，不能用它替代当前 .py。

```bash
less /home/ljiayi/dragon_project/dragon_utils/CALETana_functions/fluxfunctions.p2
```

## fluxfunctions.py

历史 BEA 电子/正电子背景和点源模型函数集合。

输入输出与限制：输入能量、模型参数及可选谱数据，返回通量/比例；用同目录裸导入 datareader，需该目录在 Python 搜索路径。不是本轮 p/He 核素绘图接口。

示例（历史/实验代码须先修正依赖与路径，不在本任务中执行）：

```bash
cd /home/ljiayi/dragon_project/dragon_utils/CALETana_functions
python3 -c "import fluxfunctions; print(fluxfunctions.BEAparamnames)"
```

主要接口：`BEAeleflx`, `BEAposflx`, `BEAbkgposflx`, `BEAposfrac`, `BEAtotflx`, `BEAbkgtotflx`, `BEAbkgeleflx`, `BEAbkgposfrac`, `bkgfunc`, `bkgeleflx` 等（完整签名见源码）。

实际导入：`datareader`, `glob`, `math`, `matplotlib`, `numpy`, `os`, `pylab`, `socket`, `sys`, `time`。

## plotfunctions.p2

历史保存/编辑备份，内容对应同名 Python 模块的较旧版本；不作为推荐入口，不自动删除。仅供文本比较，输入输出及依赖以对应版本内容为准，不能用它替代当前 .py。

```bash
less /home/ljiayi/dragon_project/dragon_utils/CALETana_functions/plotfunctions.p2
```

## plotfunctions.py

历史实验谱和 DRAGON 谱作图函数集合，plotamsproflux 等在现有 Matplotlib 图上添加曲线。

输入输出与限制：输入 figure、basepath、实验字典、谱及调制选项，返回 artist/曲线数据。依赖同目录裸导入 datareader/fluxfunctions；函数多数不负责保存，调用者使用 outputs/figures/ 规范路径。

示例（历史/实验代码须先修正依赖与路径，不在本任务中执行）：

```bash
cd /home/ljiayi/dragon_project/dragon_utils/CALETana_functions
python3 -c "import plotfunctions"
```

主要接口：`plotcaltotflux`, `plotcalICRCflux`, `plotcalPRLflux`, `plotcalPRL2flux`, `plotcalYA2020flux`, `plotcalYA2022flux`, `plotcalYA2022bflux`, `plotcalYA2022fflux`, `plotcalYA2023flux`, `plotcalYA2025flux` 等（完整签名见源码）。

实际导入：`datareader`, `fluxfunctions`, `glob`, `math`, `matplotlib`, `numpy`, `os`, `pylab`, `socket`, `sys`, `time`。

## plotfunctions.py~

历史保存/编辑备份，内容对应同名 Python 模块的较旧版本；不作为推荐入口，不自动删除。仅供文本比较，输入输出及依赖以对应版本内容为准，不能用它替代当前 .py。

```bash
less /home/ljiayi/dragon_project/dragon_utils/CALETana_functions/plotfunctions.py~
```

## propfunctions.py

点源电子能量损失、扩散和注入谱的历史计算库；initpropmod/initeloss 必须先初始化。

输入输出与限制：输入传播配置、能量/年龄/距离/注入参数，返回损失或点源谱。传播配置在 initpropmod 内硬编码，loadresults 可读外部 pickle；状态通过全局变量共享，不能当核素传播入口。

示例（历史/实验代码须先修正依赖与路径，不在本任务中执行）：

```python
from dragon_utils.CALETana_functions import propfunctions as pf
pf.initpropmod("C1ZDLB")
pf.initeloss(True, True)
```

主要接口：`loadresults`, `initpropmod`, `initeloss`, `Eloss`, `Einitial`, `Einitialss`, `rdiffKN`, `rdiffKNss`, `breakinjectspec`, `breakinjectspecarr` 等（完整签名见源码）。

实际导入：`bisect`, `math`, `numpy`, `os`, `pickle`, `sys`, `time`。

## pulsdict-old.py

静态脉冲星字典（pulsdict），记录 age、dist、Etot、name/color 等；无 CLI、输入文件或生成输出，使用 Python 标准库即可。不同文件为历史配置，不能随意互换。

```python
# Load this legacy file with runpy.run_path(path).
```

主要接口：`pulsdict` 静态数据。

实际导入：。

## readDRAGON.py

历史 DRAGON ASCII reader；该副本 BCratio 可包含 C-14，与根目录副本签名不同。

输入输出与限制：输入模拟文件、目录、corrfact 等，返回旧字典/数组；字段顺序和归一化依旧版本，不作为当前单轮默认 reader。

示例（历史/实验代码须先修正依赖与路径，不在本任务中执行）：

```python
from dragon_utils.CALETana_functions.readDRAGON import BCratio
ratio = BCratio(1.0, 2.0, 10.0, 5.0, 1.0)
```

主要接口：`readDragonBKGautoSiP`, `BCratio`, `readDragonBKGauto`, `readDragonfileauto`。

实际导入：`math`, `os`, `sys`, `time`。

## rigconvtest.py

刚度/每核子动能换算实验，rig/ekin；顶层直接打印 B 核素 E=50 的换算。

输入输出与限制：无 CLI 参数，输出终端数值；历史质量/单位约定需单独核实，不用于验证新流程物理处理。

示例（历史/实验代码须先修正依赖与路径，不在本任务中执行）：

```bash
cd /home/ljiayi/dragon_project/dragon_utils/CALETana_functions
python3 rigconvtest.py
```

主要接口：`rig`, `ekin`。

实际导入：`datetime`, `glob`, `math`, `os`, `random`, `sys`, `time`。

## testprop.py

点源谱标量/数组计算的绘图与性能实验；main 调用 initpropmod("C1ZDLB") 和 initeloss。

输入输出与限制：输入硬编码 ages/gams/cuts，输出旧 ../astro/pulsplot/testplot-*.png。需外部传播数据及目录，可能耗时；本次只整理文档，正式使用前须另行调整输出路径。

示例（历史/实验代码须先修正依赖与路径，不在本任务中执行）：

```bash
cd /home/ljiayi/dragon_project/dragon_utils/CALETana_functions
python3 testprop.py
```

主要接口：`main`, `plotpulsnew`, `plotpulsarr`, `pulsarspecnew`, `pulsarspecarr`。

实际导入：`math`, `matplotlib`, `numpy`, `os`, `propfunctions`, `sys`, `time`。
