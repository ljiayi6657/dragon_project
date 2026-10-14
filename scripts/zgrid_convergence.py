"""Compare DRAGON2 vertical grids within 0.1 to 50000 GeV/n kinetic energy."""

import argparse
from contextlib import redirect_stdout
import csv
from datetime import date
import io
import json
import os
from pathlib import Path
import re
import sys
import tempfile

import numpy as np
from lxml import etree


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dragon_utils.plotting import BCfitting as bc
from dragon_utils.plotting import pHefitting as phe
from dragon_utils.xml_manager.xml_modifier import calc_dz, get_param, load_xml


PATTERN = re.compile(r"(\d{4}-\d{2}-\d{2})_dimZ([1-9]\d*)\.txt")
FIELDS = (
    "date", "dimZ", "dz_kpc", "previous_dimZ", "reference_dimZ",
    "bc_adj_max_pct", "p_adj_max_pct", "he_adj_max_pct",
    "overall_adj_max_pct", "overall_ref_max_pct", "source_file",
)
LABELS = {"bc": "B/C", "p": "proton", "He": "helium"}
EMIN = 0.1
EMAX = 50000.0


def warn(message):
    print(f"Warning: {message}", file=sys.stderr)


def discover(directory):
    """Select the latest dated TXT for each DimZ, then sort by DimZ."""
    directory = Path(directory).expanduser().resolve()
    if not directory.is_dir():
        raise ValueError(f"Input directory does not exist: {directory}")
    selected = {}
    for path in sorted(directory.glob("*.txt")):
        match = PATTERN.fullmatch(path.name)
        if not path.is_file() or match is None:
            warn(f"Ignoring TXT outside YYYY-MM-DD_dimZ<N>.txt format: {path.name}")
            continue
        stamp, dimz = match.groups()
        dimz = int(dimz)
        try:
            date.fromisoformat(stamp)
            if dimz < 2:
                raise ValueError("DimZ must exceed one")
        except ValueError as exc:
            warn(f"Ignoring invalid filename {path.name}: {exc}")
            continue
        if dimz in selected:
            old = selected[dimz]
            chosen = max(old, path, key=lambda item: item.name)
            warn(f"Duplicate DimZ={dimz}: {old.name}, {path.name}; using {chosen.name}")
            path = chosen
        selected[dimz] = path
    if not selected:
        raise ValueError(f"No matching simulation TXT files in {directory}")
    return sorted(selected.items())


def load_spectra(directory):
    """Reuse the project readers and reject unsuitable physical values."""
    models = []
    for dimz, source in discover(directory):
        try:
            _, energy, ratio = bc.load_model(source)
            with redirect_stdout(io.StringIO()):
                _, axis, flux = phe.load_model(source)
            if not np.array_equal(energy, axis):
                raise ValueError("B/C and p/He readers returned different energy grids")
            if not np.all(np.isfinite(ratio)) or np.any(ratio <= 0):
                raise ValueError("B/C must be finite and positive for relative comparisons")
        except (OSError, ValueError, UnicodeError) as exc:
            warn(f"Skipping invalid spectrum {source.name}: {exc}")
            continue
        models.append({"dimZ": dimz, "source": source, "energy": energy,
                       "bc": ratio, "flux": flux})
    if not models:
        raise ValueError("No valid spectra containing B/C, primary + secondary p, and He-3/4")
    return models


def make_grids(models, points):
    """Intersect the energy window with shared coverage without extrapolation."""
    if not isinstance(points, int) or isinstance(points, bool) or points < 2:
        raise ValueError("--points must be an integer of at least 2")
    grids = {}
    lo = max(EMIN, max(model["energy"][0] for model in models))
    hi = min(EMAX, min(model["energy"][-1] for model in models))
    if hi <= lo:
        raise ValueError("No common B/C coverage within the deviation energy window")
    grids["bc"] = np.geomspace(lo, hi, points)
    for mode, phi in (("p", phe.PHI_P), ("He", phe.PHI_HE)):
        if not np.isfinite(phi) or phi < 0:
            raise ValueError(f"Invalid existing {mode} solar modulation potential")
        bounds = []
        for model in models:
            energy = model["energy"]
            for name, charge, massnum, mass in phe.SPECIES[mode]:
                # Apply the window to TOA energy, retaining the full LIS input.
                low = max(energy[0] - charge * phi / massnum, EMIN)
                high = min(energy[-1] - charge * phi / massnum, EMAX)
                if high <= low:
                    raise ValueError(f"No {name} TOA coverage within the deviation energy "
                                     f"window in {model['source'].name}")
                # Invert the existing kinetic conversion only to determine coverage.
                bounds.append((massnum / charge * np.sqrt(low * (low + 2 * mass)),
                               massnum / charge * np.sqrt(high * (high + 2 * mass))))
        lo = max(bound[0] for bound in bounds)
        hi = min(bound[1] for bound in bounds)
        # Move endpoints inward to avoid floating-point boundary extrapolation.
        lo *= 1 + 1e-12
        hi *= 1 - 1e-12
        if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
            raise ValueError(f"No common {LABELS[mode]} TOA rigidity interval")
        grid = np.geomspace(lo, hi, points)
        if not all(np.all(phe.coverage(model["energy"], grid, mode, phi))
                   for model in models):
            raise ValueError(f"Common {LABELS[mode]} grid exceeds shifted LIS coverage")
        grids[mode] = grid
    return grids


def spacing(source, dimz):
    """Read only matching workflow metadata or its corresponding XML."""
    state = ROOT / "outputs/workflow" / f"{source.stem}.json"
    paths = [ROOT / "data/processed" / f"{source.stem}.xml"]
    if state.is_file():
        try:
            record = json.loads(state.read_text(encoding="utf-8"))
            if record.get("stem", source.stem) != source.stem:
                raise ValueError("Workflow stem differs from the TXT filename")
            params = record.get("params", {})
            if float(params["DimZ"]) != dimz:
                raise ValueError("Workflow DimZ differs from the TXT filename")
            if params.get("zgrid") == "nonuniform":
                warn(f"{source.name}: nonuniform Z grid; dz_kpc left empty")
                return None
            if params.get("zgrid") == "uniform":
                extent = float(params["L"])
                if not np.isfinite(extent) or extent <= 0:
                    raise ValueError("Invalid workflow L")
                return calc_dz(extent, dimz)
            for item in record.get("inputs", []):
                if item.get("local"):
                    path = Path(item["local"]).expanduser()
                    if path.name == f"{source.stem}.xml":
                        paths.append(path if path.is_absolute() else ROOT / path)
        except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
            warn(f"{state.name}: unusable metadata ({exc}); trying matching XML")
    for path in dict.fromkeys(paths):
        if not path.is_file():
            continue
        try:
            doc = load_xml(path)
            if int(get_param(doc, "DimZ")) != dimz:
                raise ValueError("XML DimZ differs from the TXT filename")
            if doc.root.xpath("//Grid/DimZ_division"):
                warn(f"{source.name}: nonuniform Z grid; dz_kpc left empty")
                return None
            extent = float(get_param(doc, "L"))
            if not np.isfinite(extent) or extent <= 0:
                raise ValueError("Invalid XML L")
            return calc_dz(extent, dimz)
        except (OSError, ValueError, KeyError, etree.XMLSyntaxError) as exc:
            warn(f"{path.name}: unusable XML ({exc})")
    warn(f"{source.name}: reliable uniform-grid L unavailable; dz_kpc left empty")
    return None


def maxdiff(new, old, label):
    """Use the second spectrum as the relative-difference denominator."""
    if new.shape != old.shape or new.size == 0:
        raise ValueError(f"{label}: comparison arrays must have matching nonempty shapes")
    if (not np.all(np.isfinite(new)) or not np.all(np.isfinite(old))
            or np.any(new <= 0) or np.any(old <= 0)):
        raise ValueError(f"{label}: relative comparisons require finite positive values")
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        diff = np.abs(new - old) / np.abs(old) * 100
    if not np.all(np.isfinite(diff)):
        raise ValueError(f"{label}: relative differences overflowed; cannot compare reliably")
    return float(np.max(diff))


def analyze(directory, points=200):
    models = load_spectra(directory)
    grids = make_grids(models, points)
    for model in models:
        energy = model["energy"]
        values = {"bc": np.interp(grids["bc"], energy, model["bc"])}
        for mode, phi in (("p", phe.PHI_P), ("He", phe.PHI_HE)):
            values[mode] = phe.rigidity(energy, model["flux"], grids[mode], mode, phi)
        model["values"] = values
    reference = models[-1]
    rows = []
    for index, model in enumerate(models):
        source = model["source"]
        row = dict.fromkeys(FIELDS)
        row.update(date=source.name[:10], dimZ=model["dimZ"],
                   dz_kpc=spacing(source, model["dimZ"]),
                   reference_dimZ=reference["dimZ"], source_file=source.name)
        ref = [maxdiff(model["values"][key], reference["values"][key], LABELS[key])
               for key in LABELS]
        row["overall_ref_max_pct"] = max(ref)
        if index:
            previous = models[index - 1]
            adjacent = [maxdiff(model["values"][key], previous["values"][key], LABELS[key])
                        for key in LABELS]
            row["previous_dimZ"] = previous["dimZ"]
            for column, value in zip(FIELDS[5:8], adjacent):
                row[column] = value
            row["overall_adj_max_pct"] = max(adjacent)
        rows.append(row)
    return rows, grids


def write_csv(rows, target):
    """Replace the CSV atomically only after all comparisons succeed."""
    target = Path(target).expanduser().resolve()
    if target.suffix.lower() != ".csv":
        raise ValueError(f"Output must be a .csv file: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="",
                                         dir=target.parent, prefix=f".{target.stem}-",
                                         suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            writer = csv.DictWriter(stream, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "data/dragon_output",
                        help="Simulation TXT directory (default: project data/dragon_output)")
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/csv/zgrid_convergence.csv",
                        help="CSV file (default: project outputs/csv/zgrid_convergence.csv)")
    parser.add_argument("--points", type=int, default=200,
                        help="Logarithmic comparison points per quantity (default: 200)")
    args = parser.parse_args()
    try:
        rows, grids = analyze(args.input, args.points)
        target = write_csv(rows, args.output)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Error: {exc}\n")
    print(f"Valid simulations: {len(rows)}")
    print("DimZ (ascending): " + ", ".join(str(row["dimZ"]) for row in rows))
    print(f"Reference DimZ: {rows[-1]['reference_dimZ']}")
    print(f"Deviation energy window: {EMIN:g} to {EMAX:g} GeV/n "
          "(kinetic; B/C LIS, proton/helium TOA)")
    for key, grid in grids.items():
        unit = "GeV/n" if key == "bc" else "GV"
        print(f"{LABELS[key]} common range: {grid[0]:.8g} to {grid[-1]:.8g} {unit}; "
              f"{grid.size} points")
    if len(rows) > 1:
        latest = rows[-1]
        print(f"Latest adjacent comparison: {latest['dimZ']} vs {latest['previous_dimZ']}")
        for label, column in zip(("B/C", "proton", "helium", "overall"), FIELDS[5:9]):
            print(f"  {label} maximum relative difference: {latest[column]:.8g}%")
    else:
        print("Latest adjacent comparison: unavailable (only one valid DimZ)")
    print(f"Updated CSV: {target}")


if __name__ == "__main__":
    main()
