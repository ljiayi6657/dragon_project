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
