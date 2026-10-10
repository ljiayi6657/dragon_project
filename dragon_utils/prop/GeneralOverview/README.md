# GeneralOverview 代码说明

仅覆盖本目录直属代码。子目录见各自 README。历史工具的原有路径/命名未经本任务迁移；推荐 companion 单轮入口为项目 scripts/run_companion.py。示例说明实际接口，不表示历史优化/外部数据环境已通过运行验收。

## 0_CreateDatasets.ipynb

构造和切分历史 fitspectra 数据集，读取位置敏感 pickle，输出相对 Data/、BestModels/Transformer/ 的 pickle/scaler；GeneralOverview 版本偏数据诊断，MLModelFits 版本含去异常值与变换数据。

入口：在本目录 Jupyter 打开并逐单元检查；默认依赖 pandas、NumPy、Matplotlib、scikit-learn、joblib/pickle，另需各单元实际导入的训练库。相对数据/模型/图片路径保留旧格式；此任务只整理文档，未执行 notebook。正式图输出需在另行授权时迁移至 outputs/figures/。

```bash
jupyter lab 0_CreateDatasets.ipynb
```
