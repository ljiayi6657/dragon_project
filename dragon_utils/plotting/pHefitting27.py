"""Compare or normalize-fit R^2.7-weighted proton/helium TOA spectra."""

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
from dragon_utils.data_processing.statistic_analysis import chisquare, fit_constant


PHI_P = 0.64
PHI_HE = 0.64
FIT_MIN = 10.0
PLOT_MIN = 5.0
SCAN_SCALE = (0.98, 0.99, 0.995, 1.005, 1.01, 1.02)
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


def plot_flux(energy, flux, output=None, fit=False, fit_min=FIT_MIN):
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
        raw = chisquare(obs[keep], matched, error[keep])
        if not np.isfinite(raw) or raw < 0:
            raise ValueError(f"Invalid {mode} chi-square")
        scale = 1.0
        chi2 = raw
        fitset = keep.copy()
        dof = used
        source = "none"
        analytic = None
        scan = None
        if fit:
            fitset &= points >= fit_min
            count = int(np.count_nonzero(fitset))
            if count < 2:
                raise ValueError(f"Fewer than two {mode} observations at R >= {fit_min:g} GV")
            model = rigidity(energy, flux, points[fitset], mode, phi)
            data = obs[fitset]
            sigma = error[fitset]
            fitout = fit_constant(data, model, sigma, SCAN_SCALE)
            analytic = fitout["analytic"]
            anachi = fitout["anachi"]
            scan = fitout["scan"]
            for candidate, value in scan:
                print(f"{mode}: scan C = {candidate:.10g}; raw chi-square = {value:.10g}")
            scale = fitout["constant"]
            chi2 = fitout["chi2"]
            source = fitout["source"]
            dof = count - 1
            print(f"{mode}: analytic C = {analytic:.10g}; raw chi-square = {anachi:.10g}")
            print(f"{mode}: adopted {source} C = {scale:.10g}; raw chi-square = "
                  f"{chi2:.10g}; N = {count}; dof = {dof}; "
                  f"reduced chi-square = {chi2 / dof:.10g}")
        else:
            print(f"{mode}: raw chi-square = {chi2:.10g}; N = {used}")
        results[mode] = {"chi2": chi2, "raw": raw, "used": used,
                         "excluded": excluded, "constant": scale,
                         "fitused": int(np.count_nonzero(fitset)), "dof": dof,
                         "reduced": chi2 / dof, "source": source,
                         "analytic": analytic, "scan": scan}
        bounds = []
        for name, charge, massnum, mass in SPECIES[mode]:
            low = max(energy[0] - charge * phi / massnum, 1e-8)
            high = energy[-1] - charge * phi / massnum
            if high <= low:
                raise ValueError(f"No TOA plotting range for {name}")
            bounds.append((massnum / charge * np.sqrt(low * (low + 2 * mass)),
                           massnum / charge * np.sqrt(high * (high + 2 * mass))))
        limits.extend(bounds)
        lo = max(max(item[0] for item in bounds), points[0] / 1.5,
                 np.nextafter(PLOT_MIN, np.inf))
        hi = min(min(item[1] for item in bounds), points[-1] * 1.5)
        grid = np.geomspace(lo, hi, 500)
        grid = grid[coverage(energy, grid, mode, phi)]
        # Weight spectra and uncertainties only for display.
        weight = points**2.7
        show = keep & (points > PLOT_MIN)
        ax.plot(grid, scale * rigidity(energy, flux, grid, mode, phi) * grid**2.7,
                label="DRAGON2 TOA fit" if fit else "DRAGON2 TOA")
        ax.errorbar(points[show], obs[show] * weight[show],
                    yerr=error[show] * weight[show], fmt="o",
                    markersize=3, capsize=2, label="AMS-02 TOA")
        if excluded:
            outside = ~keep & (points > PLOT_MIN)
            if np.any(outside):
                ax.errorbar(points[outside], obs[outside] * weight[outside],
                            yerr=error[outside] * weight[outside], fmt="x",
                            color="gray", markersize=3,
                            label="AMS-02 outside coverage")
        ax.set_title("Proton" if mode == "p" else "Helium (He-3 + He-4)")
        ax.set_xlabel("Rigidity [GV]")
        ax.set_ylabel(r"$R^{2.7}$ Flux [cm$^{-2}$ s$^{-1}$ sr$^{-1}$ GV$^{1.7}$]")
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlim(left=PLOT_MIN)
        if fit:
            symbol = r"C_p" if mode == "p" else r"C_{\rm He}"
            note = (rf"${symbol} = {scale:.5g}$" + "\n" +
                    rf"$\chi^2 = {chi2:.2f}$, $\chi^2/\nu = {chi2 / dof:.2f}$" + "\n" +
                    rf"$R \geq {fit_min:g}$ GV, $\phi = {phi:.2f}$ GV")
        else:
            note = rf"$\chi^2 = {chi2:.2f}$, $\phi = {phi:.2f}$ GV"
        ax.text(0.05, 0.05, note, transform=ax.transAxes)
        ax.legend()
    points, obs, error = load_ams("ratio")
    keep = coverage(energy, points, "p", PHI_P) & coverage(energy, points, "He", PHI_HE)
    used = int(np.count_nonzero(keep))
    excluded = int(points.size - used)
    print(f"p/He: used {used}/{points.size}; excluded {excluded} observations "
          "outside shifted LIS coverage; no chi-square calculated")
    if used == 0:
        raise ValueError("No AMS-02 p/He observations within shifted LIS coverage")
    lo = max(max(item[0] for item in limits), points[0] / 1.5,
             np.nextafter(PLOT_MIN, np.inf))
    hi = min(min(item[1] for item in limits), points[-1] * 1.5)
    grid = np.geomspace(lo, hi, 500)
    grid = grid[coverage(energy, grid, "p", PHI_P) & coverage(energy, grid, "He", PHI_HE)]
    if grid.size < 2:
        raise ValueError("Insufficient common TOA rigidity grid for p/He")
    toa = {}
    c_p = results["p"]["constant"]
    c_he = results["He"]["constant"]
    proton = c_p * rigidity(energy, flux, grid, "p", PHI_P, parts=toa)
    helium = c_he * rigidity(energy, flux, grid, "He", PHI_HE, parts=toa)
    ratio = proton / helium
    if not np.all(np.isfinite(ratio)) or np.any(ratio <= 0):
        raise ValueError("Invalid TOA p/He ratio")
    axes[2].plot(grid, ratio, label="DRAGON2 TOA fit" if fit else "DRAGON2 TOA")
    show = keep & (points > PLOT_MIN)
    axes[2].errorbar(points[show], obs[show], yerr=error[show], fmt="o",
                    markersize=3, capsize=2, label="AMS-02 TOA")
    if excluded:
        outside = ~keep & (points > PLOT_MIN)
        if np.any(outside):
            axes[2].errorbar(points[outside], obs[outside], yerr=error[outside], fmt="x",
                             color="gray", markersize=3,
                             label="AMS-02 outside coverage")
    axes[2].set_title("Proton / Helium at equal rigidity")
    axes[2].set_xlabel("Rigidity [GV]")
    axes[2].set_ylabel("p/He")
    axes[2].set_xscale("log")
    axes[2].set_xlim(left=PLOT_MIN)
    if fit:
        note = (rf"$C_p = {c_p:.5g}$, $C_{{\rm He}} = {c_he:.5g}$" + "\n" +
                rf"$C_p/C_{{\rm He}} = {c_p / c_he:.5g}$")
        axes[2].text(0.05, 0.08, note, transform=axes[2].transAxes)
    axes[2].legend()
    fig.tight_layout()
    if output is not None:
        target = Path(output).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(target, dpi=150)
    return fig, results, toa


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dragon", nargs="?", default=DRAGON_OUT,
                        help="DRAGON2 output directory or a .txt spectrum")
    parser.add_argument("--output", help="Exact figure path")
    parser.add_argument("--fit", action="store_true",
                        help="Fit positive proton and helium flux constants")
    parser.add_argument("--fit-min", type=float, default=FIT_MIN, metavar="GV",
                        help=f"Minimum rigidity used by --fit (default: {FIT_MIN:g} GV)")
    args = parser.parse_args()
    try:
        for phi in (PHI_P, PHI_HE):
            if not np.isfinite(phi) or phi < 0:
                raise ValueError("Modulation potentials must be finite and nonnegative")
        if not np.isfinite(args.fit_min) or args.fit_min < 0:
            raise ValueError("Fit minimum rigidity must be finite and nonnegative")
        path, energy, flux = load_model(args.dragon)
        print("Units: LIS energy GeV/n; flux cm^-2 s^-1 sr^-1 (GeV/n)^-1.")
        print("AMS comparisons: rigidity GV; flux cm^-2 s^-1 sr^-1 GV^-1.")
        print("Fixed project potentials; diagonal errors; bin-center evaluation.")
        print("Display: R^2.7 times flux and uncertainties; chi-square uses unweighted flux.")
        stamp = datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%Y-%m-%d")
        target = (Path(args.output).expanduser().resolve() if args.output
                  else Path(OUTPUT_DIR).resolve() /
                  f"{stamp}_{'pHefit' if args.fit else 'pHe27'}.png")
        fig, results, toa = plot_flux(energy, flux, output=target,
                                      fit=args.fit, fit_min=args.fit_min)
        plt.close(fig)
    except (ValueError, OSError) as exc:
        plt.close("all")
        parser.exit(1, f"Error: {exc}\n")
    print(f"Saved figure: {target}")


if __name__ == "__main__":
    main()
