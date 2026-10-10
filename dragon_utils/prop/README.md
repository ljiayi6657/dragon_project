# DRAGON propagation optimization tools

本目录保存了一组围绕 DRAGON/DRAGON2 传播模型拟合结果构建的优化、代理模型、可视化和太阳调制工具。历史代码主要读取 `fitspectra` 生成的 pickle 数据，整理为参数表和损失表，再使用梯度下降、贝叶斯优化、Markov Chain 或神经网络提出新的模拟参数。

> 原审查日期：2026-08-24；2026-10-10 已重新核查入口并补充各目录 README。本文档基于当前目录中的 15 个 Python 文件、10 个 Jupyter Notebook、配置与启动脚本整理。`HelModArchives/`、`NN_data/`、模型文件和图像等大型数据资产只按结构检查，没有逐个解析二进制内容。

## 目录概览

| 路径 | 作用 | 主要入口 |
| --- | --- | --- |
| `common/` | 通用数据加载、插值数据处理、缩放、筛选、权重和参数空间绘图 | `datafunc.py`、`plotPS.py` |
| `GradientDescent/` | 用局部/全局 Ridge 多项式或样条代理模型计算梯度并提交新模拟 | `GD.py` |
| `BayesianOptimization/` | 使用 `skopt.gp_minimize` 在缩放后的参数空间内提出新点 | `BayesOpt.py` |
| `MarkovChain/` | 随机步进、接受概率和可选神经网络辅助的参数搜索 | `MC.py` |
| `neural/` | 似然预测、参数预测、候选点生成和神经网络实验 | `neuraltest.py`、`neuralscan.py` |
| `GeneralOverview/` | 数据集检查、可视化、切分和 PyTorch 数据集准备 | `0_CreateDatasets.ipynb` |
| `MLModelFits/` | 多项式、随机森林、XGBoost、神经网络、贝叶斯搜索和梯度搜索实验 | `0_...` 至 `6_...` notebooks |
| `ComparisonPlots/` | 比较优化运行的损失曲线并生成热图 | 两个 notebooks |
| `helmod/` | HelMod 4.1 离线太阳调制模块及模拟归档 | `HelMod_OfflineModule.py` |
| `requirements.txt` | 当前环境的冻结依赖列表 | `pip install -r requirements.txt` |

当前目录约 21 GB，其中 `.venv/` 约 11 GB、`neural/` 约 7.6 GB、`helmod/` 约 1.7 GB。大部分空间来自虚拟环境、HelMod `.npz` 归档、训练模型和历史运行数据，不是源代码。

## 总体数据流

1. `fitspectra-*.py` 将 DRAGON 模拟与实验数据的拟合结果保存为 pickle 元组。
2. 各优化模块从 `globpardict` 构造参数 DataFrame，并从选定的损失数组构造 `Y` 列。
3. 无穷值、NaN、失败模拟、固定参数和可选插值点被过滤或赋予替代损失。
4. 参数 `X` 与损失 `y` 通过 scikit-learn scaler 标准化。
5. 优化器或神经网络提出一个新参数点。
6. `submit_task` 重写外部 `dragonbkg` 文件中的 `#Autoconfigblock`，随后提交 DRAGON 模拟。
7. 主循环定期重新运行 `fitspectra`，检查新模拟是否完成；实现了持久化的模块会将进度保存为 `data.pkl` 与 `output.log`。

### 核心表结构

优化代码普遍使用以下 DataFrame 约定：

| 对象 | 含义 |
| --- | --- |
| `X_data` | 原始传播参数，每行是一组模拟参数 |
| `y_data` | 原始目标值，列名通常为 `Y` |
| `X_scaled`、`y_scaled` | 经 `StandardScaler` 或 `RobustScaler` 处理的表 |
| `w_data` | 拟合权重，列名为 `W` |
| `isintpol` | 是否为插值数据，列名为 `iI` |
| `faultdata` / `X_fault` | 失败、NaN 或无穷结果对应的参数 |
| `hash_data` | Markov Chain 使用的模拟哈希 |

输入 pickle 采用位置敏感的长元组格式，并且不同脚本期望的字段数量和顺序并不完全一致。必须使用与脚本版本匹配的 `fitspectra` 输出；不匹配时可能在解包阶段直接失败，或更危险地发生字段错位。

## 子目录入口

各目录直属文件的用途、接口、调用和限制见相应子目录唯一 README。BayesianOptimization 当前 main 是本机 Task 2 的 1–2 轮接口，使用 skopt.Optimizer；历史 gp_minimize/常驻任务说明不再适用于该入口。其他优化循环仍保留旧外部提交依赖。

## 环境与运行前检查

建议使用 Python 3.10。目录内已有 `.venv/`，但它占用约 11 GB，GradientDescent/MarkovChain 启动脚本仍固定激活 `/home/motz/CALETana/prop/.venv`；当前 start_BayesOpt.sh 使用项目根目录与 ~/.cache/dragon-task2deps。

```bash
cd /home/ljiayi/dragon_project/dragon_utils/prop
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`requirements.txt` 并未覆盖代码实际使用的全部包。按所运行模块，可能还需要：

- TensorFlow：`neural/` 与 Markov Chain 的 NN 辅助；
- Astropy：HelMod FITS 输入；
- XGBoost：`MLModelFits/3_XGBoostDT.ipynb`；
- `bayesian-optimization`：`MLModelFits/5_BayesianSearch.ipynb`；
- Jupyter：运行 notebooks。

运行优化脚本之前，至少检查以下事项：

1. 对应子目录的 `config.yaml` 中仍有 `/home/motz/...` 和少量 `/home/ehanser/...` 旧路径，必须指向本机实际文件。
2. `fitSpectra_path` 和 `dragonbkg_path` 是外部依赖，本目录不包含这些脚本。
3. `submit_task` 会直接改写外部 `dragonbkg` 文件并提交任务；不要把 `simulation_IP` 误设为生产机器。
4. 从相应子目录启动脚本，因为部分导入和相对路径依赖当前工作目录。
5. 不要在不了解内容时加载不可信 pickle；pickle 反序列化可执行任意代码。

历史配置修正后的典型入口如下；当前 BayesOpt 接口以其子目录 README 为准：

```bash
cd GradientDescent && python GD.py
python BayesianOptimization/BayesOpt.py --check
cd MarkovChain && python MC.py
cd neural && python neuraltest.py
```

## pandas DataFrame 效率审查

### 结论

不能通过“把整个项目更新成 pandas DataFrame”获得普遍加速。优化、神经网络和 notebook 的表格型数据已经大量使用 DataFrame；scikit-learn 与 TensorFlow 最终仍会把这些数据转换为 NumPy 数组或张量。对于纯数值密集循环，继续增加 DataFrame 包装往往会增加索引、类型和复制开销。

更合适的边界是：

- 用 DataFrame 管理带列名的模拟参数、损失、权重、筛选和绘图数据；
- 用 NumPy 数组或 TensorFlow/PyTorch 张量完成大批量随机采样、距离、插值、矩阵乘法和模型训练；
- 只在模块边界将数值结果包装回 DataFrame，以保留列名。

### 值得调整的区域

| 优先级 | 位置 | 当前模式 | 建议方向 | 预期影响 |
| --- | --- | --- | --- | --- |
| 高 | `neural/neuralscan.py:442`、`neural/neuraltest.py:978` | Python 双层列表推导生成约一百万个随机点，再构造 DataFrame | 用 NumPy 随机数组一次生成候选，模型预测时直接传 ndarray；最终候选再转为单行 DataFrame | 很可能显著降低生成时间与峰值内存；这不是 pandas 改造，而是 NumPy 向量化 |
| 高 | `helmod/HelMod_OfflineModule.py:860-871` | 对探测能量和 LIS 能量执行双重 Python 循环 | 将主要累加写成边界分布矩阵与谱向量的矩阵乘法；仅保留少 bin 特殊处理 | 可能显著加速 HelMod 调制；DataFrame 不适合此数值核 |
| 中高 | `neural/neuraltest.py:291-310` | 对能量列和每行谱数组执行多层列表推导，再拼接多个 DataFrame | 先把谱堆叠为规则 ndarray，广播计算通量、比值和谱指数，最后一次构造带列名 DataFrame | 对大能谱表可明显减少 Python 循环和中间对象 |
| 中 | `GradientDescent/GD.py`、`BayesianOptimization/BayesOpt.py`、`MarkovChain/MC.py` | 历史轨迹保存为“单行 DataFrame 的列表”加独立损失列表 | 若后续重构，可采用一个按 step 索引的轨迹 DataFrame，并为 loss、status、hash 增加列 | 改善内存、序列化和绘图流程；对 DRAGON 总运行时间影响有限 |
| 低至中 | 多个 `filter_points` / `filter_data` | 对每个固定参数逐次 `drop` 并反复复制/重置索引 | 仍保留 DataFrame，但一次构造组合布尔 mask 后单次筛选 | 参数表很大或固定列很多时减少复制；通常不是主瓶颈 |
| 低 | `MarkovChain/MC.py:55-58` | 循环将文件名映射到 hash 列 | 可用 `Series(foundfiles).map(hashdict)` 或列表推导 | 代码更紧凑，速度收益通常很小 |

### 不建议改成 DataFrame 的区域

- `HelMod_OfflineModule.py` 中 `ParticleFlux[Z][A][K]` 是“核素层级 + 多条数值数组”的非规则结构，嵌套字典比单个宽表自然。
- `.npz` 中的边界分布是密集数值矩阵，NumPy 矩阵运算比 DataFrame 更合适。
- `Rigidity`、`Energy`、`beta_` 和通量单位转换都是逐元素数值函数，应直接支持 ndarray 广播。
- Keras、PyTorch 和 scikit-learn 的训练数据应在训练边界转为 ndarray/tensor，避免在迭代内部频繁创建 DataFrame。
- `np.loadtxt` 读取 HelMod 的固定宽度纯数值文件已经合适；改用 `pandas.read_csv` 可增加列名可读性，但不保证更快或更省内存。
- 绘图代码中的维度循环数量很小，改为 DataFrame 操作不会带来实质收益。

### 建议实施顺序

若未来允许修改代码，推荐按以下顺序做基准测试后再改造：

1. 向量化百万随机候选生成，并分块预测以控制峰值内存。
2. 将 HelMod `Spectra` 的主双重循环改为 NumPy 矩阵运算。
3. 向量化神经网络能谱特征构造。
4. 统一共享的数据加载器，消除多个版本的长元组解包和重复清洗逻辑。
5. 最后再评估是否把运行历史统一为单一 DataFrame。

应分别记录数据加载、候选生成、模型预测、HelMod 调制与完整 DRAGON 周期的耗时。由于 DRAGON 模拟本身通常远慢于本地表操作，DataFrame 层面的微小优化未必能改变端到端时间。

## 已知兼容性与维护风险

- `HelMod_OfflineModule.py:1377` 和 `:1380` 使用已从 NumPy 1.24 移除的 `np.float`；当前 `requirements.txt` 固定 NumPy 1.26.4，执行对应实验数据绘图分支会失败。
- 三个主优化模块及神经网络目录各自保留了相似的数据加载、过滤、提交与等待代码，修复时容易出现版本漂移。
- `MarkovChain/neural.py` 与 `neural/neuralscan.py` 完全重复；两个 `plot_progress.py` 也完全重复。
- 多处使用 `shell=True`、字符串拼接命令和直接改写外部脚本，输入路径和参数必须视为可信。
- 多个等待循环一次等待 300 秒，外部程序没有产生预期提示时还可能进入更长的重试周期。
- 原审查中的 Python 源文件均可被 Python AST 解析；HelMod 中有三处正则字符串触发无效转义 `SyntaxWarning`，但不是语法错误。

## 本次审查范围

2026-10-10 此 prop 子树只更新/新增文档，未修改或运行其 Python、Shell、YAML、Notebook、模型与优化循环。当前 companion 实现与构建验证在项目其他目录独立进行。


## neuraltest.py

旧 TensorFlow 训练/参数空间原型，含 chisquarepredict/reeval/getrandommodel 和多个示例。

输入输出与限制：输入旧 ../../astro/CALplots/ pickle，输出模型/预测/保存结果；没有稳定 CLI，数据与训练参数硬编码，导入也打印 TensorFlow 版本。实验代码，非 companion 入口。

示例（历史/实验代码须先修正依赖与路径，不在本任务中执行）：

```bash
cd /home/ljiayi/dragon_project/dragon_utils/prop
python3 neuraltest.py
```

主要接口：`main`, `chisquarepredict`, `reeval`, `getrandommodel`, `example3`, `example2`, `example1`, `dataframe_to_dataset`, `encode_numerical_feature`, `encode_categorical_feature` 等（完整签名见源码）。

实际导入：`datetime`, `glob`, `math`, `numpy`, `os`, `pandas`, `pickle`, `pickle5`, `random`, `sklearn`, `sys`, `tensorflow`, `time`。
