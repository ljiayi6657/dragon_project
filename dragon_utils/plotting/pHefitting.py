"""Compare DRAGON2 proton/helium TOA spectra with AMS-02 and plot p/He."""

import argparse
from datetime import datetime
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from dragon_utils.data_processing.physics import SM_output
from dragon_utils.data_processing.statistic_analysis import chisquare


PHI_P = 0.64
PHI_HE = 0.64
DRAGON_OUT = ROOT / "data/dragon_output"
AMS_DIR = ROOT / "data/experiment_data/expdata/nucdata"
AMS_RATIO = AMS_DIR / "pHeratioAMS02.csv"
OUTPUT_DIR = ROOT / "outputs/figures"
SPECIES = {
    "p": (("p", 1, 1, 0.938272046),),
    "He": (("NUC_2003", 2, 3, 0.931494),
           ("NUC_2004", 2, 4, 3.727379508 / 4)),
}


def load_model(source):
    path = Path(source).expanduser().resolve()
    if not path.exists():
        raise ValueError(f"DRAGON2 input does not exist: {path}")
    if path.is_dir():
        files = [item for item in path.glob("*.txt") if item.is_file()]
        if not files:
            raise ValueError(f"No DRAGON2 .txt spectra in: {path}")
        path = max(files, key=lambda item: (item.stat().st_mtime, item.name))
    elif not path.is_file() or path.suffix != ".txt":
        raise ValueError(f"DRAGON2 input must be a directory or .txt spectrum: {path}")
    print(f"DRAGON2 spectrum: {path}")
    with path.open(encoding="utf-8") as stream:
        for count, line in enumerate(stream, 1):
            if line.strip() and not line.lstrip().startswith("#"):
                header = line.split()
                break
        else:
            raise ValueError(f"Empty DRAGON2 spectrum: {path}")
    if header[:2] != ["Energy", "[GeV]"]:
        raise ValueError(f"Unrecognized DRAGON2 header: {path}")
    keys = header[2:]
    needed = ("Sec_p", "Pri_p", "NUC_2003", "NUC_2004")
    if any(keys.count(name) != 1 for name in needed):
        raise ValueError(f"Missing or duplicate required proton/helium column: {path}")
    data = np.loadtxt(path, skiprows=count, comments="#", ndmin=2)
    if data.shape[0] < 2 or data.shape[1] != len(keys) + 1:
        raise ValueError(f"Incomplete DRAGON2 spectrum: {path}")
    if not np.all(np.isfinite(data)):
        raise ValueError(f"Non-finite DRAGON2 values: {path}")
    energy = data[:, 0]
    if np.any(energy <= 0) or np.any(np.diff(energy) <= 0):
        raise ValueError(f"DRAGON2 energy must be positive and strictly increasing: {path}")
    # dragon.cc/GetEk(): GeV/n and differential flux per m2; convert area only.
    flux = {name: data[:, keys.index(name) + 1] / 10000 for name in needed}
    if any(np.any(values < 0) for values in flux.values()):
        raise ValueError(f"Negative proton/helium component flux: {path}")
    flux["p"] = flux["Sec_p"] + flux["Pri_p"]
    for name in ("p", "NUC_2003", "NUC_2004"):
        if np.any(flux[name] <= 0):
            raise ValueError(f"{name} LIS must be positive for SM_output log-log interpolation")
    return path, energy, flux


def load_ams(mode):
    # AMS 2015 Table-I and datareader.py: Rlo,Rhi,J,stat,trig,acc,unf,scale,syst.
    schema = ("lo", "hi", "flux", "stat", "trig", "acc", "unf", "scale", "syst")
    if mode == "ratio":
        path = AMS_RATIO
        fields = ("rigidity_min GV", "rigidity_max GV", "proton_to_helium_ratio")
        fields += tuple(f"proton_to_helium_ratio_error_{key}" for key in
                        ("statistical", "trigger", "acceptance", "unfolding",
                         "rigidity_scale", "systematic_total"))
        with path.open(encoding="utf-8-sig") as stream:
            header = tuple(item.strip() for item in stream.readline().strip().split(","))
        if header != fields:
            raise ValueError(f"Unexpected AMS-02 p/He CSV header: {path}")
        data = np.loadtxt(path, delimiter=",", skiprows=1, ndmin=2)
    else:
        name = "protonAMS02-2015.dat" if mode == "p" else "heliumAMS02.dat"
        path = AMS_DIR / name
        data = np.loadtxt(path, comments="#", ndmin=2)
        schema += ("expo",) if mode == "p" else ("ten", "expo")
    if data.shape[0] == 0 or data.shape[1] != len(schema):
        raise ValueError(f"Unexpected AMS-02 column count: {path}")
    if not np.all(np.isfinite(data)):
        raise ValueError(f"Non-finite AMS-02 values: {path}")
    cols = dict(zip(schema, data.T))
    if mode == "He" and np.any(cols["ten"] != 10):
        raise ValueError(f"AMS-02 helium exponent base must be 10: {path}")
    if mode != "ratio" and np.any(cols["expo"] != np.rint(cols["expo"])):
        raise ValueError(f"Invalid AMS-02 exponent: {path}")
    if np.any(cols["lo"] <= 0) or np.any(cols["hi"] <= cols["lo"]):
        raise ValueError(f"Invalid AMS-02 rigidity bins: {path}")
    axis = np.sqrt(cols["lo"] * cols["hi"])
    if np.any(np.diff(axis) <= 0) or np.any(cols["lo"][1:] < cols["hi"][:-1]):
        raise ValueError(f"AMS-02 rigidity bins must be increasing and disjoint: {path}")
    if np.any(cols["flux"] <= 0) or np.any(data[:, 3:9] < 0):
        raise ValueError(f"Invalid AMS-02 flux or uncertainty: {path}")
    # Published Table-II ratio and errors are dimensionless, without exponent scaling.
    factor = 1.0 if mode == "ratio" else np.power(10.0, cols["expo"]) / 10000
    obs = cols["flux"] * factor
    # syst already includes trig/acc/unf/scale.
    error = np.hypot(cols["stat"], cols["syst"]) * factor
    if not np.all(np.isfinite(obs)) or not np.all(np.isfinite(error)) or np.any(error <= 0):
        raise ValueError(f"Invalid scaled AMS-02 flux or uncertainty: {path}")
    return axis, obs, error


def kinetic(axis, charge, massnum, mass):
    """Convert rigidity [GV] to kinetic energy [GeV/n]."""
    momentum = charge * axis / massnum
    return momentum**2 / (np.hypot(momentum, mass) + mass)


def coverage(energy, points, mode, phi):
    keep = np.ones(points.size, dtype=bool)
    for name, charge, massnum, mass in SPECIES[mode]:
        shifted = kinetic(points, charge, massnum, mass) + charge * phi / massnum
        keep &= (shifted >= energy[0]) & (shifted <= energy[-1])
    return keep


def modulate(energy, flux, points, name, charge, massnum, mass, phi):
    _, toa = SM_output(energy, flux[name], PhiP=phi, Mass=mass,
                       output_energies=points, allow_extrapolation=False,
                       charge=charge, massnum=massnum)
    if not np.all(np.isfinite(toa)) or np.any(toa <= 0):
        raise ValueError(f"Nonpositive or non-finite {name} TOA flux")
    return toa


def rigidity(energy, flux, points, mode, phi, parts=None):
    """Sum isotope TOA fluxes after each isotope's rigidity Jacobian."""
    total = np.zeros(points.size)
    for name, charge, massnum, mass in SPECIES[mode]:
        ek = kinetic(points, charge, massnum, mass)
        toa = modulate(energy, flux, ek, name, charge, massnum, mass, phi)
        jac = (charge / massnum)**2 * points / (ek + mass)
        total += toa * jac
        if parts is not None:
            parts[name] = toa * jac
    return total


def plot_flux(energy, flux):
    fig, axes = plt.subplots(3, 1, figsize=(8, 10))
    results = {}
    limits = []
    for ax, mode, phi in zip(axes[:2], ("p", "He"), (PHI_P, PHI_HE)):
        points, obs, error = load_ams(mode)
        keep = coverage(energy, points, mode, phi)
        used = int(np.count_nonzero(keep))
        excluded = int(points.size - used)
        print(f"{mode}: Phi = {phi:.6g} GV; used {used}/{points.size}; "
              f"excluded {excluded} observations outside shifted LIS coverage")
        if used == 0:
            raise ValueError(f"No {mode} observations within shifted LIS coverage")
        matched = rigidity(energy, flux, points[keep], mode, phi)
        chi2 = chisquare(obs[keep], matched, error[keep])
        if not np.isfinite(chi2) or chi2 < 0:
            raise ValueError(f"Invalid {mode} chi-square")
        results[mode] = {"chi2": chi2, "used": used, "excluded": excluded}
        print(f"{mode}: raw chi-square = {chi2:.10g}; N = {used}")
        bounds = []
        for name, charge, massnum, mass in SPECIES[mode]:
            low = max(energy[0] - charge * phi / massnum, 1e-8)
            high = energy[-1] - charge * phi / massnum
            if high <= low:
                raise ValueError(f"No TOA plotting range for {name}")
            bounds.append((massnum / charge * np.sqrt(low * (low + 2 * mass)),
                           massnum / charge * np.sqrt(high * (high + 2 * mass))))
        limits.extend(bounds)
        lo = max(max(item[0] for item in bounds), points[0] / 1.5)
        hi = min(min(item[1] for item in bounds), points[-1] * 1.5)
        grid = np.geomspace(lo, hi, 500)
        grid = grid[coverage(energy, grid, mode, phi)]
        ax.plot(grid, rigidity(energy, flux, grid, mode, phi), label="DRAGON2 TOA")
        ax.errorbar(points[keep], obs[keep], yerr=error[keep], fmt="o",
                    markersize=3, capsize=2, label="AMS-02 TOA")
        if excluded:
            ax.errorbar(points[~keep], obs[~keep], yerr=error[~keep], fmt="x",
                        color="gray", markersize=3, label="AMS-02 outside coverage")
        ax.set_title("Proton" if mode == "p" else "Helium (He-3 + He-4)")
        ax.set_xlabel("Rigidity [GV]")
        ax.set_ylabel(r"Flux [cm$^{-2}$ s$^{-1}$ sr$^{-1}$ GV$^{-1}$]")
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.text(0.05, 0.08, rf"$\chi^2 = {chi2:.2f}$, $\phi = {phi:.2f}$ GV",
                transform=ax.transAxes)
        ax.legend()
    points, obs, error = load_ams("ratio")
    keep = coverage(energy, points, "p", PHI_P) & coverage(energy, points, "He", PHI_HE)
    used = int(np.count_nonzero(keep))
    excluded = int(points.size - used)
    print(f"p/He: used {used}/{points.size}; excluded {excluded} observations "
          "outside shifted LIS coverage; no chi-square calculated")
    if used == 0:
        raise ValueError("No AMS-02 p/He observations within shifted LIS coverage")
    lo = max(max(item[0] for item in limits), points[0] / 1.5)
    hi = min(min(item[1] for item in limits), points[-1] * 1.5)
    grid = np.geomspace(lo, hi, 500)
    grid = grid[coverage(energy, grid, "p", PHI_P) & coverage(energy, grid, "He", PHI_HE)]
    if grid.size < 2:
        raise ValueError("Insufficient common TOA rigidity grid for p/He")
    toa = {}
    proton = rigidity(energy, flux, grid, "p", PHI_P, parts=toa)
    helium = rigidity(energy, flux, grid, "He", PHI_HE, parts=toa)
    ratio = proton / helium
    if not np.all(np.isfinite(ratio)) or np.any(ratio <= 0):
        raise ValueError("Invalid TOA p/He ratio")
    axes[2].plot(grid, ratio, label="DRAGON2 TOA")
    axes[2].errorbar(points[keep], obs[keep], yerr=error[keep], fmt="o",
                    markersize=3, capsize=2, label="AMS-02 TOA")
    if excluded:
        axes[2].errorbar(points[~keep], obs[~keep], yerr=error[~keep], fmt="x",
                        color="gray", markersize=3, label="AMS-02 outside coverage")
    axes[2].set_title("Proton / Helium at equal rigidity")
    axes[2].set_xlabel("Rigidity [GV]")
    axes[2].set_ylabel("p/He")
    axes[2].set_xscale("log")
    axes[2].legend()
    fig.tight_layout()
    return fig, results, toa


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dragon", nargs="?", default=DRAGON_OUT,
                        help="DRAGON2 output directory or a .txt spectrum")
    args = parser.parse_args()
    try:
        for phi in (PHI_P, PHI_HE):
            if not np.isfinite(phi) or phi < 0:
                raise ValueError("Modulation potentials must be finite and nonnegative")
        path, energy, flux = load_model(args.dragon)
        print("Units: LIS energy GeV/n; flux cm^-2 s^-1 sr^-1 (GeV/n)^-1.")
        print("AMS comparisons: rigidity GV; flux cm^-2 s^-1 sr^-1 GV^-1.")
        print("Fixed project potentials; diagonal errors; bin-center evaluation.")
        fig, results, toa = plot_flux(energy, flux)
        output = Path(OUTPUT_DIR).expanduser().resolve()
        output.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%y-%m-%d-%H%M")
        target = output / f"pHeratio_{stamp}.png"
        fig.savefig(target, dpi=150)
        plt.close(fig)
    except (ValueError, OSError) as exc:
        plt.close("all")
        parser.exit(1, f"Error: {exc}\n")
    print(f"Saved figure: {target}")


if __name__ == "__main__":
    main()
