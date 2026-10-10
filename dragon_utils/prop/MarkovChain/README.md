# MarkovChain 代码说明

仅覆盖本目录直属代码。子目录见各自 README。历史工具的原有路径/命名未经本任务迁移；推荐 companion 单轮入口为项目 scripts/run_companion.py。示例说明实际接口，不表示历史优化/外部数据环境已通过运行验收。

## MC.py

历史随机参数步进和可选 NN 辅助的自动提交。

输入输出与限制：读取 config.yaml/旧 fitspectra pickle/外部提交器，写 MCData/运行日志并提交模拟。load_previous 分支调用未定义 load_previous_descentData；save_current_data 未在主循环稳定使用，不可依赖恢复格式。

示例（历史/实验代码须先修正依赖与路径，不在本任务中执行）：

```bash
cd /home/ljiayi/dragon_project/dragon_utils/prop/MarkovChain
python3 MC.py
```

主要接口：`mute`, `load_data`, `top_results`, `closest_points`, `filter_points`, `filter_data`, `get_distances`, `get_farthest_point`, `submit_task`, `load_previous_data` 等（完整签名见源码）。

实际导入：`collections`, `datafunc`, `datetime`, `getpass`, `io`, `joblib`, `logging`, `math`, `multiprocessing`, `numpy`, `os`, `pandas`, `pickle`, `random`, `re`, `scipy`, `sklearn`, `skopt`, `subprocess`, `sys`, `tensorflow`, `time`, `yaml`。

## neural.py

神经网络自动训练/提点实验副本，当前与 neural/neuralscan.py 相同。

输入输出与限制：读取当前目录 config.yaml 及旧 pickle，输出模型、ANN 图、候选与提交记录；有外部路径依赖，不是独立稳定的 Markov 恢复接口。

示例（历史/实验代码须先修正依赖与路径，不在本任务中执行）：

```bash
cd /home/ljiayi/dragon_project/dragon_utils/prop/MarkovChain
python3 neural.py
```

主要接口：`main`, `generate_saveFolderName`, `get_folderPrefix`, `get_folderID`, `load_config`, `load_data`, `closest_points`, `filter_points`, `get_best_point`, `getstringfromdict` 等（完整签名见源码）。

实际导入：`collections`, `datetime`, `getpass`, `glob`, `itertools`, `json`, `logging`, `math`, `matplotlib`, `numpy`, `os`, `pandas`, `pickle`, `random`, `re`, `sklearn`, `subprocess`, `sys`, `tensorflow`, `time`, `yaml`。

## plot_progress.py

与 BayesianOptimization/plot_progress.py 相同的历史图脚本副本。

输入输出与限制：仍使用 BayesianOptimization 配置与 points/losses/bounds/init_X/init_y 结构，输出历史 plots/*.png；MC 当前持久化无法稳定提供该结构，不能直接保证兼容。

示例（历史/实验代码须先修正依赖与路径，不在本任务中执行）：

```bash
cd /home/ljiayi/dragon_project/dragon_utils/prop/MarkovChain
python3 plot_progress.py
```

主要接口：`load_datapath`, `load_data`, `get_magnitudes`, `top_results`, `create_trajectoryPairplots`, `create_lossCurve`, `create_plots`, `main`。

实际导入：`getpass`, `math`, `matplotlib`, `numpy`, `os`, `pandas`, `pickle`, `re`, `yaml`。

## start_MC.sh

历史启动器激活固定虚拟环境后运行 MC.py。

输入输出与限制：输入硬编码 /home/motz/CALETana/prop/.venv 和 config.yaml，输出继承 MC；无参数接口，环境须先迁移。

示例（历史/实验代码须先修正依赖与路径，不在本任务中执行）：

```bash
cd /home/ljiayi/dragon_project/dragon_utils/prop/MarkovChain
bash start_MC.sh
```
