# %%
### Imports
import numpy as np
import pandas as pd

from skopt import Optimizer
from skopt.space import Real
from sklearn.preprocessing import StandardScaler

import argparse
import csv
import json
import re
import os
import sys
import shutil
import pickle
from datetime import datetime
from pathlib import Path
import shlex
import subprocess
import time
import logging
import getpass
import random
from zoneinfo import ZoneInfo
import yaml

ROOT = Path(__file__).resolve().parents[3]
TOKYO = ZoneInfo("Asia/Tokyo")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dragon_utils.xml_manager.parameter_map import PARAM_MAP
from dragon_utils.xml_manager.xml_modifier import find_one, get_param, load_xml, modify_xml, render_xml, set_param
from dragon_utils.CALETana_functions.datareader import readamsproflxvals, readamsHEflxvals, readamsBCratio
from dragon_utils.data_processing.physics import SM_output
from dragon_utils.data_processing.statistic_analysis import chisquare
from dragon_utils import companion
from scripts import run_companion as remote
from scripts.xml_batch import file_hash

# %%
def update_data(fitSpectra_path):
    directory = os.path.dirname(fitSpectra_path)
    file_name = os.path.basename(fitSpectra_path)
    
    os.chdir(directory)
    command = f"./{file_name}"    
    filenumber = None

    # Execute fitspectra-xxx in interactive mode (read write to console possible)
    with subprocess.Popen(command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1, universal_newlines=True) as process:
        logging.info("\n")
        logging.info("-"*20+"Fitting potential new simulations"+"-"*20)
        start_time = time.time()                                    # To check whether we are caught in a loop
        
        while True:
            output = process.stdout.readline().strip()              # IMPORTANT: in fitSpectra-xxx's "input('text')" prompts end all the lines with 'text\n', otherwise readline() cannnot read the input prompt and we wait forever!!!
            if type(output)!=str: output = output.decode()
            
            if output: 
                start_time=time.time()
                if "select order parameter" in output: break        # if we arrive at ordering of finished fits, end the fitting
                logging.info(f"{output}")
                if "enter maximum age of files" in output: 
                    process.stdin.write("0\n")
                    process.stdin.flush()
                    logging.info("0")
                if "use saved prefit data?" in output:
                    process.stdin.write("y\n")
                    process.stdin.flush()
                    logging.info("y")
                if "starting prefit" in output:             # read out current simulation number
                    match = re.search(r"\d+", output)
                    if match: filenumber = int(match.group())
    
            if output == "" and process.poll() is not None: break   # if there is no output and no further communication, end the fitting
            if time.time() - start_time > 300: raise TimeoutError("No processable communication for > 5 minutes. Terminated simulation fitting!")
    if filenumber == None: 
        logging.warning("No new simulation number could be obtained. Two conflicting requests trying to fit likely. Waiting random time before next request.")
        time.sleep(random.randint(0, 300))      
    return filenumber

# %%
def load_data(dragon_datapath,bayes_settings,preset_parameters):
    logging.info("\n")
    logging.info("-"*20+"Loading and processing new data"+"-"*20)

    # 1. Load data and save in pd.DataFrame
    data_loaded = False
    while not data_loaded:
        try:
            with open(dragon_datapath, "rb") as file:
                hashdict,foundfiles,globpardict,pflxs,pfs,x2s,x2dict,vx2s,vx2dict,rx2s,rx2dict,px2s,px2dict,hx2s,hx2dict,fx2s,fx2dict,qx2s,qx2dict,vfx2s,vfx2dict,likes,likedict,mlikes,mlikedict,tlikes,tlikedict,qlikes,qlikedict,slikes,slikedict,mx2s,mx2dict,sx2s,sx2dict,cx2s,cx2dict,tss,tsdict,faultfiles,faultpardict,corrfactlist = pickle.load(file)
                lossparamdict={"x":x2s,"v":vx2s,"r":rx2s,"p":px2s,"h":hx2s,"f":fx2s,"q":qx2s,"vf":vfx2s,"l":likes,"ml":mlikes,"tl":tlikes,"ql":qlikes,"sl":slikes,"m":mx2s,"s":sx2s,"c":cx2s}
                globpardict["Y"]=lossparamdict[bayes_settings["lossparameter"]]
                data = pd.DataFrame.from_dict(globpardict)
                faultdata = pd.DataFrame.from_dict(faultpardict)
            data_loaded = True
        except Exception as e:
            print("error in loading data, initiating wait")
            logging.warning(f"Error occured: {e}")
            logging.info("Two runs might be trying to access data simultaneously. Waiting before trying again.")
            time.sleep(random.randint(0, 300)) 

    logging.info(f"Total simulations loaded: {len(data)+len(faultdata)}")
    logging.info(f"Number failed simulations: {len(faultfiles)}")


    # 2. Process data by replacing nans and infs with maximum finite likelihood or removing them  
    init_len = len(data)    
    if bayes_settings["infliketreatment"]=="replace":
        if bayes_settings["maxloss"]=="maxval":
            maxloss=data.loc[data["Y"]!=np.inf, "Y"].max()
            #print("maxloss set to : ",maxloss)
        elif bayes_settings["maxloss"]=="default":            
            if "l" in bayes_settings["lossparameter"]:
                maxloss=-np.log(sys.float_info.min)
            else:
                maxloss=sys.float_info.max**0.1
        else:
            maxloss=int(bayes_settings["maxloss"]) 
        data.replace([np.inf, -np.inf], maxloss, inplace=True)    
        faultreplace=faultdata.copy()
        faultreplace["Y"]=[maxloss]*len(faultdata)
        data = pd.concat([data, faultreplace], ignore_index=True, axis=0).reset_index(drop=True)
        data = data.dropna().reset_index(drop=True)
        post_len = len(data)
    elif bayes_settings["infliketreatment"]=="remove":
        maxloss=np.inf
        data.replace([np.inf, -np.inf], np.nan, inplace=True)
        faultdata = pd.concat([faultdata, data[data.isna().any(axis=1)].copy()], ignore_index=True, axis=0).drop(columns=["Y"]).reset_index(drop=True)
        ###### Improvement possibility: handle inf/nan/fails differently by assigning high neg. log-likelihood ######
        data = data.dropna().reset_index(drop=True)
        post_len = len(data)    
        logging.info(f"Number inf/nan simulations: {(init_len-post_len)}")
    logging.info(f"Final selected simulations: {post_len}")
    logging.info(f"Best neg. log-likelihood: { np.min(data['Y']) }")

     # 3. Filter data for preset parameters and drop preset parameter columns
        
    y_data = data[["Y"]].copy()
    X_data = data.copy().drop(columns=y_data.columns)
    
    
    if preset_parameters!=None:
        beforefilterlen=len(X_data)
        logging.info(f"Simulations before preset parameters filter: {beforefilterlen}")
        X_data, y_data = filter_points(X_data, y_data, preset_parameters)
        afterfilterlen=len(X_data)
        logging.info(f"Simulations before preset parameters filter: {afterfilterlen}")
        X_data = X_data.drop(columns=list(preset_parameters.keys()))
        faultdata = faultdata.drop(columns=list(preset_parameters.keys()))
    
    # 4. Fitting scalers to standardize data    
    Xscaler= StandardScaler()
    yscaler = StandardScaler()
    X_scaled = pd.DataFrame(Xscaler.fit_transform(X_data.copy()), columns=X_data.columns)
    y_scaled = pd.DataFrame(yscaler.fit_transform(y_data.copy()), columns=y_data.columns)
    
    return X_data, y_data, X_scaled, y_scaled, Xscaler, yscaler, faultdata, maxloss

# %%
# returns the n best X,y parameters in terms of log-likelihood
def top_results(X, y, n):
    #watch out that X, y have same indexing
    X_der = X.copy().reset_index(drop=True)
    y_der = y.copy().reset_index(drop=True)
    ycolumn = y_der.columns[0]
    top_indices = y_der.sort_values(by=ycolumn, ascending=True).head(n).index.tolist()
    top_y = y_der.loc[top_indices].reset_index(drop=True)
    top_X = X_der.loc[top_indices].reset_index(drop=True)
    return top_X, top_y

# returns the n closest X,y parameters to a point in terms of euclidian distance in parameter space
def closest_points(X, y, point, n):
    X_der = X.copy().reset_index(drop=True)
    y_der = y.copy().reset_index(drop=True)
    point_der = point.copy().iloc[0]
    distances = np.linalg.norm(X_der-point_der, axis=1)

    closest_indices = np.argsort(distances)[:n]
    closest_X = X_der.loc[closest_indices].reset_index(drop=True)
    closest_y = y_der.loc[closest_indices].reset_index(drop=True)
    return closest_X, closest_y

def filter_points(X, y, preset_parameters):
    X_filt = X.copy().reset_index(drop=True)
    y_filt = y.copy().reset_index(drop=True)
    for col_name,value in  preset_parameters.items():
        dropindx=X_filt.index[X_filt[col_name]!=value]
        X_filt.drop(dropindx,inplace=True)
        y_filt.drop(dropindx,inplace=True)
    filtered_X = X_filt.reset_index(drop=True)
    filtered_y = y_filt.reset_index(drop=True)
    return filtered_X, filtered_y

def get_distances(X_scaled,point):
    X_der = X_scaled.copy().reset_index(drop=True)
    point_der = point.copy().iloc[0]
    distances = np.linalg.norm(X_der-point_der, axis=1)
    return pd.DataFrame(distances,columns=["Distance"])
    
def get_farthest_point(X, y, sX, maxloss=False):
    bp, bl = top_results(X, y, 1)
    X_der = X.copy()
    y_der = y.copy()
    sX_der = sX.copy()
    if maxloss:
        y_filt_indices=y_der[y_der["Y"]<maxloss].index.tolist()
        X_der = X_der.copy().iloc[y_filt_indices].reset_index(drop=True)
        y_der = y_der.copy().iloc[y_filt_indices].reset_index(drop=True)
        sX_der = sX_der.copy().iloc[y_filt_indices].reset_index(drop=True)  
    bpf=pd.DataFrame(bp, columns=sX.columns).reindex_like(sX_der,method="nearest")  
    distances = np.linalg.norm(sX_der-bpf, axis=1)    
    far_indx = np.argsort(distances)[-1:]
    far_y = y_der.loc[far_indx].reset_index(drop=True)
    far_X = X_der.loc[far_indx].reset_index(drop=True)
    print("distance of farthest point ",distances[far_indx[0]])
    return far_X,far_y.values[0].item()

# %%
def value_text(value):
    """Format one parameter without changing its stored precision."""
    return np.format_float_positional(float(value), unique=True, trim="-")


def name_text(value):
    """Format one parameter with at most four significant digits."""
    return format(float(value), ".4g")


def point_text(point):
    """Format one optimizer point for compact monitoring output."""
    return " ".join(f"{name}={name_text(point[name])}"
                    for name in ("D0", "deltaA", "deltaB", "deltaZ"))


def make_stem(point, date):
    """Build the required parameter-bearing stem."""
    return (f"{date}_BayesOpt_D{name_text(point['D0'])}"
            f"_dA{name_text(point['deltaA'])}"
            f"_dB{name_text(point['deltaB'])}"
            f"_dZ{name_text(point['deltaZ'])}")


def submit_task(point, cfg, seen, host, dry=False):
    names = list(cfg["seed"])
    if set(point) != set(names):
        raise ValueError("Candidate names must match the four-parameter seed")
    point = {name: float(point[name]) for name in names}
    bounds = cfg.get("bounds")
    for name, value in point.items():
        if not np.isfinite(value):
            raise ValueError(f"Non-finite candidate: {name}={value}")
        if bounds is not None:
            low, high = bounds[name]
            if not low <= value <= high:
                raise ValueError(f"Out-of-range candidate: {name}={value}")
    if point["D0"] <= 0 or point["deltaA"] < 0 or point["deltaB"] <= 0 or point["deltaZ"] < 0:
        raise ValueError("D0/deltaB must be positive and deltaA/deltaZ non-negative")
    if host not in cfg["hosts"]:
        raise KeyError(f"Unknown compute host: {host}")
    date = datetime.now(TOKYO).strftime("%Y-%m-%d")
    key = tuple(point[name] for name in names)
    stem_key = ("stem", date, *(name_text(point[name]) for name in names))
    if key in seen or stem_key in seen:
        raise ValueError("Duplicate candidate across the formal search")

    base = Path(cfg["base"]).expanduser().resolve()
    source = Path(cfg["source"]).expanduser().resolve()
    coeff = Path(cfg["coeff"]).expanduser().resolve()
    if not base.is_file() or not source.is_file() or not coeff.is_file():
        raise FileNotFoundError("Base XML, source abundance, or coefficient table is missing")
    stem = make_stem(point, date)
    out = ROOT / "outputs/bayes"
    out.mkdir(parents=True, exist_ok=True)
    processed = ROOT / "data/processed"
    processed.mkdir(parents=True, exist_ok=True)
    xml_path = processed / f"{stem}.xml"
    param_path = processed / f"{stem}.source.param"
    diff_path = out / f"{stem}.diff"
    rec_path = out / f"{stem}-{host}.json"
    updates = {name: value_text(value) for name, value in point.items()}
    updates.update({name: value_text(value) for name, value in cfg["fixed"].items()})
    if not xml_path.exists():
        modify_xml(base, updates, xml_path, diff_path)
    if not param_path.exists():
        shutil.copy2(source, param_path)
    if file_hash(param_path) != file_hash(source):
        raise ValueError("Candidate source abundance differs from the fixed source")

    base_doc = load_xml(base)
    run_doc = load_xml(xml_path)
    fixed = {}
    actual = {}
    for name in PARAM_MAP:
        value = get_param(run_doc, name)
        actual[name] = value
        if name in point:
            if float(value) != point[name]:
                raise ValueError(f"Candidate was quantized: {name}")
        elif name in cfg["fixed"]:
            expected = float(cfg["fixed"][name])
            fixed[name] = value
            if float(value) != expected:
                raise ValueError(f"Fixed search parameter changed: {name}")
        else:
            fixed[name] = get_param(base_doc, name)
            if value != fixed[name]:
                raise ValueError(f"Fixed XML parameter changed: {name}")
    grid = find_one(run_doc, "//Grid")
    if grid.get("type") != "3D" or float(actual["VariableDelta"]) != 1:
        raise ValueError("Expected 3D VariableDelta model")
    if int(actual["Zmin"]) != 1 or int(actual["Zmax"]) != 8:
        raise ValueError("Bayesian optimization candidates must use Zmin=1 and Zmax=8")
    if find_one(run_doc, "//Galaxy/Diffusion").get("type") == "Anisotropic":
        raise ValueError("3D VariableDelta requires isotropic diffusion")
    values = [float(actual[name]) for name in
              ("DiffusionThreshold", "DiffusionThresholdZ", "deltaA", "deltaB", "deltaZ")]
    if not all(np.isfinite(value) for value in values):
        raise ValueError("Non-finite 3D VariableDelta input")
    if min(values[0], values[1], values[2], values[4]) < 0 or values[3] <= 0:
        raise ValueError("Invalid 3D VariableDelta input")
    for name in (*point, *cfg["fixed"]):
        set_param(run_doc, name, get_param(base_doc, name))
    if render_xml(run_doc) != render_xml(base_doc):
        raise ValueError("A non-search XML setting changed")

    output = find_one(load_xml(xml_path), "//Output")
    expected = [dict(native=stem + ".txt", archive=stem + ".txt", kind="ascii")]
    if output.find("fullstore") is not None:
        expected.append(dict(native=stem + ".fits.gz", archive=stem + ".fits.gz", kind="spatial"))
    if output.find("partialstore") is not None:
        expected.append(dict(native=stem + "_spectrum.fits.gz",
                             archive=stem + "-spectrum.fits.gz", kind="solar"))
    target = cfg["hosts"][host]
    ssh = target["ssh"]
    program = Path(target["program"])
    state_key = stem + "-" + host
    rec = {
        "id": stem,
        "stem": stem,
        "mode": "bayes",
        "date": date,
        "host": host,
        "ssh": ssh,
        "threads": int(target["threads"]),
        "stateKey": state_key,
        "status": "checked",
        "candidate": point,
        "order": names,
        "bounds": bounds,
        "units": {"D0": "1e28 cm2/s", "deltaA": "kpc^-1",
                  "deltaB": "1", "deltaZ": "kpc^-1"},
        "paths": {name: PARAM_MAP[name] for name in names},
        "actual": actual,
        "fixed": fixed,
        "params": {"DimZ": int(actual["DimZ"]), "Zmax": int(actual["Zmax"])},
        "baseline": str(base),
        "baselineHash": file_hash(base),
        "xml": str(xml_path),
        "xmlHash": file_hash(xml_path),
        "diff": str(diff_path),
        "sourceParam": str(param_path),
        "sourceHash": file_hash(param_path),
        "coefficient": str(coeff),
        "coefficientHash": file_hash(coeff),
        "sourceMode": "fixed per-run copy",
        "program": str(program),
        "runXml": str(xml_path),
        "inputs": [
            {"local": str(xml_path), "remote": str(xml_path), "sha256": file_hash(xml_path)},
            {"local": str(param_path), "remote": str(param_path), "sha256": file_hash(param_path)},
        ],
        "expected": expected,
        "source": str(program / "output" / f"{stem}.txt"),
        "record": str(rec_path),
        "components": None,
        "total": None,
    }
    if dry:
        rec_path.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
        seen.add(key)
        seen.add(stem_key)
        return rec

    log = remote.new_log()
    runtime = remote.new_log()
    rec.update(log=str(log), localLog=str(log), remoteLog=str(runtime),
               status="preparing", token=file_hash(log) + datetime.now().astimezone().isoformat())
    reserved = False
    try:
        remote.rpc("reserve", state_key, log, host=ssh, spec=rec)
        reserved = True
        for item in rec["inputs"]:
            companion.upload(item["local"], item["remote"], log, host=ssh)
        state = remote.rpc("launch", state_key, log, host=ssh, token=rec["token"])
        rec.update(state)
        view = shlex.join([*companion.SSH, ssh,
                           shlex.join(["tail", "-n", "60", "-F", "--", rec["remoteLog"]])])
        display = "#{session_name}:#{window_index}.#{pane_index}"
        session = host + "_log"
        target = f"={session}:log.0"
        try:
            try:
                viewer = companion.run_command(
                    ["tmux", "new-session", "-d", "-s", session, "-n", "log",
                     "-P", "-F", display, view], log, capture=True)
            except RuntimeError:
                companion.run_command(
                    ["tmux", "respawn-pane", "-k", "-t", target, view],
                    log, capture=True)
                companion.run_command(
                    ["tmux", "clear-history", "-t", target],
                    log, capture=True)
                viewer = companion.run_command(
                    ["tmux", "display-message", "-p", "-t", target, display],
                    log, capture=True)
            rec["monitor"] = viewer.stdout.strip()
            print(f"Monitor: tmux attach -t {session} ({rec['monitor']})", flush=True)
        except (OSError, RuntimeError) as err:
            rec["monitor"] = None
            print(f"Warning: tmux monitor unavailable: {err}", flush=True)
    except BaseException:
        if reserved:
            try:
                remote.rpc("abort", state_key, log, host=ssh, token=rec["token"])
            except Exception:
                pass
        raise
    finally:
        rec_path.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    seen.add(key)
    seen.add(stem_key)
    return rec


def apply_coeff(source, target, coeff):
    """Convert one Z=8 ASCII spectrum into its Z=14 prediction."""
    source = Path(source)
    target = Path(target)
    coeff = Path(coeff)
    with source.open(encoding="utf-8") as handle:
        header = handle.readline().split()
    if header[:2] != ["Energy", "[GeV]"]:
        raise ValueError("Invalid Z=8 ASCII header")
    names = header[2:]
    model = np.loadtxt(source, skiprows=1)
    with coeff.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        rows = list(reader)
    if fields != ["Energy_GeV", *names]:
        raise ValueError("Coefficient columns differ from the DRAGON2 spectrum")
    factors = np.array([[float(row[name]) for name in fields] for row in rows])
    if model.shape != factors.shape or not np.allclose(model[:, 0], factors[:, 0], rtol=1e-12, atol=0):
        raise ValueError("Coefficient energy grid differs from the DRAGON2 spectrum")
    if not np.all(np.isfinite(factors)) or np.any(factors[:, 1:] <= 0):
        raise ValueError("Coefficient table contains invalid values")
    result = model.copy()
    result[:, 1:] *= factors[:, 1:]
    target.parent.mkdir(parents=True, exist_ok=True)
    np.savetxt(target, result, fmt="%.12e", comments="",
               header="Energy [GeV] " + " ".join(names))
    return target


def collect_task(rec, once=False, quiet=False):
    """Poll or wait for one remote task and retrieve verified products."""
    log = Path(rec["log"])
    path = Path(rec["record"])
    while rec["status"] in {"launching", "running", "finalizing"}:
        if not quiet:
            print(f"{rec['host']} {rec['id']}: {rec['status']}", flush=True)
        if not once:
            time.sleep(20)
        state = remote.rpc("status", rec["stateKey"], log, host=rec["ssh"])
        rec.update(state)
        path.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
        if once and rec["status"] in {"launching", "running", "finalizing"}:
            return rec
    runtime = ROOT / "logs" / Path(rec["remoteLog"]).name
    companion.download(rec["remoteLog"], runtime, log, host=rec["ssh"])
    rec["runtimeLog"] = str(runtime)
    duration = None
    with runtime.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            text = line.rstrip("\r\n")
            if re.fullmatch(r"Solution found in .+ s\.", text):
                duration = text
    rec["duration"] = duration
    if duration:
        print(f"{rec['host']}: {duration}", flush=True)
    if rec["status"] != "succeeded" or rec.get("exitcode") != 0:
        rec["status"] = "run_failed"
        path.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
        return rec
    archive = ROOT / "data/dragon_output"
    archive.mkdir(parents=True, exist_ok=True)
    rec["artifacts"] = []
    for item in rec["outputs"]:
        if item["kind"] == "ascii":
            suffix = ".txt"
        elif item["kind"] == "spatial":
            suffix = ".fits.gz"
        else:
            suffix = "-spectrum.fits.gz"
        target = archive / f"{rec['id']}-{rec['host']}{suffix}"
        staged = target.with_name(target.stem + ".part" + target.suffix)
        staged.unlink(missing_ok=True)
        try:
            companion.download(item["remote"], staged, log, host=rec["ssh"])
            if staged.stat().st_size != item["size"] or file_hash(staged) != item["sha256"]:
                raise ValueError(f"Returned output hash/size mismatch: {target}")
            code = (
                "import sys; from scripts.run_companion import validate_data, validate_fits; "
                "(validate_data if sys.argv[1] == 'ascii' else validate_fits)(sys.argv[2])"
            )
            companion.run_command(
                ["env", "-u", "PYTHONPATH", sys.executable, "-c", code,
                 item["kind"], staged], log, cwd=ROOT)
            staged.replace(target)
        finally:
            staged.unlink(missing_ok=True)
        rec["artifacts"].append({**item, "local": str(target)})
        print(f"Retrieved: {target}", flush=True)
    raw = next(item["local"] for item in rec["artifacts"] if item["kind"] == "ascii")
    pred = archive / f"{rec['id']}-{rec['host']}-z14.txt"
    apply_coeff(raw, pred, rec["coefficient"])
    print(f"Predicted Z=14 spectrum: {pred}", flush=True)
    rec.update(status="simulated", spectrumZ8=raw, spectrum=str(pred),
               spectrumHash=file_hash(pred))
    path.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    return rec

# %%
def determine_bounds(X, Xscaler, volume_factor):
    # Determine boundary box for Bayesian optimization (take outer edges of all closest points)
    low_bounds = []
    up_bounds = []
    for column in X.columns:
        low_bounds.append(round(max(0.0001, np.min(X[column])), 4))
        up_bounds.append(round(max(0.0001, np.max(X[column])), 4))
    boundaries = list(zip(low_bounds, up_bounds))
    logging.info(f"Determined boundaries: {boundaries}")
    
    # Double size of boundary box search space
    low_bounds_scaled = []
    up_bounds_scaled = []
    scale_factor = volume_factor**(1/len(X.columns))
    for i, column in enumerate(X.columns):
        dimension_length=up_bounds[i]-low_bounds[i]
        dimension_length_correction = (dimension_length*scale_factor-dimension_length)/2
        low_bounds_scaled.append(round(max(0.0001, low_bounds[i]-dimension_length_correction) , 4))
        up_bounds_scaled.append(round(max(0.0001, up_bounds[i]+dimension_length_correction) , 4))
    boundaries_corrected = list(zip(low_bounds_scaled, up_bounds_scaled))
    boundaries_corrected_scaled = list(zip(Xscaler.transform(pd.DataFrame([low_bounds_scaled], columns=X.columns))[0], Xscaler.transform(pd.DataFrame([up_bounds_scaled], columns=X.columns))[0]))
    logging.info(f"Determined corrected boundaries: {boundaries_corrected}")    
    
    return (boundaries_corrected, boundaries_corrected_scaled)

# %%
def load_previous_data(folder):
    highest_file, _ = highest_fileandID(folder)
    if highest_file==None: 
        raise FileNotFoundError("There are no saved in the given folder files!")
    else:
        with open(os.path.join(folder, highest_file), "rb") as file:
            save_data = pickle.load(file)
            points = save_data["points"]
            bounds = save_data["bounds"]
            losses = save_data["losses"]
    return points, losses, bounds

def save_current_data(X, y, points, losses, bounds, folder):
    with open(os.path.join(folder, "data.pkl"), "wb") as file:
        save_data = {"points": points, "bounds": bounds, "losses": losses, "init_X": X, "init_y": y}
        pickle.dump(save_data, file) 
    logging.info("\n")
    logging.info("-"*20+"Saved new data"+"-"*20) 
    
    
def highest_fileandID(folder):
    detected_files = os.listdir(folder)
    pattern = re.compile(r"_\d{4}-\d{2}-\d{2}_(\d+)\.pkl")
    mode_files = [f for f in detected_files if pattern.match(f)]
    
    highest_id = -1
    highest_file = None
    for file in mode_files:
        match = pattern.match(file)
        if match:
            file_id = int(match.group(1))
            if file_id > highest_id:
                highest_file = file
                highest_id = file_id
                    
    return [highest_file, highest_id]

# %%
def load_config():
    try: script_dir = os.path.dirname(os.path.realpath(__file__))
    except: script_dir = f"/home/{getpass.getuser()}/CALETana/prop/BayesianOptimization"
    with open(os.path.join(script_dir, "config.yaml"), "r") as file:
        config = yaml.safe_load(file)
    bayes_settings = config["bayes_settings"]
    preset_parameters = config["preset_parameters"]
    comp_settings = config["comp_settings"]
    paths = config["paths"]
    return bayes_settings, preset_parameters, comp_settings, paths

# %%
def generate_saveFolderName(path, load_previous, settings):
    folder_prefix = get_folderPrefix(settings)
    date = datetime.now().strftime("%Y-%m-%d")
    highest_folder, id = get_folderID(folder_prefix, path)
    
    if load_previous:
        if highest_folder == None: raise FileNotFoundError("Loading previous results was requested, but none were found") 
        folder_name = highest_folder
        save_path = os.path.join(path, folder_name)
    else: 
        folder_name = f"{folder_prefix}_{date}_{id+1}"
        save_path = os.path.join(path, folder_name)
        os.makedirs(save_path, exist_ok=True)
        with open(os.path.join(save_path, "output.log"),"w") as file: pass
        
    return save_path

def get_folderPrefix(s):
    prefix = f"{s['lossparameter']}_Calls{s['n_calls']}_ClosestPoints{s['n_closest_points']}_VolumeFactor{s['volume_factor']}"
    return prefix

def get_folderID(prefix, path):
    # obtains foldername with highest ID that matches current settings in path
    detected_folders = os.listdir(path)
    pattern = re.compile(prefix+r"_\d{4}-\d{2}-\d{2}_(\d+)")
    prefix_folders = [f for f in detected_folders if pattern.match(f)]
    
    highest_id = -1
    highest_folder = None
    for file in prefix_folders:
        match = pattern.match(file)
        if match:
            file_id = int(match.group(1))
            if file_id > highest_id:
                highest_folder = file
                highest_id = file_id     
    return [highest_folder, highest_id]


# %%
def checkSimulationProgress(X_data, y_data, X_fault, point_list, loss_list, maxloss):
    logging.info("\n")
    logging.info("-"*20+"Checking for finished simulations"+"-"*20)
    simulation_finished, simulation_infnan = False, False
    match = X_data[(X_data==point_list[-1].iloc[0]).all(axis=1)]
    #Check whether last point is in new data and save its new loss
    if not match.empty: 
        logging.info("A simulation has finished successfully")
        if(len(point_list)!=len(loss_list)): loss_list.append(y_data.iloc[match.index[0],0])
        logging.info(f"Point:\n{point_list[-1].iloc[0]}")
        logging.info(f"Loss: {loss_list[-1]}")
        simulation_finished = True
    if ((X_fault == point_list[-1].iloc[0]).all(axis=1)).any():  # Check whether last point simulation has failed
        logging.error(f"\033[91m Problem occured \033[0m: Simulation of point failed or is inf\n{point_list[-1]}")
        if(len(point_list)!=len(loss_list)): loss_list.append(maxloss)
        logging.info(f"Point:\n{point_list[-1].iloc[0]}")
        logging.info(f"Loss: {loss_list[-1]}")
        simulation_finished, simulation_infnan = True, True      # for failed simulations: take last working point and only take half of the last not working step size (momentum)         
    return simulation_finished, simulation_infnan

# %%
def obj_func(point, cfg, seen, rec=None):
    if rec is None:
        raise ValueError("A retrieved remote record is required for scoring")
    if rec["candidate"] != point:
        raise ValueError("Remote record does not match the candidate")
    if rec["status"] not in {"simulated", "scored"}:
        return rec
    try:
        spec = Path(rec["spectrum"])
        with spec.open(encoding="utf-8") as handle:
            header = handle.readline().split()
        if header[:2] != ["Energy", "[GeV]"]:
            raise ValueError("Invalid DRAGON2 ASCII header")
        columns = header[2:]
        required = ("NUC_5010", "NUC_5011", "NUC_6012", "NUC_6013", "NUC_6014")
        if any(columns.count(name) != 1 for name in required):
            raise ValueError("Required isotope column missing or duplicated")
        data = np.loadtxt(spec, skiprows=1)
        if data.ndim != 2 or data.shape[0] < 2 or data.shape[1] != len(columns) + 1:
            raise ValueError("Incomplete DRAGON2 ASCII table")
        if not np.all(np.isfinite(data)) or np.any(data[:, 0] <= 0) or np.any(np.diff(data[:, 0]) <= 0):
            raise ValueError("Invalid model energy axis or values")
        energy = data[:, 0]
        base = str(ROOT / "data/experiment_data/expdata") + "/"
        observed = readamsBCratio(base)
        points = [(float(axis), float(vals[0]), float(vals[1]), vals[2])
                  for axis, vals in observed.items() if vals[2][0] >= 10]
        if len(points) != 40:
            raise ValueError("Unexpected observation count for BC")
        axis = np.array([item[0] for item in points])
        obs = np.array([item[1] for item in points])
        error = np.array([item[2] for item in points])
        boron = np.zeros(len(points))
        carbon = np.zeros(len(points))
        species = (("NUC_5010", 5, 10, 10 * 0.931494),
                   ("NUC_5011", 5, 11, 11 * 0.931494),
                   ("NUC_6012", 6, 12, 12 * 0.931494),
                   ("NUC_6013", 6, 13, 13 * 0.931494),
                   ("NUC_6014", 6, 14, 14 * 0.931494))
        phi = cfg["phi"]["BC"]
        for name, charge, massnum, mass in species:
            flux = data[:, columns.index(name) + 1] / 10000
            _, toa = SM_output(energy, flux, PhiP=phi, Mass=mass / massnum,
                               output_energies=axis, charge=charge, massnum=massnum)
            if name.startswith("NUC_5"):
                boron += toa
            else:
                carbon += toa
        if np.any(carbon <= 0):
            raise ValueError("Nonpositive carbon denominator")
        model = boron / carbon
        result = chisquare(obs, model, error, return_points=True)
        rows = []
        for i, item in enumerate(points):
            rows.append({
                "run": rec["id"], "observable": "BC", "axis": item[0],
                "lower": item[3][0], "upper": item[3][1],
                "observed": obs[i], "model": model[i], "error": result["sigma"][i],
                "residual": result["residual"][i],
                "contribution": result["contribution"][i], "phi": phi,
            })
        out = ROOT / "outputs/csv" / (rec["id"] + "-" + rec["host"] + "-residual.csv")
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        figures = {}
        fit = None
        for label, script in (("BCfitting", "BCfitting.py"),
                              ("pHefitting27", "pHefitting27.py")):
            target = ROOT / "outputs/figures" / f"{rec['id']}-{rec['host']}-{label}.png"
            target.parent.mkdir(parents=True, exist_ok=True)
            command = ["env", "-u", "PYTHONPATH", sys.executable,
                       ROOT / "dragon_utils/plotting" / script,
                       rec["spectrum"], "--output", target]
            if label == "pHefitting27":
                command.extend(["--fit", "--fit-min", str(cfg["fitMin"])])
                done = companion.run_command(command, rec["log"], capture=True)
                lines = [line.removeprefix("FIT_RESULT=") for line in done.stdout.splitlines()
                         if line.startswith("FIT_RESULT=")]
                if len(lines) != 1:
                    raise ValueError("p/He fitter did not return one FIT_RESULT record")
                fit = json.loads(lines[0])
            else:
                companion.run_command(command, rec["log"])
            if not target.is_file() or not target.stat().st_size:
                raise ValueError(f"Plot was not created: {target}")
            figures[label] = {"path": str(target), "sha256": file_hash(target)}
        if fit is None or set(fit) != {"p", "He", "fitMin"}:
            raise ValueError("Incomplete p/He fit result")
        if float(fit["fitMin"]) != float(cfg["fitMin"]):
            raise ValueError("p/He fit threshold differs from the search configuration")
        parts = {"p": float(fit["p"]["chi2"]),
                 "He": float(fit["He"]["chi2"]),
                 "BC": float(result["chi2"])}
        raw = {"p": float(fit["p"]["fitraw"]),
               "He": float(fit["He"]["fitraw"])}
        norm = {"p": float(fit["p"]["constant"]),
                "He": float(fit["He"]["constant"])}
        total = float(sum(parts.values()))
        values = [*parts.values(), *raw.values(), *norm.values(), total]
        if (not all(np.isfinite(value) for value in values) or
                min([*parts.values(), *raw.values(), total]) < 0 or
                min(norm.values()) <= 0):
            raise ValueError("Invalid fitted objective")
        objective = f"pHe_norm{value_text(cfg['fitMin'])}_BC_v1"
        rec.update({"status": "scored", "components": parts, "rawComponents": raw,
                    "normalization": norm, "fitResult": fit, "fitMin": float(cfg["fitMin"]),
                    "objective": objective, "total": total,
                    "points": str(out), "pointsHash": file_hash(out),
                    "count": {"p": int(fit["p"]["fitused"]),
                              "He": int(fit["He"]["fitused"]), "BC": 40}})
        rec["plots"] = figures
        rec.pop("error", None)
    except Exception as exc:
        rec.update({"status": "evaluation_failed", "error": str(exc), "total": None})
    Path(rec["record"]).write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    return rec


def save_csv(records, batch, result, proposal=None, date=None):
    """Upsert scored records in one dated optimization table."""
    if not records:
        raise ValueError("No optimization records to save")
    date = date or records[0]["date"]
    path = ROOT / "outputs/csv" / f"{date}_BayesOpt.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "date", "batch", "host", "stem", "status", "D0", "deltaA", "deltaB", "deltaZ",
        "raw_p", "raw_He", "norm_p", "norm_He", "fit_min",
        "chi2_p", "chi2_He", "chi2_BC", "chi2_total", "optimizer_loss",
        "optimizer_result", "next_proposal", "z8_spectrum", "z14_spectrum",
        "BCfitting", "pHefitting27", "duration", "record",
    ]
    prior = []
    if path.exists():
        with path.open(newline="", encoding="utf-8") as handle:
            prior = list(csv.DictReader(handle))
    prior = [{name: row.get(name, "") for name in fields} for row in prior]
    keys = {(date, str(batch), rec["host"], rec["id"]) for rec in records}
    prior = [row for row in prior if
             (row["date"], row["batch"], row["host"], row["stem"]) not in keys]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(prior)
        for rec in records:
            parts = rec.get("components") or {}
            raw = rec.get("rawComponents") or {}
            norm = rec.get("normalization") or {}
            plots = rec.get("plots") or {}
            point = rec["candidate"]
            writer.writerow({
                "date": date, "batch": batch, "host": rec["host"],
                "stem": rec["id"], "status": rec["status"],
                "D0": point["D0"], "deltaA": point["deltaA"],
                "deltaB": point["deltaB"], "deltaZ": point["deltaZ"],
                "raw_p": raw.get("p"), "raw_He": raw.get("He"),
                "norm_p": norm.get("p"), "norm_He": norm.get("He"),
                "fit_min": rec.get("fitMin"),
                "chi2_p": parts.get("p"), "chi2_He": parts.get("He"),
                "chi2_BC": parts.get("BC"), "chi2_total": rec.get("total"),
                "optimizer_loss": rec.get("total"), "optimizer_result": result,
                "next_proposal": json.dumps(proposal, separators=(",", ":")) if proposal else "",
                "z8_spectrum": rec.get("spectrumZ8", ""),
                "z14_spectrum": rec.get("spectrum", ""),
                "BCfitting": plots.get("BCfitting", {}).get("path", ""),
                "pHefitting27": plots.get("pHefitting27", {}).get("path", ""),
                "duration": rec.get("duration", ""), "record": rec["record"],
            })
    return path

# %%
def get_pointsInBounds(bounds, X, y):
    X_der = X.copy().reset_index(drop=True)
    y_der = y.copy().reset_index(drop=True)
    
    for col, (low, high) in zip(X_der.columns, bounds):
        X_der = X_der[(X_der[col]>=low) & (X_der[col]<=high)]
        
    by = y_der.loc[X_der.index].reset_index(drop=True)
    bX = X_der.reset_index(drop=True)
    
    return (bX, by)


def load_history(cfg, seen):
    """Re-score unique completed formal candidates without rerunning DRAGON2."""
    accepted = {"batch_told", "history_refit", "async_told"}
    records = []
    tables = sorted((ROOT / "outputs/csv").glob("*_BayesOpt.csv"))
    for table in tables:
        with table.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        for row in rows:
            if row.get("optimizer_result") not in accepted:
                continue
            path = Path(row.get("record", ""))
            if not path.is_file():
                raise FileNotFoundError(f"Formal optimization record is missing: {path}")
            rec = json.loads(path.read_text(encoding="utf-8"))
            point = rec.get("candidate")
            if not isinstance(point, dict) or set(point) != set(cfg["seed"]):
                raise ValueError(f"Invalid formal candidate record: {path}")
            key = tuple(float(point[name]) for name in cfg["seed"])
            if key in seen:
                continue
            for name, value in zip(cfg["seed"], key):
                low, high = cfg["bounds"][name]
                if not float(low) <= value <= float(high):
                    raise ValueError(f"Historical candidate is outside current bounds: {path}")
            spectrum = Path(rec.get("spectrum", ""))
            if not spectrum.is_file() or file_hash(spectrum) != rec.get("spectrumHash"):
                raise ValueError(f"Historical Z=14 spectrum is missing or changed: {path}")
            rec["status"] = "simulated"
            rec = obj_func(point, cfg, seen, rec=rec)
            if rec["status"] != "scored":
                raise RuntimeError(f"Historical candidate re-score failed: {path}: {rec.get('error')}")
            seen.add(key)
            records.append(rec)
    return records


def ask_point(opt, cfg, seen, active, issued):
    """Ask one unique point while treating active candidates as pending."""
    names = list(cfg["seed"])
    pending = [[rec["candidate"][name] for name in names]
               for rec in active.values()]
    for retry in range(1000):
        shadow = opt.copy(random_state=int(cfg["seedValue"]) + issued + retry)
        if pending:
            lie = min(opt.yi) if opt.yi else 0.0
            shadow.tell(pending, [lie] * len(pending))
        point = dict(zip(names, shadow.ask()))
        key = tuple(float(point[name]) for name in names)
        date = datetime.now(TOKYO).strftime("%Y-%m-%d")
        stem_key = ("stem", date, *(name_text(point[name]) for name in names))
        if key not in seen and stem_key not in seen:
            return point, issued + retry + 1
    raise RuntimeError("Optimizer could not produce a unique candidate")


# %%
def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--test", action="store_true")
    mode.add_argument("--resume-test", dest="resume", action="store_true")
    mode.add_argument("--calls", type=int)
    args = parser.parse_args()
    with (Path(__file__).parent / "config.yaml").open(encoding="utf-8") as handle:
        cfg = yaml.safe_load(handle)["search"]
    names = ["D0", "deltaA", "deltaB", "deltaZ"]
    if list(cfg["seed"]) != names:
        raise ValueError("Seed order must be D0, deltaA, deltaB, deltaZ")
    if list(cfg["hosts"]) != ["companion", "yellowgiant"]:
        raise ValueError("The host order must be companion, yellowgiant")
    if not np.isfinite(cfg.get("fitMin", np.nan)) or float(cfg["fitMin"]) < 0:
        raise ValueError("fitMin must be finite and nonnegative")
    cfg["date"] = datetime.now(TOKYO).strftime("%Y-%m-%d")
    base = str(ROOT / "data/experiment_data/expdata") + "/"
    observed = {
        "p": readamsproflxvals(base, convtoE=False),
        "He": readamsHEflxvals(base, convtoE=False),
        "BC": readamsBCratio(base),
    }
    counts = {"p": 36, "He": 37, "BC": 40}
    limits = {"p": 30, "He": 30, "BC": 10}
    for mode, points in observed.items():
        vals = [item for item in points.values() if item[2][0] >= limits[mode]]
        if len(vals) != counts[mode]:
            raise ValueError(f"Observation preflight failed for {mode}")
        obs = np.array([item[0] for item in vals])
        err = np.array([item[1] for item in vals])
        if chisquare(obs, obs, err) != 0:
            raise ValueError("Chi-square preflight failed")
    with Path(cfg["coeff"]).open(newline="", encoding="utf-8") as handle:
        fields = csv.DictReader(handle).fieldnames or []
    required = {"Energy_GeV", "Pri_p", "Sec_p", "NUC_2003", "NUC_2004",
                "NUC_5010", "NUC_5011", "NUC_6012", "NUC_6013", "NUC_6014"}
    if not required <= set(fields):
        raise ValueError("Z=14/Z=8 coefficient table lacks required columns")
    seen = set()
    if args.check:
        records = [submit_task(cfg["seed"], cfg, set(), host, dry=True)
                   for host in cfg["hosts"]]
        print(json.dumps({"status": "passed", "records": [rec["record"] for rec in records],
                          "observations": counts}, indent=2), flush=True)
        return
    if args.test or args.resume:
        if args.resume:
            stem = make_stem(cfg["seed"], cfg["date"])
            records = []
            for host in cfg["hosts"]:
                path = ROOT / "outputs/bayes" / f"{stem}-{host}.json"
                rec = json.loads(path.read_text(encoding="utf-8"))
                if (rec.get("id") != stem or rec.get("host") != host or
                        rec.get("candidate") != cfg["seed"]):
                    raise ValueError(f"Resume record differs from the test seed: {path}")
                local_status = rec.get("status")
                saved = {name: rec[name] for name in
                         ("artifacts", "spectrumZ8", "spectrum", "spectrumHash",
                          "runtimeLog", "duration", "components", "total", "points",
                          "pointsHash", "count", "plots") if name in rec}
                artifacts = rec.get("artifacts", [])
                ready = (local_status in {"simulated", "scored"} and
                         len(artifacts) == len(rec.get("outputs", [])))
                for item in artifacts:
                    target = Path(item.get("local", ""))
                    ready = (ready and target.is_file() and target.stat().st_size == item["size"]
                             and file_hash(target) == item["sha256"])
                target = Path(rec.get("spectrum", ""))
                ready = (ready and target.is_file() and
                         file_hash(target) == rec.get("spectrumHash"))
                parts = rec.get("components")
                scored = (ready and local_status == "scored" and isinstance(parts, dict) and
                          set(parts) == {"p", "He", "BC"} and
                          isinstance(rec.get("total"), (int, float)) and
                          np.isfinite(rec["total"]) and
                          set(rec.get("plots", {})) == {"BCfitting", "pHefitting27"})
                if scored:
                    target = Path(rec.get("points", ""))
                    scored = (target.is_file() and
                              file_hash(target) == rec.get("pointsHash"))
                    for item in rec.get("plots", {}).values():
                        target = Path(item.get("path", ""))
                        scored = (scored and target.is_file() and
                                  file_hash(target) == item.get("sha256"))
                state = remote.rpc("status", rec["stateKey"], Path(rec["log"]),
                                   host=rec["ssh"])
                if state.get("token") != rec.get("token"):
                    raise ValueError(f"Remote task token differs from the local record: {host}")
                runok = state.get("status") == "succeeded" and state.get("exitcode") == 0
                ready = ready and runok
                scored = scored and runok
                rec.update(state)
                rec.update(saved)
                if ready:
                    rec["status"] = "scored" if scored else "simulated"
                path.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
                records.append(rec)
        else:
            records = [submit_task(cfg["seed"], cfg, set(), host)
                       for host in cfg["hosts"]]
        records = [rec if rec["status"] in {"simulated", "scored"} else collect_task(rec)
                   for rec in records]
        records = [obj_func(cfg["seed"], cfg, seen, rec=rec) for rec in records]
        if all(rec["status"] == "scored" for rec in records):
            left = np.loadtxt(records[0]["spectrum"], skiprows=1)
            right = np.loadtxt(records[1]["spectrum"], skiprows=1)
            scale = np.maximum(np.maximum(np.abs(left), np.abs(right)), np.finfo(float).tiny)
            parity = float(np.max(np.abs(left - right) / scale))
            result = f"test_stopped; z14_max_relative_difference={parity:.12g}"
        else:
            result = "test_failed; no_next_proposal"
        table = save_csv(records, 1, result)
        print(f"Test table: {table}", flush=True)
        for rec in records:
            print(f"{rec['host']}: {rec['status']} chi2={rec.get('total')}", flush=True)
        if any(rec["status"] != "scored" for rec in records):
            raise RuntimeError("Synchronous two-host test failed; no next proposal was made")
        print("Two-host test completed; optimizer stopped before the next proposal.", flush=True)
        return

    bounds = cfg.get("bounds")
    if not isinstance(bounds, dict) or list(bounds) != names:
        raise ValueError("Set linear bounds for D0, deltaA, deltaB, deltaZ before a full search")
    if args.calls is None or args.calls < 1:
        raise ValueError("--calls must be a positive global candidate count")
    for name, pair in bounds.items():
        if len(pair) != 2 or not float(pair[0]) < float(pair[1]):
            raise ValueError(f"Invalid linear bounds: {name}")
    opt = Optimizer([Real(*bounds[name], prior="uniform", name=name) for name in names],
                    base_estimator="GP", n_initial_points=int(cfg["nInitial"]),
                    random_state=cfg["seedValue"], avoid_duplicates=True)
    history = load_history(cfg, seen)
    if len(history) > args.calls:
        raise ValueError(f"--calls={args.calls} is below {len(history)} completed formal candidates")
    for index, rec in enumerate(history, 1):
        point = rec["candidate"]
        opt.tell([point[name] for name in names], rec["total"])
        save_csv([rec], f"history-{index:03d}", "history_refit", date=cfg["date"])
    if history:
        best = min(history, key=lambda item: item["total"])
        print(f"Best: {point_text(best['candidate'])} chi2={name_text(best['total'])}",
              flush=True)
    if len(history) == args.calls:
        print(f"Global target already reached: {args.calls} candidates", flush=True)
        return

    active = {}
    issued = 0
    completed = len(history)
    event = 0
    for host in cfg["hosts"]:
        if completed + len(active) >= args.calls:
            break
        point, issued = ask_point(opt, cfg, seen, active, issued)
        active[host] = submit_task(point, cfg, seen, host)
        print(f"Assigned {host}: {point_text(point)}", flush=True)

    while active:
        for host in cfg["hosts"]:
            rec = active.get(host)
            if rec is None:
                print(f"{host}: idle", flush=True)
            else:
                print(f"{host} {rec['id']}: {rec['status']}", flush=True)
        if opt.yi:
            best = int(np.argmin(opt.yi))
            point = dict(zip(names, opt.Xi[best]))
            print(f"Best: {point_text(point)} chi2={name_text(opt.yi[best])}", flush=True)
        else:
            print("Best: unavailable", flush=True)
        changed = False
        for host in list(active):
            rec = collect_task(active[host], once=True, quiet=True)
            active[host] = rec
            if rec["status"] in {"launching", "running", "finalizing"}:
                continue
            changed = True
            del active[host]
            point = rec["candidate"]
            rec = obj_func(point, cfg, seen, rec=rec)
            event += 1
            proposal = None
            if rec["status"] == "scored":
                opt.tell([point[name] for name in names], rec["total"])
                completed += 1
                result = "async_told"
            else:
                result = "async_failed"
            if completed + len(active) < args.calls:
                proposal, issued = ask_point(opt, cfg, seen, active, issued)
                active[host] = submit_task(proposal, cfg, seen, host)
                print(f"Assigned {host}: {point_text(proposal)}", flush=True)
            table = save_csv([rec], f"run-{event:03d}", result, proposal,
                             date=cfg["date"])
            print(f"{host} {result}: {completed}/{args.calls}; {table}", flush=True)
        if not changed and active:
            time.sleep(20)

    if len(opt.yi) != args.calls:
        raise RuntimeError(f"Optimization stopped at {len(opt.yi)}/{args.calls} scored candidates")
    best = int(np.argmin(opt.yi))
    winner = dict(zip(names, opt.Xi[best]))
    print(f"Optimization completed: {point_text(winner)} chi2={name_text(opt.yi[best])}",
          flush=True)

if __name__ == "__main__":
    main()
