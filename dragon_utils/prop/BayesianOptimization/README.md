# BayesianOptimization 代码说明

仅覆盖本目录直属代码。子目录见各自 README。历史工具的原有路径/命名未经本任务迁移；推荐 companion 单轮入口为项目 scripts/run_companion.py。示例说明实际接口，不表示历史优化/外部数据环境已通过运行验收。

## BayesOpt.py

当前 main 是本机 Task 2 的 1–2 轮有限贝叶斯接口，保留多段历史函数但不是旧 gp_minimize 常驻循环。

输入输出与限制：读取同目录 config.yaml 的 local 配置；--check 无模拟但写检查记录，--runs 1/2 执行本机模型，--resume 恢复指定已完成记录的评分。XML 在 data/processed/、结果/JSON 在 outputs/task2/ 和程序 output，日志依实际代码。样本仅检查表头，不评分。临时 bounds 非正式物理搜索范围，与 companion 单轮入口独立。

示例（历史/实验代码须先修正依赖与路径，不在本任务中执行）：

```bash
python3 dragon_utils/prop/BayesianOptimization/BayesOpt.py --check
python3 dragon_utils/prop/BayesianOptimization/BayesOpt.py --runs 1
```

主要接口：`update_data`, `load_data`, `top_results`, `closest_points`, `filter_points`, `get_distances`, `get_farthest_point`, `submit_task`, `determine_bounds`, `load_previous_data` 等（完整签名见源码）。

实际导入：`argparse`, `collections`, `csv`, `datetime`, `dragon_utils`, `getpass`, `hashlib`, `json`, `logging`, `numpy`, `os`, `pandas`, `pathlib`, `pickle`, `random`, `re`, `shutil`, `sklearn`, `skopt`, `subprocess`, `sys`, `time`, `uuid`, `yaml`。

## plot_progress.py

历史搜索轨迹和损失曲线绘图。

输入输出与限制：读取 config.yaml 的 paths.progress_dir 和历史 data.pkl（points/losses/bounds/init_X/init_y），输出历史运行目录 plots/*.png。当前 Task 2 JSON 不符合此格式，不能直接画其记录；旧路径需检查。

示例（历史/实验代码须先修正依赖与路径，不在本任务中执行）：

```bash
cd /home/ljiayi/dragon_project/dragon_utils/prop/BayesianOptimization
python3 plot_progress.py
```

主要接口：`load_datapath`, `load_data`, `get_magnitudes`, `top_results`, `create_trajectoryPairplots`, `create_lossCurve`, `create_plots`, `main`。

实际导入：`getpass`, `math`, `matplotlib`, `numpy`, `os`, `pandas`, `pickle`, `re`, `yaml`。

## start_BayesOpt.sh

当前包装器定位项目根目录，设置 PYTHONPATH 为 ~/.cache/dragon-task2deps 与项目根，并限制数值库线程为 1。

输入输出与限制：转发全部 CLI 参数到 BayesOpt.py，继承其输入输出与限制；依赖缓存包目录及系统 python，不使用旧 /home/motz 虚拟环境。

示例（历史/实验代码须先修正依赖与路径，不在本任务中执行）：

```bash
bash dragon_utils/prop/BayesianOptimization/start_BayesOpt.sh --check
```
