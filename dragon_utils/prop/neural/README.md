# neural 代码说明

仅覆盖本目录直属代码。子目录见各自 README。历史工具的原有路径/命名未经本任务迁移；推荐 companion 单轮入口为项目 scripts/run_companion.py。示例说明实际接口，不表示历史优化/外部数据环境已通过运行验收。

## neuralscan.py

较早的 TensorFlow 自动训练、随机候选提点、提交和等待循环。

输入输出与限制：读取 config.yaml、旧拟合 pickle，保存 NN 模型、ANN_RX_test_info 图和搜索数据；与 MarkovChain/neural.py 重复，外部提交/数据路径未验收。

示例（历史/实验代码须先修正依赖与路径，不在本任务中执行）：

```bash
cd /home/ljiayi/dragon_project/dragon_utils/prop/neural
python3 neuralscan.py
```

主要接口：`main`, `generate_saveFolderName`, `get_folderPrefix`, `get_folderID`, `load_config`, `load_data`, `closest_points`, `filter_points`, `get_best_point`, `getstringfromdict` 等（完整签名见源码）。

实际导入：`collections`, `datetime`, `getpass`, `glob`, `itertools`, `json`, `logging`, `math`, `matplotlib`, `numpy`, `os`, `pandas`, `pickle`, `random`, `re`, `sklearn`, `subprocess`, `sys`, `tensorflow`, `time`, `yaml`。

## neuraltest.py

较新的似然预测和谱->传播参数训练实验，支持多次训练与模型复用。

输入输出与限制：读取 config.yaml、谱/似然 pickle，输出 NN_data/NN_test、Keras 模型及 ANN 图；导入设置 mixed_float16，全局影响 TensorFlow 策略；百万候选循环可能耗时，非单轮入口。

示例（历史/实验代码须先修正依赖与路径，不在本任务中执行）：

```bash
cd /home/ljiayi/dragon_project/dragon_utils/prop/neural
python3 neuraltest.py
```

主要接口：`main`, `testparpredict`, `testlikepredict`, `generate_saveFolderName`, `get_folderPrefix`, `get_folderID`, `load_config`, `load_flux_data`, `load_like_data`, `closest_points` 等（完整签名见源码）。

实际导入：`collections`, `datetime`, `getpass`, `glob`, `itertools`, `json`, `logging`, `math`, `matplotlib`, `multiprocessing`, `numpy`, `os`, `pandas`, `pickle`, `random`, `re`, `sklearn`, `subprocess`, `sys`, `tensorflow`, `time`, `yaml`。
