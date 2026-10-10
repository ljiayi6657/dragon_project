# helmod 代码说明

仅覆盖本目录直属代码。子目录见各自 README。历史工具的原有路径/命名未经本任务迁移；推荐 companion 单轮入口为项目 scripts/run_companion.py。示例说明实际接口，不表示历史优化/外部数据环境已通过运行验收。

## HelMod_OfflineModule.py

HelMod 4.1 离线太阳调制模块，可作库或 CLI。

输入输出与限制：读取 --ArchivePATH 模拟矩阵归档、--LIS GALPROP FITS/两列 TXT、--SimName 实验键，输出 HelModOutput* 谱与可选图。库主类 `SolarModulation`；需 NumPy/SciPy/Astropy；两处 np.float 与 NumPy 1.24+ 不兼容，归档/单位必须匹配，不取代当前 force-field 绘图。

示例（历史/实验代码须先修正依赖与路径，不在本任务中执行）：

```bash
python3 dragon_utils/prop/helmod/HelMod_OfflineModule.py -h
```

主要接口：`To_np_array`, `beta_`, `Rigidity`, `Energy`, `dT_dR`, `dR_dT`, `Tkin2Rigi_FluxConversione`, `find_nearest_idx`, `find_nearest_value`, `mkdir_p` 等（完整签名见源码）。

实际导入：`astropy`, `errno`, `getopt`, `glob`, `matplotlib`, `numpy`, `os`, `re`, `scipy`, `sys`。
