# data_processing 代码说明

仅覆盖本目录直属代码。子目录见各自 README。历史工具的原有路径/命名未经本任务迁移；推荐 companion 单轮入口为项目 scripts/run_companion.py。示例说明实际接口，不表示历史优化/外部数据环境已通过运行验收。

## flux.py

interp 返回 linear/cubic 插值闭包；支持 logx/logy，验证一维有限数组和严格递增 x。

输入输出与限制：输入数组和插值模式，返回 callable，不写文件。默认禁止外推；log 模式要求正值，cubic 需足够采样点。

示例（历史/实验代码须先修正依赖与路径，不在本任务中执行）：

```python
from dragon_utils.data_processing.flux import interp
value = interp([1, 2], [2, 4], "linear")(1.5)
```

主要接口：`interp`。

实际导入：`math`, `numpy`, `os`, `pickle`, `scipy`, `sys`, `time`。

## physics.py

solmod 与 SM_output 实现现有 force-field 调制。后者 log-log LIS 插值，按 Z/A 移动能量并乘调制因子。

输入输出与限制：输入 GeV/n 能量、LIS 谱、PhiP(GV)、每核子质量、Z/A；输出能量和 TOA 数组，不写文件。默认禁止 LIS 外推，正值/单位需由调用者保持。

示例（历史/实验代码须先修正依赖与路径，不在本任务中执行）：

```python
from dragon_utils.data_processing.physics import SM_output
energy, toa = SM_output([1, 2, 4], [3, 2, 1], output_energies=[1], charge=1, massnum=1)
```

主要接口：`solmod`, `SM_output`。

实际导入：`numpy`, `scipy`。

## statistic_analysis.py

chisquare 支持对角误差或协方差，dof 可给约化 χ²，return_points 可返回贡献/残差等细节。

输入输出与限制：输入匹配形状的观测/期望/误差，输出原始 χ²、指定 dof 下的约化值或细节字典。协方差必须正定且与误差一致；本流程不改变统计口径。

示例（历史/实验代码须先修正依赖与路径，不在本任务中执行）：

```python
from dragon_utils.data_processing.statistic_analysis import chisquare
value = chisquare([1, 2], [1, 2], [0.1, 0.2])
```

主要接口：`chisquare`。

实际导入：`numpy`。
