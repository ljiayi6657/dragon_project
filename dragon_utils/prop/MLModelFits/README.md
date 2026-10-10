# MLModelFits 代码说明

仅覆盖本目录直属代码。子目录见各自 README。历史工具的原有路径/命名未经本任务迁移；推荐 companion 单轮入口为项目 scripts/run_companion.py。示例说明实际接口，不表示历史优化/外部数据环境已通过运行验收。

## 0_CreateDatasets.ipynb

构造和切分历史 fitspectra 数据集，读取位置敏感 pickle，输出相对 Data/、BestModels/Transformer/ 的 pickle/scaler；GeneralOverview 版本偏数据诊断，MLModelFits 版本含去异常值与变换数据。

入口：在本目录 Jupyter 打开并逐单元检查；默认依赖 pandas、NumPy、Matplotlib、scikit-learn、joblib/pickle，另需各单元实际导入的训练库。相对数据/模型/图片路径保留旧格式；此任务只整理文档，未执行 notebook。正式图输出需在另行授权时迁移至 outputs/figures/。

```bash
jupyter lab 0_CreateDatasets.ipynb
```

## 1_PolynomialRegression.ipynb

比较 Linear/Ridge/Lasso/ElasticNet 多项式代理，读取 Data/ pickle，输出 BestModels/ 下 joblib 模型及评估图。

入口：在本目录 Jupyter 打开并逐单元检查；默认依赖 pandas、NumPy、Matplotlib、scikit-learn、joblib/pickle，另需各单元实际导入的训练库。相对数据/模型/图片路径保留旧格式；此任务只整理文档，未执行 notebook。正式图输出需在另行授权时迁移至 outputs/figures/。

```bash
jupyter lab 1_PolynomialRegression.ipynb
```

## 2_RandomForest.ipynb

随机森林多输出拟合与网格搜索，读取预处理 Data，输出 BestModels/RandomForest.pkl。

入口：在本目录 Jupyter 打开并逐单元检查；默认依赖 pandas、NumPy、Matplotlib、scikit-learn、joblib/pickle，另需各单元实际导入的训练库。相对数据/模型/图片路径保留旧格式；此任务只整理文档，未执行 notebook。正式图输出需在另行授权时迁移至 outputs/figures/。

```bash
jupyter lab 2_RandomForest.ipynb
```

## 3_XGBoostDT.ipynb

XGBoost/GBDT 多输出拟合与超参数实验，读取 Data，输出 BestModels/GBDT.pkl；需 xgboost。

入口：在本目录 Jupyter 打开并逐单元检查；默认依赖 pandas、NumPy、Matplotlib、scikit-learn、joblib/pickle，另需各单元实际导入的训练库。相对数据/模型/图片路径保留旧格式；此任务只整理文档，未执行 notebook。正式图输出需在另行授权时迁移至 outputs/figures/。

```bash
jupyter lab 3_XGBoostDT.ipynb
```

## 4_NeuralNetwork.ipynb

PyTorch 全连接网络训练实验，输入预处理数组/数据集，输出训练结果与 notebook 图；需 torch。

入口：在本目录 Jupyter 打开并逐单元检查；默认依赖 pandas、NumPy、Matplotlib、scikit-learn、joblib/pickle，另需各单元实际导入的训练库。相对数据/模型/图片路径保留旧格式；此任务只整理文档，未执行 notebook。正式图输出需在另行授权时迁移至 outputs/figures/。

```bash
jupyter lab 4_NeuralNetwork.ipynb
```

## 5_BayesianSearch.ipynb

读取已保存 joblib 代理和 scaler，在代理上执行贝叶斯参数搜索；需 bayesian-optimization，依旧模型和 scaler 路径。

入口：在本目录 Jupyter 打开并逐单元检查；默认依赖 pandas、NumPy、Matplotlib、scikit-learn、joblib/pickle，另需各单元实际导入的训练库。相对数据/模型/图片路径保留旧格式；此任务只整理文档，未执行 notebook。正式图输出需在另行授权时迁移至 outputs/figures/。

```bash
jupyter lab 5_BayesianSearch.ipynb
```

## 6_GDSearch.ipynb

将 Ridge 多项式模型转换为 PyTorch 计算图，在代理上梯度搜索；读取 joblib/scaler/pickle，输出候选和图，不是 companion 模型提交器。

入口：在本目录 Jupyter 打开并逐单元检查；默认依赖 pandas、NumPy、Matplotlib、scikit-learn、joblib/pickle，另需各单元实际导入的训练库。相对数据/模型/图片路径保留旧格式；此任务只整理文档，未执行 notebook。正式图输出需在另行授权时迁移至 outputs/figures/。

```bash
jupyter lab 6_GDSearch.ipynb
```
