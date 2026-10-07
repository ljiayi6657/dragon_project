# Plotting Utilities

## BCfitting.py

Plots a diagnostic comparison of a DRAGON2 B/C ratio with AMS-02 observations. It sums B-10 and B-11, and C-12, C-13, and C-14 from the DRAGON2 ASCII spectrum. The three panels show B/C, Model / Data, and fractional residual.

The model output is an unmodulated local interstellar spectrum (LIS), while the AMS-02 data are near-Earth observations (TOA). This plot is for visual inspection; its ratios and residuals are not a physical fit statistic.

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

For a directory, the newest `.txt` spectrum is selected. The paths at the top of the script can be edited. Output uses `YYYY-MM-DD_BCratio-HHMM.png` in the figures directory.

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

For a directory, the newest `.txt` file is selected by modification time (filename breaks ties), and the absolute selected path is printed. Invalid inputs fail with a nonzero exit status. The output directory is created when absent. The single figure is named `pHeratio_YY-MM-DD-TTTT.png` using `Asia/Tokyo`, with `TTTT` equal to 24-hour `HHMM`; its absolute path is printed. Runs within the same minute overwrite the same figure.
