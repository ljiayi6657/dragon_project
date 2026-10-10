# GradientDescent 代码说明

仅覆盖本目录直属代码。子目录见各自 README。历史工具的原有路径/命名未经本任务迁移；推荐 companion 单轮入口为项目 scripts/run_companion.py。示例说明实际接口，不表示历史优化/外部数据环境已通过运行验收。

## GD.py

历史局部/全局 Ridge 多项式或样条代理梯度搜索与自动模拟提交循环。

输入输出与限制：输入 config.yaml、fitspectra pickle 与外部 dragonbkg/fitSpectra；输出 DescentData/OldData/data.pkl/output.log 和模拟提交。部分路径仍 /home/motz，循环持续运行，不用于 companion 单轮。

示例（历史/实验代码须先修正依赖与路径，不在本任务中执行）：

```bash
cd /home/ljiayi/dragon_project/dragon_utils/prop/GradientDescent
python3 GD.py
```

主要接口：`load_config`, `update_data`, `load_data`, `load_interpolation_data`, `save_current_data`, `generate_saveFolderName`, `get_folderPrefix`, `get_folderID`, `load_previous_descentData`, `get_best_point` 等（完整签名见源码）。

实际导入：`collections`, `datetime`, `getpass`, `hyperopt`, `json`, `logging`, `numpy`, `os`, `pandas`, `pickle`, `random`, `re`, `scipy`, `sklearn`, `subprocess`, `sys`, `time`, `yaml`。

## plotPS.py

历史参数空间配对图及损失-距离图。

输入输出与限制：输入配置和 fitspectra pickle，输出配置运行目录 ParameterSpacePairplots-*.png 等；裸导入 common/datafunc，需满足 ../common 路径。正式图片路径尚未迁移。

示例（历史/实验代码须先修正依赖与路径，不在本任务中执行）：

```bash
cd /home/ljiayi/dragon_project/dragon_utils/prop/GradientDescent
python3 plotPS.py
```

主要接口：`load_config`, `get_distances`, `create_ParameterSpacePairplots`, `create_ParameterSpacePairplot`, `create_LossDistanceplot`, `main`。

实际导入：`GD`, `collections`, `datetime`, `getpass`, `hyperopt`, `json`, `logging`, `math`, `matplotlib`, `numpy`, `os`, `pandas`, `pickle`, `random`, `re`, `scipy`, `sklearn`, `subprocess`, `sys`, `time`, `yaml`。

## plot_descentData.py

历史下降轨迹/损失动量图与目录整理工具。

输入输出与限制：输入配置 progress_dir 与 data.pkl，输出运行目录 plots/trajectoryPairplots.png 等。含移动和递归删除旧目录逻辑，实际运行前必须检查路径和保留数据。

示例（历史/实验代码须先修正依赖与路径，不在本任务中执行）：

```bash
cd /home/ljiayi/dragon_project/dragon_utils/prop/GradientDescent
python3 plot_descentData.py
```

主要接口：`load_datapath`, `load_data`, `get_magnitudes`, `create_trajectoryPairplots`, `create_lossCurve`, `create_lossCurves`, `create_plots`, `main`。

实际导入：`getpass`, `math`, `matplotlib`, `numpy`, `os`, `pandas`, `pickle`, `re`, `sys`, `yaml`。

## start_GradientDescent.sh

旧虚拟环境启动包装；0 启动 GD.py，1 启动 submitGD.py。

输入输出与限制：固定 source /home/motz/CALETana/prop/.venv/bin/activate；未迁移环境和默认路径，仅记录原始调用方式。可能启动持续/批量计算。

示例（历史/实验代码须先修正依赖与路径，不在本任务中执行）：

```bash
cd /home/ljiayi/dragon_project/dragon_utils/prop/GradientDescent
bash start_GradientDescent.sh 0
```

## submitGD.py

历史参数组合批量提交，配置多组下降并分配 IP。

输入输出与限制：输入硬编码组合与配置，输出多份运行配置/外部启动命令；可能批量启动任务，配置和路径未验收，不是单轮流程。

示例（历史/实验代码须先修正依赖与路径，不在本任务中执行）：

```bash
cd /home/ljiayi/dragon_project/dragon_utils/prop/GradientDescent
python3 submitGD.py
```

主要接口：`load_config`, `get_configurations`, `iter_lowest_level`, `manage_execution`, `run_script`, `main`。

实际导入：`concurrent`, `copy`, `itertools`, `json`, `queue`, `subprocess`, `time`, `yaml`。
