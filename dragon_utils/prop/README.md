# DRAGON propagation optimization tools

本目录保存了一组围绕 DRAGON/DRAGON2 传播模型拟合结果构建的优化、代理模型、可视化和太阳调制工具。代码主要读取 `fitspectra` 生成的 pickle 数据，整理为参数表和损失表，再使用梯度下降、贝叶斯优化、Markov Chain 或神经网络提出新的模拟参数。

> 审查日期：2026-08-24。本文档基于当前目录中的 15 个 Python 文件、10 个 Jupyter Notebook、配置与启动脚本整理。`HelModArchives/`、`NN_data/`、模型文件和图像等大型数据资产只按结构检查，没有逐个解析二进制内容。

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

## 各模块说明

### `common/`

`datafunc.py` 提供当前最接近共享实现的数据入口，包括：

- 运行外部 `fitspectra` 并处理交互提示；
- 将模拟字典和选定损失转换为 DataFrame；
- 合并插值点并计算插值权重；
- 处理 NaN、无穷值和失败模拟；
- 固定参数筛选、标准化、最佳点选择及距离/指数权重。

`plotPS.py` 读取 `common/config.yaml`，生成参数空间配对图和损失—距离图。

### `GradientDescent/`

`GD.py` 的主循环会拟合局部或全局 Ridge 代理模型，然后通过数值或解析梯度生成下一参数点。支持：

- Polynomial 或 Spline 特征；
- Manual 或 Hyperopt 自动选择超参数；
- Normal、Nesterov 或自动步长；
- Exponential、Distance 或无额外权重；
- 失败模拟后的半步回退；
- 继续历史运行与自动重启。

`submitGD.py` 用参数网格生成多组配置，并把任务分配到多个 IP。`plot_descentData.py` 和 `plotPS.py` 用于运行轨迹与参数空间检查。

注意：`plot_descentData.py` 包含移动和递归删除历史目录的逻辑。运行前应备份数据并确认 `progress_dir` 指向正确目录。

### `BayesianOptimization/`

`BayesOpt.py` 读取历史模拟，在最佳点附近确定边界，然后使用 Gaussian Process 和 Expected Improvement 提出新点。每次目标函数调用都会提交模拟、等待拟合结果并更新 `data.pkl`。

`plot_progress.py` 读取保存的 `points`、`losses`、`bounds`、`init_X` 和 `init_y`，绘制搜索轨迹与损失曲线。

### `MarkovChain/`

`MC.py` 从最佳点、较远优质点或指定哈希开始随机步进。较差点是否接受由损失比、距离条件和随机数共同决定。启用 `NN_assist` 时，会训练 TensorFlow 代理模型并从随机候选中选取预测损失最低的点。

当前实现存在以下恢复、持久化和绘图问题：

- `MC.py` 调用了未定义的 `load_previous_descentData`，因此 `load_previous: true` 路径不可直接使用。
- `MC.py` 虽定义了 `save_current_data`，但主循环没有调用它，当前运行不会按该函数的格式持续写入搜索进度。
- `MarkovChain/plot_progress.py` 与 `BayesianOptimization/plot_progress.py` 内容完全相同，仍读取 BayesianOptimization 配置，并假定存在 Markov Chain 当前保存格式没有稳定提供的 `bounds`、`init_X` 和 `init_y`。

`MarkovChain/neural.py` 与 `neural/neuralscan.py` 当前字节级完全相同，属于重复副本。

### `neural/`

`neuraltest.py` 同时包含两类任务：

- 从参数预测似然；
- 从能谱及谱指数特征反推传播参数。

它还包含多次训练、残差分布绘图、模型复用检查以及大规模随机候选搜索。`neuralscan.py` 是较早的自动训练—提点—提交循环。根目录的 `neuraltest.py` 则是更早的 TensorFlow 原型和示例集合，使用相对数据路径，不应与 `neural/neuraltest.py` 混淆。

### Notebooks

- `GeneralOverview/0_CreateDatasets.ipynb`：数据质量、相关性、分布、异常值和训练/验证/测试切分。
- `MLModelFits/0_CreateDatasets.ipynb`：构造原始、变换后及去异常值数据集。
- `MLModelFits/1_PolynomialRegression.ipynb`：Linear、Ridge、Lasso、ElasticNet 和多项式特征。
- `MLModelFits/2_RandomForest.ipynb`：Random Forest 网格搜索与有/无异常值比较。
- `MLModelFits/3_XGBoostDT.ipynb`：XGBoost 多输出策略、GridSearchCV 与 BayesSearchCV。
- `MLModelFits/4_NeuralNetwork.ipynb`：PyTorch 全连接网络训练。
- `MLModelFits/5_BayesianSearch.ipynb`：基于已有代理模型的参数贝叶斯搜索实验。
- `MLModelFits/6_GDSearch.ipynb`：将 sklearn Ridge 模型转换为 PyTorch 计算图并优化输入参数。
- `ComparisonPlots/`：多次运行的损失曲线对比和二维插值热图。

### `helmod/`

`HelMod_OfflineModule.py` 是 HelMod 4.1 离线模块，可作为库或命令行脚本使用。它可以：

- 读取 GALPROP FITS 或两列 TXT 的本地星际谱（LIS）；
- 在动能/核子与刚度之间转换；
- 按核素加载并合并主、次级成分；
- 读取 `HelModArchives/` 中的 `RawMatrixFile.npz`；
- 计算太阳调制后能谱并与归档实验数据作图。

基础命令形式为：

```bash
python helmod/HelMod_OfflineModule.py \
  --ArchivePATH helmod/HelModArchives/<archive> \
  --LIS <galprop.fits.gz-or-spectrum.txt> \
  --SimName <experiment-key>
```

可通过 `-h` 查看 `--txtFile`、`--ParametersSet`、`--SumAllIsotpes`、`--PrintLIS`、`--SimUnit` 和 `--MakePlot` 等选项。

## 环境与运行前检查

建议使用 Python 3.10。目录内已有 `.venv/`，但它占用约 11 GB，而且启动脚本固定激活 `/home/motz/CALETana/prop/.venv`，并不指向当前目录。

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

典型入口如下，但不建议在未修正配置路径前直接执行：

```bash
cd GradientDescent && python GD.py
cd BayesianOptimization && python BayesOpt.py
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
- 当前 15 个 Python 源文件均可被 Python AST 解析；HelMod 中有三处正则字符串触发无效转义 `SyntaxWarning`，但不是语法错误。

## 本次审查范围

本次只新增此 README，没有修改任何 Python、Shell、YAML、Notebook、数据、模型或历史输出文件，也没有执行 DRAGON、DRAGON2、`fitspectra`、优化器或 HelMod 模拟。
