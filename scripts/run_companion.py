"""Run one explicitly selected DRAGON2 input on companion."""

import argparse
from datetime import datetime, timedelta
import fcntl
import gzip
import json
import math
from pathlib import Path
import re
import shlex
import sys
import tempfile
import time
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dragon_utils import companion
from dragon_utils.xml_manager.xml_modifier import load_xml, get_param, find_one, calc_dz
from scripts.xml_batch import file_hash, copy_baseline, save_state

BASE = Path("/home/ljiayi/dragon_project")
PROGRAM = Path("/home/ljiayi/dragon/DRAGON2-Beta_version-master")
TOKYO = ZoneInfo("Asia/Tokyo")
ACTIVE = {"prepared", "launching", "running", "finalizing", "unknown"}
PATTERN = r"\d{4}-\d{2}-\d{2}_(?:(?:BCratio|pHe)_)?dimZ[1-9]\d*"

# The remote worker uses only the standard library and survives SSH disconnects.
REMOTE = r'''
import datetime, fcntl, hashlib, json, os, pathlib, subprocess, sys, traceback
from zoneinfo import ZoneInfo
request = json.loads(sys.argv[1])
op = request['op']
path = pathlib.Path(request['path'])
path.parent.mkdir(parents=True, exist_ok=True)
lock = path.with_suffix('.lock').open('a')
fcntl.flock(lock, fcntl.LOCK_EX)
state = json.loads(path.read_text()) if path.exists() else None
active = {'prepared', 'launching', 'running', 'finalizing', 'unknown'}
if op == 'reserve':
    if state and state['status'] in active:
        raise RuntimeError('Existing task requires fetch/status inspection; never relaunch automatically')
    spec = request['spec']
    directory = pathlib.Path(spec['program']) / 'output'
    names = [spec['stem'] + suffix for suffix in ('.txt', '.fits', '.fits.gz', '_spectrum.fits', '_spectrum.fits.gz')]
    history = [str(directory / name) for name in names if (directory / name).exists()]
    pathlib.Path(spec['remoteLog']).parent.mkdir(parents=True, exist_ok=True)
    with open(spec['remoteLog'], 'x') as stream:
        stream.write('# Companion single run\n')
    state = dict(spec, status='prepared', history=history)
    for item in spec['inputs']:
        pathlib.Path(item['remote']).parent.mkdir(parents=True, exist_ok=True)
elif op == 'abort':
    if state and state['token'] == request['token'] and state['status'] == 'prepared':
        state.update(status='failed', error='Input preparation/transfer aborted', exitcode=None)
elif op == 'launch':
    if not state or state['token'] != request['token'] or state['status'] != 'prepared':
        raise RuntimeError('Task is not reserved for this launch')
    for item in state['inputs']:
        digest = hashlib.sha256()
        with open(item['remote'], 'rb') as stream:
            for block in iter(lambda: stream.read(1048576), b''): digest.update(block)
        if digest.hexdigest() != item['sha256']: raise RuntimeError('Input SHA256 mismatch')
    for name in state['history']: pathlib.Path(name).unlink()
    state['status'] = 'launching'
elif op in ('status', 'worker'):
    if state is None: raise FileNotFoundError(path)
    if op == 'worker' and (state['token'] != request['token'] or state['status'] != 'launching'):
        raise RuntimeError('Worker launch token/status mismatch')
    if op == 'status' and state['status'] in {'launching', 'running', 'finalizing'}:
        try:
            fields = pathlib.Path('/proc/' + str(state['pid']) + '/stat').read_text().rsplit(')', 1)[1].split()
            boot = pathlib.Path('/proc/sys/kernel/random/boot_id').read_text().strip()
            if fields[19] != state['birth'] or fields[0] == 'Z' or boot != state['boot']:
                raise RuntimeError('Worker identity changed')
        except (OSError, RuntimeError):
            state.update(status='unknown', error='Worker disappeared without a completed exit record')
else:
    raise ValueError(op)
if op == 'worker':
    state.update(status='running', pid=os.getpid(),
                 birth=pathlib.Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()[19],
                 boot=pathlib.Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                 started=datetime.datetime.now(ZoneInfo('Asia/Tokyo')).isoformat())
temporary = path.with_suffix('.part')
temporary.write_text(json.dumps(state, indent=2) + '\n')
temporary.replace(path)
if op == 'launch':
    child = subprocess.Popen([sys.executable, '-c', request['code'], json.dumps(dict(op='worker', path=str(path), token=state['token']))],
                             stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             start_new_session=True, close_fds=True)
    state['pid'] = child.pid
    state['birth'] = pathlib.Path('/proc/' + str(child.pid) + '/stat').read_text().rsplit(')', 1)[1].split()[19]
    state['boot'] = pathlib.Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    temporary.write_text(json.dumps(state, indent=2) + '\n')
    temporary.replace(path)
fcntl.flock(lock, fcntl.LOCK_UN)
if op == 'worker':
    with open(state['remoteLog'], 'a', buffering=1) as log:
        try:
            program = pathlib.Path(state['program'])
            state['build'] = {}
            files = list(program.glob('*.cc')) + list(program.glob('*.f')) + list(program.glob('*.F')) + list((program / 'include').glob('*.h'))
            files += list((program / 'cparamlib').glob('*.c')) + list((program / 'cparamlib').glob('*.h'))
            files += [program / name for name in ('DRAGON', '.libs/DRAGON', '.libs/libDRAGON.so.0', '.libs/libTiXML.so.0', 'cparamlib/.libs/libcparamlib.so.0')]
            env = dict(os.environ)
            env['LD_LIBRARY_PATH'] = ':'.join([str(program / '.libs'), str(program / 'cparamlib/.libs'), '/home/ljiayi/.local/dragon/usr/lib/x86_64-linux-gnu', env.get('LD_LIBRARY_PATH', '')])
            dependencies = subprocess.run(['ldd', str(program / '.libs/DRAGON')], env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            log.write(dependencies.stdout)
            if dependencies.returncode or 'not found' in dependencies.stdout:
                raise RuntimeError('Unresolved executable dependencies')
            for line in dependencies.stdout.splitlines():
                parts = line.split()
                files += [pathlib.Path(part) for part in parts if part.startswith('/') and pathlib.Path(part).is_file()]
            for target in files:
                if not target.is_file(): continue
                digest = hashlib.sha256()
                with target.open('rb') as stream:
                    for block in iter(lambda: stream.read(1048576), b''): digest.update(block)
                state['build'][str(target)] = digest.hexdigest()
            log.write('Started: ' + state['started'] + '\nCommand: ./DRAGON ' + state['inputs'][0]['remote'] + '\n')
            log.flush()
            done = subprocess.run([str(program / 'DRAGON'), state['inputs'][0]['remote']], cwd=program,
                                  env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
            state.update(status='finalizing', exitcode=done.returncode)
            state['outputs'] = []
            if done.returncode: raise RuntimeError('DRAGON exit code ' + str(done.returncode))
            for item in state['expected']:
                target = program / 'output' / item['native']
                if not target.is_file() or not target.stat().st_size:
                    raise RuntimeError('Missing or empty output: ' + str(target))
                digest = hashlib.sha256()
                with target.open('rb') as stream:
                    for block in iter(lambda: stream.read(1048576), b''): digest.update(block)
                state['outputs'].append(dict(item, remote=str(target), size=target.stat().st_size, sha256=digest.hexdigest()))
            state['status'] = 'succeeded'
        except BaseException as exc:
            traceback.print_exc(file=log)
            state.update(status='failed', error=str(exc))
            state.setdefault('exitcode', None)
        state['ended'] = datetime.datetime.now(ZoneInfo('Asia/Tokyo')).isoformat()
        log.write('\nEnded: ' + state['ended'] + '\nExit code: ' + str(state['exitcode']) + '\nStatus: ' + state['status'] + '\n')
    fcntl.flock(lock, fcntl.LOCK_EX)
    temporary.write_text(json.dumps(state, indent=2) + '\n')
    temporary.replace(path)
    fcntl.flock(lock, fcntl.LOCK_UN)
else:
    print(json.dumps(state))
'''


def inspect_xml(path):
    """Validate the selected input without changing any bytes."""
    path = Path(path).expanduser().resolve()
    if not path.is_file() or path.suffix != ".xml":
        raise ValueError(f"Expected an explicit XML file: {path}")
    source = path.with_suffix(".source.param")
    if not source.is_file():
        raise FileNotFoundError(f"Missing exact source abundance: {source}")
    doc = load_xml(path)
    values = {}
    for name in ("L", "Rmax", "Ekmin", "Ekmax", "Ekfactor", "DimZ", "Zmin", "Zmax"):
        value = get_param(doc, name)
        values[name] = int(value) if name in {"DimZ", "Zmin", "Zmax"} else float(value)
    if not all(math.isfinite(value) for value in values.values()):
        raise ValueError("Non-finite XML grid values")
    if values["L"] <= 0 or values["Rmax"] <= 0 or values["DimZ"] < 3:
        raise ValueError("L/Rmax must be positive and DimZ must be at least 3")
    if not 0 < values["Ekmin"] < values["Ekmax"] or values["Ekfactor"] <= 1:
        raise ValueError("Invalid energy grid")
    if values["Zmin"] != 1 or values["Zmax"] < 6:
        raise ValueError("Both plots require Zmin=1 and Zmax>=6 (p, He, B, C)")
    grid = find_one(doc, "//Grid")
    kind = grid.get("type")
    if kind not in {"2D", "3D"}:
        raise ValueError("Grid type must be 2D or 3D")
    axes = {"Z": values["L"]}
    axes.update({axis: values["Rmax"] for axis in (("X", "Y") if kind == "3D" else ("R",))})
    for axis, extent in axes.items():
        size = int(find_one(doc, f"//Grid/Dim{axis}").get("value"))
        if size < 3:
            raise ValueError(f"Dim{axis} must be at least 3")
        nodes = grid.findall(f"Dim{axis}_division")
        if len(nodes) > 1:
            raise ValueError(f"Duplicate Dim{axis}_division")
        if nodes:
            points = [float(item) for item in nodes[0].get("points", "").split(";")]
            if len(points) != size or not all(math.isfinite(item) for item in points):
                raise ValueError(f"Dim{axis} must match the finite division point count")
            if any(right <= left for left, right in zip(points, points[1:])):
                raise ValueError(f"Dim{axis} division points must increase")
            if axis != "R" and not points[0] < 0 < points[-1]:
                raise ValueError(f"Dim{axis} division must span zero")
            if axis == "R" and (points[0] < 0 or points[-1] <= 0):
                raise ValueError("Invalid radial division")
            if axis == "Z":
                values.update(zgrid="nonuniform", zpoints=points, dz=None)
    if "zgrid" not in values:
        values.update(zgrid="uniform", dz=calc_dz(values["L"], values["DimZ"]))
    output = find_one(doc, "//Output")
    if output.find("OnlyPrimaries") is not None:
        raise ValueError("OnlyPrimaries omits columns needed by the two diagnostics")
    flags = {}
    for name in ("fullstore", "partialstore"):
        if len(output.findall(name)) > 1:
            raise ValueError(f"Duplicate output flag: {name}")
        flags[name] = output.find(name) is not None
    if output.find("timestepstore") is not None:
        raise ValueError("timestepstore is outside the single-round output manifest")
    abundances = {}
    for number, line in enumerate(source.read_text().splitlines(), 1):
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) < 5 or (len(parts) - 3) % 2:
            raise ValueError(f"Invalid source abundance row {number}")
        uid = int(parts[0])
        data = [float(item) for item in parts[1:]]
        if uid in abundances or not all(math.isfinite(item) for item in data) or data[0] < 0:
            raise ValueError(f"Invalid/duplicate source abundance at row {number}")
        abundances[uid] = data[0]
    needed = (1001, 2003, 2004, 5010, 5011, 6012, 6013, 6014)
    if any(uid not in abundances for uid in needed) or any(abundances[uid] <= 0 for uid in (1001, 2004, 6012)):
        raise ValueError("Source abundance lacks required p/He/B/C species or primary injection")
    values.update(gridtype=kind, **flags)
    return path, source, values


def make_plan(xml, now=None):
    """Fix the round date and derive exact input/output paths."""
    now = now or datetime.now(TOKYO)
    path, source, values = inspect_xml(xml)
    stem = f"{now:%Y-%m-%d}_dimZ{values['DimZ']}"
    inputs = []
    for original, suffix in ((path, ".xml"), (source, ".source.param")):
        target = BASE / "data/processed" / (stem + suffix)
        inputs.append(dict(original=str(original), local=str(target), remote=str(target), sha256=file_hash(original)))
    expected = [dict(native=stem + ".txt", archive=stem + ".txt", kind="ascii")]
    for flag, suffix, archive, kind in (("fullstore", ".fits.gz", ".fits.gz", "spatial"),
                                        ("partialstore", "_spectrum.fits.gz", "-spectrum.fits.gz", "solar")):
        if values[flag]:
            expected.append(dict(native=stem + suffix, archive=stem + archive, kind=kind))
    return dict(stem=stem, date=now.strftime("%Y-%m-%d"), startedLocal=now.isoformat(),
                params=values, inputs=inputs, expected=expected, program=str(PROGRAM),
                figures={name: str(BASE / "outputs/figures" / f"{now:%Y-%m-%d}_{name}_dimZ{values['DimZ']}.png")
                         for name in ("BCratio", "pHe")})


def new_log():
    """Reserve a dated Markdown log without overwriting earlier logs."""
    now = datetime.now(TOKYO)
    folder = BASE / "logs"
    folder.mkdir(parents=True, exist_ok=True)
    while True:
        path = folder / f"{now:%Y-%m-%d_%H-%M-%S}.md"
        try:
            path.touch(exist_ok=False)
            return path
        except FileExistsError:
            now += timedelta(seconds=1)


def rpc(op, stem, log, **kwargs):
    """Call one logged remote operation with quoted arguments."""
    request = dict(op=op, path=str(BASE / "outputs/workflow" / (stem + ".json")), **kwargs)
    if op == "launch":
        request["code"] = REMOTE
    done = companion.execute(["python3", "-c", REMOTE, json.dumps(request)], log, capture=True)
    return json.loads(done.stdout)


def validate_data(path):
    """Reuse both plotting readers for spectrum completeness checks."""
    import matplotlib
    matplotlib.use("Agg")
    from dragon_utils.plotting import BCfitting, pHefitting
    BCfitting.load_model(path)
    pHefitting.load_model(path)


def validate_fits(path):
    """Check gzip integrity and parse every FITS HDU."""
    from astropy.io import fits
    if str(path).endswith(".gz"):
        with gzip.open(path, "rb") as stream:
            while stream.read(1048576):
                pass
    with fits.open(path, checksum=True) as hdus:
        hdus.verify("exception")
        if len(hdus) < 2:
            raise ValueError(f"FITS lacks particle HDUs: {path}")
        for hdu in hdus[1:]:
            if hdu.data is None or not hdu.data.size:
                raise ValueError(f"Empty particle FITS HDU: {path}")


def pull(state, log):
    """Retrieve only successful manifest files; keep failure logs too."""
    remote_log = state.get("remoteLog")
    if remote_log:
        runtime = BASE / "logs" / Path(remote_log).name
        companion.download(remote_log, runtime, log)
        if state["status"] in {"succeeded", "failed"}:
            duration = None
            with runtime.open(encoding="utf-8", errors="replace") as stream:
                for line in stream:
                    text = line.rstrip("\r\n")
                    if re.fullmatch(r"Solution found in .+ s\.", text):
                        duration = text
            if duration:
                state["duration"] = duration
                print(duration, flush=True)
            elif state["status"] == "succeeded":
                print(f"Warning: DRAGON duration line not found in {runtime}", file=sys.stderr, flush=True)
    if state["status"] != "succeeded" or state.get("exitcode") != 0:
        raise RuntimeError(f"Remote status: {state['status']}; {state.get('error', '')}. Use fetch to inspect again.")
    outputs = state.get("outputs", [])
    if [(item["native"], item["archive"]) for item in outputs] != [(item["native"], item["archive"]) for item in state["expected"]]:
        raise ValueError("Remote output manifest differs from submitted XML")
    folder = BASE / "data/dragon_output"
    folder.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="companion-", dir=BASE / "outputs/workflow") as temp:
        for item in outputs:
            target = folder / item["archive"]
            staged = Path(temp) / target.name
            companion.download(item["remote"], staged, log)
            if staged.stat().st_size != item["size"] or file_hash(staged) != item["sha256"]:
                raise ValueError(f"Returned output hash/size mismatch: {target}")
            if item["kind"] == "ascii":
                validate_data(staged)
            else:
                validate_fits(staged)
        for item in outputs:
            target = folder / item["archive"]
            (Path(temp) / target.name).replace(target)
            item["local"] = str(target)
    state["localStatus"] = "retrieved"


def draw(state, log):
    """Plot both diagnostics from this round's exact verified spectrum."""
    if state.get("localStatus") not in {"retrieved", "plotted", "plotFailed"}:
        raise ValueError("Retrieve and validate the successful task before plotting")
    for item in state["outputs"]:
        if file_hash(item["local"]) != item["sha256"]:
            raise ValueError(f"Archived data changed: {item['local']}")
    spectrum = next(item["local"] for item in state["outputs"] if item["kind"] == "ascii")
    state["plots"] = {}
    try:
        for name, script in (("BCratio", "BCfitting.py"), ("pHe", "pHefitting.py")):
            target = Path(state["figures"][name])
            target.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(prefix="companion-", suffix=".png", dir=target.parent, delete=False) as temp:
                staged = Path(temp.name)
                try:
                    companion.run_command([sys.executable, ROOT / "dragon_utils/plotting" / script,
                                           spectrum, "--output", staged], log)
                    if not staged.is_file() or not staged.stat().st_size:
                        raise ValueError(f"Plot not created: {target}")
                    staged.replace(target)
                finally:
                    staged.unlink(missing_ok=True)
            state["plots"][name] = dict(path=str(target), sha256=file_hash(target))
        state["localStatus"] = "plotted"
    except BaseException:
        state["localStatus"] = "plotFailed"
        raise


def run(log, state):
    """Submit exactly one round, then wait and retrieve its completed outputs."""
    target = BASE / "outputs/workflow" / (state["stem"] + ".json")
    state.update(token=file_hash(log) + datetime.now(TOKYO).isoformat(), remoteLog=str(new_log()),
                 localLog=str(log), status="preparing")
    reserved = False
    try:
        rpc("reserve", state["stem"], log, spec=state)
        reserved = True
        save_state(target, state)
        for item in state["inputs"]:
            if item["original"] != item["local"]:
                copy_baseline(item["original"], item["local"], overwrite=True)
            if file_hash(item["local"]) != item["sha256"]:
                raise ValueError("Input changed during preparation")
            companion.upload(item["local"], item["remote"], log)
        state = rpc("launch", state["stem"], log, token=state["token"])
        save_state(target, state)
        try:
            view = shlex.join([*companion.SSH, companion.HOST,
                               shlex.join(["tail", "-n", "60", "-F", "--", state["remoteLog"]])])
            display = "#{session_name}:#{window_index}.#{pane_index}"
            try:
                viewer = companion.run_command(["tmux", "new-session", "-d", "-s", "dragon_log", "-n", state["stem"],
                                                "-P", "-F", display, view], log, capture=True)
            except RuntimeError:
                viewer = companion.run_command(["tmux", "new-window", "-d", "-t", "=dragon_log:", "-n", state["stem"],
                                                "-P", "-F", display, view], log, capture=True)
            state["monitor"] = viewer.stdout.strip()
            companion.run_command(["tmux", "select-window", "-t", "=" + state["monitor"].rsplit(".", 1)[0]], log)
            print(f"Log viewer: {state['monitor']} (selected automatically); attach if needed: tmux attach -t dragon_log", flush=True)
        except (OSError, RuntimeError) as exc:
            state["monitorError"] = str(exc)
            print(f"Warning: log viewer unavailable: {exc}; remote calculation is retained", file=sys.stderr, flush=True)
        save_state(target, state)
        while state["status"] in {"launching", "running", "finalizing"}:
            print(f"{state['stem']}: {state['status']}; fetch can resume after disconnect", flush=True)
            time.sleep(20)
            state.update(rpc("status", state["stem"], log))
            save_state(target, state)
        pull(state, log)
        save_state(target, state)
        draw(state, log)
    except BaseException as exc:
        state["localError"] = str(exc)
        if reserved:
            try:
                remote = rpc("abort", state["stem"], log, token=state["token"])
                for key in ("status", "exitcode", "error", "ended", "build"):
                    if key in remote:
                        state[key] = remote[key]
                if state.get("remoteLog"):
                    companion.download(state["remoteLog"], state["remoteLog"], log)
            except Exception as recovery:
                state["recoveryError"] = str(recovery)
        raise
    finally:
        if reserved:
            save_state(target, state)
    return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="mode", required=True)
    submit = commands.add_parser("run", help="Run one user-checked XML")
    submit.add_argument("xml")
    submit.add_argument("--preview", action="store_true", help="Validate/print plan without writes or SSH")
    for mode in ("fetch", "plot"):
        entry = commands.add_parser(mode, help="Retrieve remote status/results" if mode == "fetch" else "Remake local figures")
        entry.add_argument("stem", help="Exact YYYY-MM-DD_dimZN round stem; legacy stems also accepted")
    for entry in (submit, commands.choices["fetch"], commands.choices["plot"]):
        entry.add_argument("--overwrite", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        if args.mode == "run" and args.preview:
            print(json.dumps(make_plan(args.xml), ensure_ascii=False, indent=2))
            return
        plan = make_plan(args.xml) if args.mode == "run" else None
        stem = plan["stem"] if plan else args.stem
        if not re.fullmatch(PATTERN, stem):
            raise ValueError("Invalid round stem")
        folder = BASE / "outputs/workflow"
        folder.mkdir(parents=True, exist_ok=True)
        with (folder / (stem + ".lock")).open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            log = new_log()
            target = folder / (stem + ".json")
            if args.mode == "run":
                state = run(log, plan)
            else:
                state = json.loads(target.read_text()) if target.exists() else {}
                try:
                    if args.mode == "fetch":
                        remote = rpc("status", stem, log)
                        if state.get("token") and state["token"] != remote["token"]:
                            raise ValueError("Remote task was replaced; local token differs")
                        state.update(remote)
                        pull(state, log)
                    else:
                        draw(state, log)
                except BaseException as exc:
                    state["localError"] = str(exc)
                    raise
                finally:
                    if state:
                        save_state(target, state)
            print(f"Status: {state.get('localStatus', state['status'])}\nState: {target}\nLog: {log}")
            labels = {"ascii": "ASCII", "spatial": "FITS fullstore", "solar": "FITS partialstore"}
            for item in state.get("outputs", []):
                if item.get("local"):
                    print(f"{labels[item['kind']]}: {item['local']}")
            for item in state.get("plots", {}).values():
                print(f"Figure: {item['path']}")
    except (OSError, ValueError, RuntimeError, KeyError) as exc:
        parser.exit(1, f"Error: {exc}\n")
    except KeyboardInterrupt:
        parser.exit(130, "Interrupted. Remote task is retained; use fetch before any new run.\n")


if __name__ == "__main__":
    main()
