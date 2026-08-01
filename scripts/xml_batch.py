from __future__ import annotations

import hashlib
import json
import shutil
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dragon_utils.xml_manager.xml_modifier import modify_xml


@dataclass(frozen=True)
class ModelSpec:
    name: str
    params: Mapping[str, object]
    drops: tuple[str, ...] = ()


def timestamp() -> str:
    """Return a concise timestamp for generated records."""

    return datetime.now().astimezone().strftime("%Y-%m-%d-%H-%M-%S")


def file_hash(path: str | Path) -> str:
    """Calculate a SHA256 digest for one file."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def check_new(path: str | Path, overwrite: bool = False) -> Path:
    """Reject an existing output unless overwrite is enabled."""

    target = Path(path)
    if target.exists() and not overwrite:
        raise FileExistsError(f"Refusing to overwrite existing file: {target}")
    return target


def make_dirs(paths: Sequence[str | Path]) -> None:
    """Create all required directories."""

    for path in paths:
        Path(path).mkdir(parents=True, exist_ok=True)


def write_log(path: str | Path, message: str) -> None:
    """Append one timestamped line to a Markdown log."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    line = f"[{datetime.now().astimezone().isoformat(timespec='seconds')}] {message}"
    with target.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def save_state(path: str | Path, state: Mapping[str, object]) -> Path:
    """Write the current batch state as JSON."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(state, ensure_ascii=False, indent=2, default=str) + "\n"
    target.write_text(text, encoding="utf-8")
    return target


def safe_name(name: str) -> str:
    """Validate a model name before using it in output paths."""

    if not name or Path(name).name != name or name in {".", ".."}:
        raise ValueError(f"Invalid model name: {name!r}")
    return name


def model_paths(
    model: ModelSpec,
    xml_dir: str | Path,
    diff_dir: str | Path,
    prefix: str = "",
) -> dict[str, Path]:
    """Build XML, source, and diff paths for one model."""

    name = safe_name(model.name)
    stem = f"{prefix}_{name}" if prefix else name
    return {
        "xml": Path(xml_dir) / f"{stem}.xml",
        "source": Path(xml_dir) / f"{stem}.source.param",
        "diff": Path(diff_dir) / f"{stem}_baseline.diff",
    }


def copy_baseline(
    baseline: str | Path,
    output: str | Path,
    overwrite: bool = False,
) -> Path:
    """Copy a baseline XML without changing its serialized form."""

    source = Path(baseline)
    if not source.is_file():
        raise FileNotFoundError(source)
    target = check_new(output, overwrite)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return target


def prepare_models(
    models: Sequence[ModelSpec],
    baseline: str | Path,
    source: str | Path,
    xml_dir: str | Path,
    diff_dir: str | Path,
    log_dir: str | Path,
    state: str | Path | None = None,
    prefix: str = "",
    overwrite: bool = False,
) -> dict[str, object]:
    """Generate XML, source, diff, log, and state artifacts for models."""

    base = Path(baseline)
    source_path = Path(source)
    xml_path = Path(xml_dir)
    diff_path = Path(diff_dir)
    log_path = Path(log_dir)
    if not base.is_file():
        raise FileNotFoundError(base)
    if not source_path.is_file():
        raise FileNotFoundError(source_path)

    stamp = timestamp()
    log = log_path / f"{stamp}_xml.md"
    state_path = Path(state) if state is not None else log_path / f"{stamp}_state.json"
    make_dirs((xml_path, diff_path, log_path, state_path.parent))
    check_new(log, overwrite)
    check_new(state_path, overwrite)

    targets = []
    for model in models:
        paths = model_paths(model, xml_path, diff_path, prefix)
        for path in paths.values():
            check_new(path, overwrite)
        targets.append((model, paths))

    record = {
        "taskStart": datetime.now().astimezone().isoformat(timespec="seconds"),
        "baseline": str(base),
        "baselineSha256": file_hash(base),
        "source": str(source_path),
        "sourceSha256": file_hash(source_path),
        "log": str(log),
        "state": str(state_path),
        "models": {},
    }
    write_log(log, f"Batch started with {len(targets)} models")
    save_state(state_path, record)

    for model, paths in targets:
        write_log(log, f"Preparing model {model.name}")
        result = modify_xml(
            base,
            model.params,
            paths["xml"],
            paths["diff"],
            drops=model.drops,
        )
        shutil.copy2(source_path, paths["source"])
        item = {
            "params": dict(model.params),
            "drops": list(model.drops),
            "xml": str(paths["xml"]),
            "xmlSha256": file_hash(paths["xml"]),
            "source": str(paths["source"]),
            "sourceSha256": file_hash(paths["source"]),
            "diff": str(paths["diff"]),
            "diffSha256": file_hash(paths["diff"]),
            "changed": result["changed"],
            "removed": result["removed"],
        }
        record["models"][model.name] = item
        save_state(state_path, record)
        write_log(log, f"Prepared model {model.name}")

    record["taskEnd"] = datetime.now().astimezone().isoformat(timespec="seconds")
    save_state(state_path, record)
    write_log(log, "Batch completed")
    return record
