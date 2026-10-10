"""Plot a diagnostic DRAGON2 B/C comparison with AMS-02 data."""

import argparse
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import matplotlib.pyplot as plt
import numpy as np


DRAGON_OUT = "/home/ljiayi/dragon_project/data/dragon_output/"
AMS_DATA = "/home/ljiayi/dragon_project/data/experiment_data/expdata/BCdata/AMS-BC-2016.dat"
OUTPUT_DIR = "/home/ljiayi/dragon_project/outputs/figures/"


def load_model(source):
    path = Path(source).expanduser()
    if not path.exists():
        raise ValueError(f"DRAGON2 input does not exist: {path}")
    if path.is_dir():
        files = list(path.glob("*.txt"))
        if not files:
            raise ValueError(f"No DRAGON2 .txt spectra in: {path}")
        path = max(files, key=lambda item: (item.stat().st_mtime, item.name))
    elif not path.is_file() or path.suffix != ".txt":
        raise ValueError(f"DRAGON2 input must be a directory or .txt spectrum: {path}")

    try:
        with path.open(encoding="utf-8") as stream:
            for count, line in enumerate(stream, 1):
                if line.strip() and not line.lstrip().startswith("#"):
                    header = line.split()
                    break
            else:
                raise ValueError(f"Empty DRAGON2 spectrum: {path}")
    except OSError as exc:
        raise ValueError(f"Cannot read DRAGON2 spectrum: {path}: {exc}") from exc

    if header[:2] != ["Energy", "[GeV]"]:
        raise ValueError(f"Unrecognized DRAGON2 header: {path}")
    keys = header[2:]
    needed = ("NUC_5010", "NUC_5011", "NUC_6012", "NUC_6013", "NUC_6014")
    if any(keys.count(name) != 1 for name in needed):
        raise ValueError(f"Missing or duplicate B/C isotope column: {path}")
    try:
        data = np.loadtxt(path, skiprows=count, comments="#", ndmin=2)
    except (OSError, ValueError) as exc:
        raise ValueError(f"Cannot parse DRAGON2 spectrum: {path}: {exc}") from exc

    if data.size == 0 or data.shape[1] != len(keys) + 1:
        raise ValueError(f"Empty or incomplete DRAGON2 spectrum: {path}")
    if not np.all(np.isfinite(data)):
        raise ValueError(f"Non-finite DRAGON2 values: {path}")
    energy = data[:, 0]
    if np.any(energy <= 0) or np.any(np.diff(energy) <= 0):
        raise ValueError(f"Invalid DRAGON2 energy grid: {path}")

    flux = {name: data[:, keys.index(name) + 1] for name in needed}
    if any(np.any(values < 0) for values in flux.values()):
        raise ValueError(f"Negative B/C isotope flux: {path}")
    boron = flux["NUC_5010"] + flux["NUC_5011"]
    carbon = flux["NUC_6012"] + flux["NUC_6013"] + flux["NUC_6014"]
    if np.any(carbon <= 0):
        raise ValueError(f"Zero carbon flux: {path}")
    return path, energy, boron / carbon


def load_ams(path):
    path = Path(path).expanduser()
    if not path.is_file():
        raise ValueError(f"AMS-02 data file does not exist: {path}")
    try:
        data = np.loadtxt(path, comments="#", ndmin=2)
    except (OSError, ValueError) as exc:
        raise ValueError(f"Cannot parse AMS-02 data: {path}: {exc}") from exc
    if data.size == 0 or data.shape[1] != 10:
        raise ValueError(f"AMS-02 data must have 10 numeric columns: {path}")
    if not np.all(np.isfinite(data)):
        raise ValueError(f"Non-finite AMS-02 values: {path}")
    if np.any(data[:, 0] <= 0) or np.any(data[:, 1] <= data[:, 0]):
        raise ValueError(f"Invalid AMS-02 energy bins: {path}")
    if np.any(data[:, 2] <= 0) or np.any(data[:, 3] < 0) or np.any(data[:, 9] < 0):
        raise ValueError(f"Invalid AMS-02 ratio or uncertainty: {path}")
    energy = np.sqrt(data[:, 0] * data[:, 1])
    if np.any(np.diff(energy) <= 0):
        raise ValueError(f"AMS-02 energy bins are not increasing: {path}")
    error = np.hypot(data[:, 3], data[:, 9])
    return energy, data[:, 2], error


def plot_bc(energy, model, obsx, obs, error, output=None):
    keep = (obsx >= energy[0]) & (obsx <= energy[-1])
    skipped = np.count_nonzero(~keep)
    if skipped:
        print(f"Skipped {skipped} AMS-02 points outside the DRAGON2 energy range.")
    if not np.any(keep):
        raise ValueError("DRAGON2 and AMS-02 energy ranges do not overlap")

    # Both horizontal axes are kinetic energy per nucleon in GeV/n.
    matched = np.interp(obsx[keep], energy, model)
    quotient = matched / obs[keep]
    residual = quotient - 1.0

    fig, axes = plt.subplots(3, 1, sharex=True, figsize=(8, 9))
    axes[0].plot(energy, model, label="DRAGON2 (LIS)")
    axes[0].errorbar(obsx, obs, yerr=error, fmt="o", markersize=3, capsize=2,
                     label="AMS-02 (TOA)")
    axes[0].set_title("B/C comparison: unmodulated model and AMS-02")
    axes[0].set_ylabel("B/C Ratio")
    axes[0].legend()

    axes[1].plot(obsx[keep], quotient, "o", markersize=3)
    axes[1].axhline(1, color="gray", linestyle="--")
    axes[1].set_ylabel("Model / Data")

    axes[2].plot(obsx[keep], residual, "o", markersize=3)
    axes[2].axhline(0, color="gray", linestyle="--")
    axes[2].set_ylabel("Fractional Residual")
    axes[2].set_xlabel("Kinetic Energy per Nucleon [GeV/n]")
    axes[2].set_xscale("log")
    plt.tight_layout()

    now = datetime.now(ZoneInfo("Asia/Tokyo"))
    stamp = now.strftime("%Y-%m-%d")
    time = now.strftime("%H%M")
    target = (Path(output).expanduser().resolve() if output is not None
              else Path(OUTPUT_DIR) / f"{stamp}_BCratio-{time}.png")
    if target.is_dir() or not target.suffix:
        target = target / f"{stamp}_BCratio-{time}.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(target, dpi=150)
    plt.close(fig)
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dragon", nargs="?", default=DRAGON_OUT,
                        help="DRAGON2 output directory or a .txt spectrum")
    parser.add_argument("--output", help="Exact figure path")
    args = parser.parse_args()
    try:
        path, energy, model = load_model(args.dragon)
        obsx, obs, error = load_ams(AMS_DATA)
        target = plot_bc(energy, model, obsx, obs, error, args.output)
    except (ValueError, OSError) as exc:
        parser.exit(1, f"Error: {exc}\n")
    print(f"DRAGON2 spectrum: {path}")
    print("Note: DRAGON2 LIS is compared with AMS-02 TOA; this is diagnostic only.")
    print(f"Saved figure: {target.resolve()}")


if __name__ == "__main__":
    main()
