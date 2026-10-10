# common 代码说明

仅覆盖本目录直属代码。子目录见各自 README。历史工具的原有路径/命名未经本任务迁移；推荐 companion 单轮入口为项目 scripts/run_companion.py。示例说明实际接口，不表示历史优化/外部数据环境已通过运行验收。

## datafunc.py

历史共享 fitspectra 调用、pickle->DataFrame、插值点和权重/缩放工具。

输入输出与限制：输入外部 fitSpectra 路径、位置敏感 pickle 元组及配置，返回 X/y/scaler/失败表等；update_data 会执行外部脚本，无默认 CLI，包导入需目录在搜索路径。

示例（历史/实验代码须先修正依赖与路径，不在本任务中执行）：

```bash
cd /home/ljiayi/dragon_project/dragon_utils/prop/common
python3 -c "from datafunc import load_data, recenter_data"
```

主要接口：`update_data`, `load_data`, `load_interpolation_data`, `get_best_point`, `get_best_points`, `filter_points`, `get_expweights`, `get_distweights`, `recenter_data`。

实际导入：`collections`, `datetime`, `getpass`, `hyperopt`, `json`, `logging`, `numpy`, `os`, `pandas`, `pickle`, `random`, `re`, `scipy`, `sklearn`, `subprocess`, `sys`, `time`, `yaml`。

## plotPS.py

共享参数空间配对图、指定维度图与损失-距离绘图。

输入输出与限制：输入同目录 config.yaml 和拟合 pickle，输出指定 folder 下 ParameterSpace*.png/LossDistance*.png。裸导入 datafunc，路径依当前目录；旧正式图路径未迁移。

示例（历史/实验代码须先修正依赖与路径，不在本任务中执行）：

```bash
cd /home/ljiayi/dragon_project/dragon_utils/prop/common
python3 plotPS.py
```

主要接口：`load_config`, `get_distances`, `get_farthest_point`, `create_ParameterSpacePairplots`, `create_ParameterSpacePairplot`, `create_LossDistanceplot`, `main`。

实际导入：`collections`, `datafunc`, `datetime`, `getpass`, `hyperopt`, `json`, `logging`, `math`, `matplotlib`, `numpy`, `os`, `pandas`, `pickle`, `random`, `re`, `scipy`, `sklearn`, `subprocess`, `sys`, `time`, `yaml`。
