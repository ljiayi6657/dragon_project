# Plotting Utilities

## BCfitting.py

Plots a diagnostic comparison of a solar-modulated DRAGON2 B/C ratio with AMS-02 TOA observations. It applies isotope-aware force-field modulation to B-10, B-11, C-12, C-13, and C-14 separately, then sums the two boron and three carbon fluxes before taking the ratio. The fixed potential is **0.64 GV**, matching `prop/BayesianOptimization/config.yaml`. The three panels show B/C, Model / Data, and fractional residual.

The DRAGON2 ASCII input remains an unmodulated local interstellar spectrum (LIS); only the model is modulated, and the plotted comparison is TOA against TOA. `load_model(source)` retains the unmodulated B/C return used by the Z-grid convergence analysis, while `load_model(source, components=True)` returns the isotope LIS fluxes used by the plot. This plot remains a visual diagnostic; it does not perform parameter optimization.

### Default paths

- DRAGON2 input: `/home/ljiayi/dragon_project/data/dragon_output/`
- AMS-02 input: `/home/ljiayi/dragon_project/data/experiment_data/expdata/BCdata/AMS-BC-2016.dat`
- Figures: `/home/ljiayi/dragon_project/outputs/figures/`

### Usage

```bash
cd /home/ljiayi/dragon_project/
python dragon_utils/plotting/BCfitting.py
python dragon_utils/plotting/BCfitting.py /path/to/dragon_output/
python dragon_utils/plotting/BCfitting.py /path/to/spectrum.txt
```

For a directory, the newest `.txt` spectrum is selected. The paths and `PHI_BC` at the top of the script can be edited. Default output uses `YYYY-MM-DD_BCratio-HHMM.png`. The optional `--output /absolute/path/figure.png` overrides it. `plot_bc(..., output=None)` accepts an exact file path; an existing directory or suffix-free path retains the legacy directory behavior. The companion entry supplies `YYYY-MM-DD_BCratio_dimZ<N>.png` and checks collisions before plotting.

## pHefitting.py

Plots proton and total helium TOA spectra with AMS-02 error bars and separate raw chi-square values, followed by model and official AMS-02 p/He at equal rigidity. The first two panels annotate only chi-square and modulation potential; point counts remain in terminal output. Required DRAGON2 columns are resolved by header name: `Sec_p`, `Pri_p`, `NUC_2003`, and `NUC_2004` must each occur exactly once.

### Default paths

- DRAGON2 input: `/home/ljiayi/dragon_project/data/dragon_output/`
- AMS-02 proton: `/home/ljiayi/dragon_project/data/experiment_data/expdata/nucdata/protonAMS02-2015.dat`
- AMS-02 helium: `/home/ljiayi/dragon_project/data/experiment_data/expdata/nucdata/heliumAMS02.dat`
- AMS-02 p/He: `/home/ljiayi/dragon_project/data/experiment_data/expdata/nucdata/pHeratioAMS02.csv`
- Figures: `/home/ljiayi/dragon_project/outputs/figures/`

Edit `PHI_P` and `PHI_HE` near the top of the script to change the proton and helium modulation potentials, both initially **0.64 GV** from `prop/BayesianOptimization/config.yaml`. Edit `OUTPUT_DIR` to change the figure directory.

### LIS-to-TOA processing and statistics

DRAGON2 `GetEk()` is kinetic energy per nucleon in GeV/n despite the ASCII header `Energy [GeV]`; normalized flux is per m², s, sr, and GeV/n (`dragon.cc`, `grid.cc`, and `include/input.h`). The script converts area units to cm² by dividing by 10000. Proton LIS is `Sec_p + Pri_p`. It reuses `data_processing.physics.SM_output` with `(Z,A,m)` equal to `(1,1,0.938272046)`, `(2,3,0.931494)`, and `(2,4,3.727379508/4)`, where m is GeV/n. He-3 and He-4 are modulated separately with energy shift `Z*phi/A`, then summed; no LIS extrapolation is allowed. Zero component flux is permitted for secondary protons, but the summed proton and each helium isotope LIS must be positive for log-log interpolation.

The [AMS proton table](https://ams02.web.cern.ch/publications/201501) and [AMS helium table](https://ams02.web.cern.ch/publications/201502) give rigidity bins in GV and flux/errors per m², s, sr, and GV. Local columns are `Rlo Rhi J stat trig acc unf scale syst expo`, with an extra base `10` column before `expo` for helium. Flux and errors are multiplied by `10^expo/10000`. The geometric rigidity-bin center is used. Existing `readamsproflxvals` and `readamsHEflxvals` implement this scaling; their `convtoE=True` helium conversion assumes He-4. To preserve the isotope mixture, this script compares spectra directly in rigidity: for each isotope, `T=sqrt((ZR/A)^2+m^2)-m`, evaluates the TOA model at T, multiplies by `dT/dR=(Z/A)^2 R/(T+m)`, and sums the helium rigidity fluxes. All three panels use rigidity in GV; the first two show differential flux per GV, and the third shows the dimensionless ratio `Jp_R/(JHe3_R+JHe4_R)` at the same rigidity.

`AMS_RATIO` points to a local, unmodified copy of the [official 2015 Table-II CSV](https://ams02.web.cern.ch/sites/default/files/publication/201502/table-ii.csv). It contains 67 bins from 1.92 to 1800 GV, with columns for bin edges, p/He, statistical error, four systematic components, and total systematic error. The header and values are validated. Ratio values and errors are already dimensionless and require no exponent or area conversion. Error bars use `sqrt(stat^2+syst^2)` directly from the published ratio table; they are not reconstructed by dividing the separately published proton and helium spectra or treating their errors as independent. These are near-Earth TOA observations, retaining solar modulation; modulation is applied only to the DRAGON2 LIS model. Runtime plotting reads the local file without network access.

Raw `chi2 = sum(((observed - TOA model)/sigma)^2)` uses `sigma = sqrt(stat^2 + syst^2)` and the existing `chisquare` utility. The total systematic column already contains trigger, acceptance, unfolding, and rigidity-scale contributions, which are not added again. Every observation whose shifted energy is outside the LIS range for any required isotope is counted and reported; excluded observations are marked separately in the figure. All covered observations are used, without the high-energy cuts of the Bayesian optimization workflow. No chi-square is calculated for p/He.

These fixed potentials were not optimized for the observation periods. The force-field approximation does not resolve time variation, drifts, or other heliospheric transport effects; low-energy comparisons are especially sensitive. The diagonal chi-square neglects systematic correlations, and bin-center evaluation approximates the bin-averaged measurement. Published p/He shares measurements with the flux panels and is shown for comparison only, without a separate chi-square or an added contribution to the flux statistics.

### Usage

```bash
cd /home/ljiayi/dragon_project/
python dragon_utils/plotting/pHefitting.py
python dragon_utils/plotting/pHefitting.py /path/to/dragon_output/
python dragon_utils/plotting/pHefitting.py /path/to/spectrum.txt
```

For a directory, the newest `.txt` file is selected by modification time (filename breaks ties), and the absolute selected path is printed. Invalid inputs fail with a nonzero exit status. The output directory is created when absent. The single figure is named `pHeratio_YY-MM-DD-TTTT.png` using `Asia/Tokyo`, with `TTTT` equal to 24-hour `HHMM`; its absolute path is printed. Runs within the same minute overwrite the same default figure. Pass `--output /absolute/path/figure.png` to choose an exact path; `plot_flux(energy, flux, output=None)` optionally saves there and still returns `(fig, results, toa)`.

`pHefitting.py` 保留未经 R^2.7 展示加权的接口及 Z 网格分析依赖；companion 默认绘图改为下述 `pHefitting27.py`，使用与 B/C 同轮的确切 TXT。


## 显式输出与单轮流程

```bash
python3 dragon_utils/plotting/BCfitting.py data/dragon_output/2026-10-10_dimZ81.txt --output /home/ljiayi/dragon_project/outputs/figures/2026-10-10_BCratio_dimZ81.png
python3 dragon_utils/plotting/pHefitting27.py data/dragon_output/2026-10-14_dimZ121.txt --output /home/ljiayi/dragon_project/outputs/figures/2026-10-14_pHe_dimZ121.png
```

日期/DimZ 替换为实际该轮值。`scripts/run_companion.py run <xml>` 无需 `--task`，一次模拟自动生成两张图；`plot YYYY-MM-DD_dimZ<N>` 也会用同一份数据重做两张图。单轮入口与直接调用绘图脚本都允许覆盖同名图片，无需 `--overwrite`；单轮入口还提供并发锁、哈希绑定及恢复。依赖 Python 3.10+、NumPy、Matplotlib；pHe 还需 SciPy 及 `data_processing.physics/statistic_analysis`。输入数据和单位、调制、同位素求和、统计定义均保留上文口径；所有正式图片直接保存到项目 `outputs/figures/`。

## pHefitting27.py

companion 默认使用的 p/He 展示版本，CLI `python3 /home/ljiayi/dragon_project/dragon_utils/plotting/pHefitting27.py /absolute/path/spectrum.txt [--output /absolute/path/figure.png]`；输入可为明确 TXT 或目录（选择最新 TXT），省略时默认 `data/dragon_output/`。主要函数仍是 `load_model`、`load_ams`、`modulate`、`rigidity`、`plot_flux`、`main`，依赖和 AMS 本地路径与 pHefitting.py 相同。质子为 Sec_p+Pri_p，He-3/4 分别调制并在刚度上相加，固定势 0.64 GV，p/He 不计算 χ²。

前两个面板的模型乘 `grid**2.7`，观测值和误差棒乘对应观测点的 `points**2.7`，纵轴为 `R^2.7 Flux [cm^-2 s^-1 sr^-1 GV^1.7]`。权重仅用于展示，χ² 始终使用未加权通量，第三幅等刚度 p/He 模型比值和观测误差不变。`plot_flux(energy, flux, output=None)` 可保存到精确路径，并返回 `(fig, results, toa)`。

默认图片为 `outputs/figures/YYYY-MM-DD_pHe27.png`（Asia/Tokyo，同日覆盖）；`--output` 覆盖默认路径。companion 显式传入原有规范名称 `YYYY-MM-DD_pHe_dimZ<N>.png`，在 figures/ 直属临时 PNG 完成后原子替换并记录哈希。生成图不会运行 DRAGON、不修改 TXT/FITS/XML；历史未加权图可使用其对应原始 TXT 加精确 `--output` 重画。未经加权的 `pHefitting.py` 和 CSV 收敛分析的数值不随此展示切换改变。

### Optional flux-normalization fit

Append `--fit` to fit independent positive post-processing constants `C_p` and `C_He`. The fitted models are `C_p` times the complete proton TOA flux and `C_He` times the sum of the separately modulated He-3 and He-4 TOA rigidity fluxes. These constants do not change the XML, `ProtNormFlux`, source abundances, propagation parameters, or the He-3/He-4 ratio. The fitted p/He curve therefore gains the factor `C_p/C_He`.

The default fitting range is bin-center rigidity `R >= 10 GV`; change it with `--fit-min GV`, including `--fit-min 0` for all covered points. All covered AMS-02 points remain visible with one common marker and legend style; the threshold annotation identifies the fitted range, while coverage exclusions retain crosses. For each species the code minimizes the existing raw diagonal statistic `sum(((observed-C*model)/sigma)^2)` analytically, then evaluates six nearby constants at factors 0.98, 0.99, 0.995, 1.005, 1.01, and 1.02. A scanned constant is adopted only when its raw chi-square is lower than the analytic result; every candidate, the analytic result, the adopted source, N, dof=N-1, and reduced chi-square are printed.

All three panels display only `R > 5 GV`, controlled by the editable top-level `PLOT_MIN`; this visual cut does not change the default `R >= 10 GV` fit selection or its statistics. The proton and helium panels annotate the adopted constant, raw fit chi-square, reduced chi-square, threshold, and modulation potential. The p/He panel annotates `C_p`, `C_He`, and their ratio without adding a ratio chi-square. The default fitted filename is `outputs/figures/YYYY-MM-DD_pHefit.png`; explicit `--output` still takes precedence. `plot_flux(energy, flux, output=None, fit=False, fit_min=10.0)` returns the adopted constant, analytic value, scan candidates, fit counts, and chi-square details inside `results`. The reusable scalar fitter is `data_processing.statistic_analysis.fit_constant`.

```bash
python3 dragon_utils/plotting/pHefitting27.py /path/to/spectrum.txt --fit
python3 dragon_utils/plotting/pHefitting27.py /path/to/spectrum.txt --fit --fit-min 0
python3 dragon_utils/plotting/pHefitting27.py /path/to/spectrum.txt --fit --fit-min 10 --output /absolute/path/fit.png
```

The companion runner does not add `--fit`, so its standard p/He plot remains the unscaled diagnostic unless a separate explicit fit command is requested. Fixed force-field potentials, diagonal errors, and bin-center evaluation retain the limitations described above; a fitted normalization cannot repair a spectral-shape mismatch and must not be interpreted as a fitted source abundance.

2026-10-14 已按各自原始 TXT 覆盖 25 张未加权历史图，保留原文件名；两张已加权的历史图保持原样。覆盖清单、输入与图片前后哈希、统计结果及历史实验缩放记录在 `outputs/workflow/2026-10-14_pHe.json`，对应运行日志路径也在清单中。18 份 companion 状态及原有氦缩放实验记录已更新图片哈希。早期临时 He-3×3、He-4×4 实验图保留原实验缩放并标注 scaled He；其他历史图使用各自原始谱，不借用最新模拟结果。
