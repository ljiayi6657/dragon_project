# ComparisonPlots 代码说明

仅覆盖本目录直属代码。子目录见各自 README。历史工具的原有路径/命名未经本任务迁移；推荐 companion 单轮入口为项目 scripts/run_companion.py。示例说明实际接口，不表示历史优化/外部数据环境已通过运行验收。

## create_comparisonPlots.ipynb

比较历史优化多轮损失曲线；读取硬编码 CALETana/MLProject/GradientDescent config 与 data.pkl，输出相对 plots/ 的 PNG。

入口：在本目录 Jupyter 打开并逐单元检查；默认依赖 pandas、NumPy、Matplotlib、scikit-learn、joblib/pickle，另需各单元实际导入的训练库。相对数据/模型/图片路径保留旧格式；此任务只整理文档，未执行 notebook。正式图输出需在另行授权时迁移至 outputs/figures/。

```bash
jupyter lab create_comparisonPlots.ipynb
```

## create_heatmap.ipynb

二维插值热图；读取硬编码 CALETana/MLProject/BayesianOptimization config 与旧拟合 pickle，输出 save_folder/heatmap.png；依赖 SciPy griddata。

入口：在本目录 Jupyter 打开并逐单元检查；默认依赖 pandas、NumPy、Matplotlib、scikit-learn、joblib/pickle，另需各单元实际导入的训练库。相对数据/模型/图片路径保留旧格式；此任务只整理文档，未执行 notebook。正式图输出需在另行授权时迁移至 outputs/figures/。

```bash
jupyter lab create_heatmap.ipynb
```
