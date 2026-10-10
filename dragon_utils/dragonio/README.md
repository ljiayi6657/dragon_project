# dragonio 代码说明

仅覆盖本目录直属代码。子目录见各自 README。历史工具的原有路径/命名未经本任务迁移；推荐 companion 单轮入口为项目 scripts/run_companion.py。示例说明实际接口，不表示历史优化/外部数据环境已通过运行验收。

## dragonio.py

saveresults 使用 pickle protocol=2 保存结果。

输入输出与限制：输入文件名和任意可 pickle 对象，输出二进制 pickle；不创建父目录且会覆盖，调用方检查路径与权限。无 CLI。

示例（历史/实验代码须先修正依赖与路径，不在本任务中执行）：

```python
from dragon_utils.dragonio.dragonio import saveresults
saveresults("/home/ljiayi/dragon_project/outputs/workflow/result.pkl", {"status": "checked"})
```

主要接口：`saveresults`。

实际导入：`math`, `os`, `pickle`, `sys`, `time`。
