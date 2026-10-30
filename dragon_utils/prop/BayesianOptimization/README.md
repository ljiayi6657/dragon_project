# BayesianOptimization 代码说明

仅覆盖本目录直属代码。子目录见各自 README。历史工具的原有路径/命名未经本任务迁移；推荐 companion 单轮入口为项目 scripts/run_companion.py。示例说明实际接口，不表示历史优化/外部数据环境已通过运行验收。

## BayesOpt.py

当前 main 是四参数远程贝叶斯接口，搜索 `D0`、`deltaA`、`deltaB`、`deltaZ`，四维均为线性空间。正式边界依次为 `D0=[2.5, 3.0]`、`deltaA=[0, 0.05]`、`deltaB=[0.01, 0.35]`、`deltaZ=[0.1, 0.3]`。基准输入固定为 `data/processed/2026-10-28_BayesianOptimization_O.xml`，当前起点为 `D0=2.6`、`deltaA=0`、`deltaB=0.01`、`deltaZ=0.2`；候选把 `DiffusionThreshold=8.3`、`DiffusionThresholdZ=0` 固定且只使用 `Zmax=8`。候选名为 `YYYY-MM-DD_BayesOpt_D<值>_dA<值>_dB<值>_dZ<值>`，XML 与同名丰度表保存在 `data/processed/`。

输入输出与限制：读取同目录 `config.yaml` 的 `search` 配置。`--check` 只生成并检查两台主机的本地候选记录；`--test` 在 companion 与 yellowgiant 各运行一次相同起点，等两边均完成、回传和评分后停止，不提出下一批；`--resume-test` 只从两台主机已有且 token 匹配的本轮状态续取、评分和作图，绝不重新启动 DRAGON；正式搜索使用偶数 `--calls N`，每批各主机一个候选，两边都完成后才调用优化器更新。正式范围读取上述四组线性边界，起点必须位于边界内。

每个 Z=8 ASCII 谱按 `data/2026-10-28_z14-z8-coefficient.csv` 的相同能量和列逐点相乘，得到带主机后缀的 `-z14.txt`；只有 Z=14 预测进入固定 0.64 GV 太阳调制和 p、He、B/C χ²。每个成功候选都生成 `BCfitting`、`pHefitting27` 两张图。原始 TXT/FITS 在 `data/dragon_output/`，图片在 `outputs/figures/`，残差和总表在 `outputs/csv/`，详细记录在 `outputs/bayes/`，全部保留候选主体并以主机后缀区分交叉测试。优化总表为 `YYYY-MM-DD_BayesOpt.csv`。

远程接口使用 SSH alias `companion` 与 `yellowgiant`，程序目录均为 `/home/ljiayi/dragon/DRAGON2-Beta_version-master`，编译线程分别为 48 与 32。任务复用 `scripts/run_companion.py` 的断线存活 worker 和哈希状态；不设置 Python 侧的联合 `delta` 上限约束，DRAGON2 自身仍可拒绝无效输入。包装器把正式搜索主控放入固定 session `BayesOpt`；companion 与 yellowgiant 日志分别使用固定 session `companion_log`、`yellowgiant_log`。三个 session 都只使用各自的单一窗口；新批次通过 `respawn-pane` 在原窗格替换日志跟随命令并清空旧历史，不新建窗口。

示例：

```bash
python3 dragon_utils/prop/BayesianOptimization/BayesOpt.py --check
python3 dragon_utils/prop/BayesianOptimization/BayesOpt.py --test
python3 dragon_utils/prop/BayesianOptimization/BayesOpt.py --resume-test
bash dragon_utils/prop/BayesianOptimization/start_BayesOpt.sh --calls 100
tmux attach -t BayesOpt
tmux attach -t companion_log
tmux attach -t yellowgiant_log
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

当前包装器定位项目根目录，设置 PYTHONPATH 为 `~/.cache/dragon-task2deps` 与项目根，并限制优化器数值库线程为 1。回传数据校验与绘图子进程会清除该缓存路径，使用与系统 Matplotlib 匹配的 NumPy。正式 `--calls N` 自动进入固定 `BayesOpt:main.0`；运行中的同名主控不会被覆盖，已退出的固定窗格可由下一次正式启动复用。

输入输出与限制：转发全部 CLI 参数到 BayesOpt.py，继承其输入输出与限制；依赖缓存包目录及系统 python，不使用旧 /home/motz 虚拟环境。

示例（历史/实验代码须先修正依赖与路径，不在本任务中执行）：

```bash
bash dragon_utils/prop/BayesianOptimization/start_BayesOpt.sh --check
bash dragon_utils/prop/BayesianOptimization/start_BayesOpt.sh --test
bash dragon_utils/prop/BayesianOptimization/start_BayesOpt.sh --resume-test
bash dragon_utils/prop/BayesianOptimization/start_BayesOpt.sh --calls 100
```
