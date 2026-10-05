# %%
### Imports
import numpy as np
import pandas as pd

from skopt import Optimizer
from skopt.space import Real
from sklearn.preprocessing import StandardScaler

import argparse
import csv
import hashlib
import json
import re
import os
import sys
import shutil
import uuid
from collections import OrderedDict
import pickle
from datetime import datetime
from pathlib import Path
import subprocess
import time
import logging
import getpass
import random
import yaml

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dragon_utils.xml_manager.parameter_map import PARAM_MAP
from dragon_utils.xml_manager.xml_modifier import find_one, get_param, load_xml, modify_xml, render_xml, set_param
from dragon_utils.CALETana_functions.datareader import readamsproflxvals, readamsHEflxvals, readamsBCratio
from dragon_utils.data_processing.physics import SM_output
from dragon_utils.data_processing.statistic_analysis import chisquare

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
def submit_task(point, cfg, seen, dry=False):
    bounds = cfg["bounds"]
    names = list(bounds)
    if set(point) != set(names):
        raise ValueError("Candidate names do not match temporary bounds")
    point = {name: float(point[name]) for name in names}
    for name, value in point.items():
        low, high = bounds[name]
        if not np.isfinite(value) or not low <= value <= high:
            raise ValueError(f"Invalid or out-of-range candidate: {name}={value}")
    key = tuple(point.values())
    if key in seen:
        raise ValueError("Duplicate candidate")

    base = ROOT / "dragon_utils/xml_manager/baseline.xml"
    binary = Path(cfg["binary"])
    if not binary.is_file() or not os.access(binary, os.X_OK):
        raise FileNotFoundError(binary)
    build = binary.parent
    out = ROOT / "outputs/task2"
    archive = ROOT / "data/dragon_output"
    out.mkdir(parents=True, exist_ok=True)
    archive.mkdir(parents=True, exist_ok=True)
    stem = datetime.now().astimezone().strftime("%Y-%m-%d") + "_run-" + uuid.uuid4().hex[:12]
    xml_path = out / f"{stem}.xml"
    diff_path = out / f"{stem}.diff"
    rec_path = out / f"{stem}.json"
    source_out = build / "output"
    if any(source_out.glob(stem + "*")):
        raise FileExistsError("Run output already exists")

    modify_xml(base, {name: repr(value) for name, value in point.items()}, xml_path, diff_path)
    source_param = build / "config_files/template.source.param"
    param_path = xml_path.with_suffix(".source.param")
    if not source_param.is_file():
        raise FileNotFoundError(source_param)
    shutil.copy2(source_param, param_path)
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
        else:
            fixed[name] = get_param(base_doc, name)
            if value != fixed[name]:
                raise ValueError(f"Fixed XML parameter changed: {name}")
    grid = find_one(run_doc, "//Grid")
    if grid.get("type") != "3D" or float(actual["VariableDelta"]) != 1:
        raise ValueError("Expected 3D VariableDelta model")
    if float(actual["Zmin"]) > 1 or float(actual["Zmax"]) < 6:
        raise ValueError("Required p, He, B and C nuclei are not propagated")
    for name in ("partialstore", "fullstore"):
        find_one(run_doc, "//Output/" + name)
    if find_one(run_doc, "//Galaxy/Diffusion").get("type") == "Anisotropic":
        raise ValueError("3D VariableDelta requires isotropic diffusion")
    threshold = float(actual["DiffusionThreshold"])
    slope = float(actual["deltaA"])
    center = float(actual["deltaB"])
    vertical = float(actual["deltaZ"])
    maximum = center + slope * min(float(actual["Rmax"]), threshold) + vertical * float(actual["L"])
    if min(threshold, slope, vertical) < 0 or center <= 0 or not np.isfinite(maximum):
        raise ValueError("Invalid 3D VariableDelta input")
    if maximum >= 2:
        raise ValueError("3D VariableDelta reacceleration limit exceeded")
    for name in point:
        set_param(run_doc, name, get_param(base_doc, name))
    if render_xml(run_doc) != render_xml(base_doc):
        raise ValueError("A fixed XML setting changed")

    with base.open("rb") as handle:
        base_hash = hashlib.file_digest(handle, "sha256").hexdigest()
    with xml_path.open("rb") as handle:
        xml_hash = hashlib.file_digest(handle, "sha256").hexdigest()
    with binary.open("rb") as handle:
        bin_hash = hashlib.file_digest(handle, "sha256").hexdigest()
    with (build / ".libs/DRAGON").open("rb") as handle:
        core_hash = hashlib.file_digest(handle, "sha256").hexdigest()
    with param_path.open("rb") as handle:
        source_hash = hashlib.file_digest(handle, "sha256").hexdigest()
    rec = {
        "id": stem,
        "status": "checked",
        "candidate": point,
        "order": names,
        "bounds": bounds,
        "units": {"D0": "1e28 cm2/s", "deltaZ": "kpc^-1"},
        "paths": {name: PARAM_MAP[name] for name in names},
        "actual": actual,
        "fixed": fixed,
        "baseline": str(base),
        "baselineHash": base_hash,
        "xml": str(xml_path),
        "xmlHash": xml_hash,
        "diff": str(diff_path),
        "binary": str(binary),
        "binaryHash": bin_hash,
        "coreBinary": str(build / ".libs/DRAGON"),
        "coreHash": core_hash,
        "sourceParam": str(param_path),
        "sourceHash": source_hash,
        "sourceMode": "per-run copy",
        "cwd": str(build),
        "command": [str(binary), str(xml_path)],
        "source": str(source_out / f"{stem}.txt"),
        "record": str(rec_path),
        "components": None,
        "total": None,
    }
    if dry:
        rec_path.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
        seen.add(key)
        return rec

    log = ROOT / "logs" / datetime.now().astimezone().strftime("%Y-%m-%d_%H-%M-%S.md")
    log.parent.mkdir(parents=True, exist_ok=True)
    while log.exists():
        time.sleep(1)
        log = ROOT / "logs" / datetime.now().astimezone().strftime("%Y-%m-%d_%H-%M-%S.md")
    start = datetime.now().astimezone()
    stdout = ""
    stderr = ""
    code = None
    try:
        done = subprocess.run(rec["command"], cwd=build, capture_output=True,
                              text=True, errors="replace", timeout=cfg["timeout"])
        code, stdout, stderr = done.returncode, done.stdout, done.stderr
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or b""
        stderr = exc.stderr or b""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", "replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", "replace")
        rec["error"] = "DRAGON2 timed out"
    end = datetime.now().astimezone()
    log.write_text("# DRAGON2 run " + stem + "\n\n"
                   + "Command: " + json.dumps(rec["command"]) + "\n"
                   + "Working directory: " + str(build) + "\n\n"
                   + "## stdout\n\n" + stdout + "\n\n## stderr\n\n" + stderr + "\n",
                   encoding="utf-8")
    rec.update({"start": start.isoformat(), "end": end.isoformat(),
                "returnCode": code, "log": str(log), "artifacts": []})
    for source in sorted(source_out.glob(stem + "*")):
        if not source.is_file():
            continue
        target = archive / source.name
        if target.exists():
            raise FileExistsError(target)
        shutil.copy2(source, target)
        with target.open("rb") as handle:
            digest = hashlib.file_digest(handle, "sha256").hexdigest()
        rec["artifacts"].append({"path": str(target), "sha256": digest,
                                 "bytes": target.stat().st_size})
    needed = {stem + ext for ext in (".txt", ".fits.gz", "_spectrum.fits.gz")}
    saved = {Path(item["path"]).name for item in rec["artifacts"]}
    if code == 0 and needed <= saved and all(item["bytes"] > 0 for item in rec["artifacts"]):
        rec["status"] = "simulated"
        rec["spectrum"] = str(archive / (stem + ".txt"))
    else:
        rec["status"] = "run_failed"
        rec.setdefault("error", "Nonzero exit or missing/empty model product")
    rec_path.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    seen.add(key)
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
        rec = submit_task(point, cfg, seen)
    else:
        if rec["returnCode"] != 0 or rec["candidate"] != point:
            raise ValueError("Resume record does not match a successful candidate")
        for name, path, digest in (("XML", rec["xml"], rec["xmlHash"]),
                                   ("source", rec["sourceParam"], rec["sourceHash"]),
                                   ("binary", rec["binary"], rec["binaryHash"]),
                                   ("core", rec["coreBinary"], rec["coreHash"]),
                                   ("spectrum", rec["spectrum"], next(
                                       item["sha256"] for item in rec["artifacts"]
                                       if item["path"] == rec["spectrum"]))):
            with Path(path).open("rb") as handle:
                if hashlib.file_digest(handle, "sha256").hexdigest() != digest:
                    raise ValueError(f"Resume {name} hash mismatch")
        seen.add(tuple(point[name] for name in cfg["bounds"]))
        rec["initialFailure"] = rec.get("error")
        rec.pop("error", None)
        rec["status"] = "simulated"
    if rec["status"] != "simulated":
        return rec
    try:
        spec = Path(rec["spectrum"])
        with spec.open(encoding="utf-8") as handle:
            header = handle.readline().split()
        if header[:2] != ["Energy", "[GeV]"]:
            raise ValueError("Invalid DRAGON2 ASCII header")
        columns = header[2:]
        required = ("Pri_p", "Sec_p", "NUC_2003", "NUC_2004",
                    "NUC_5010", "NUC_5011", "NUC_6012", "NUC_6013", "NUC_6014")
        if any(columns.count(name) != 1 for name in required):
            raise ValueError("Required isotope column missing or duplicated")
        data = np.loadtxt(spec, skiprows=1)
        if data.ndim != 2 or data.shape[0] < 2 or data.shape[1] != len(columns) + 1:
            raise ValueError("Incomplete DRAGON2 ASCII table")
        if not np.all(np.isfinite(data)) or np.any(data[:, 0] <= 0) or np.any(np.diff(data[:, 0]) <= 0):
            raise ValueError("Invalid model energy axis or values")
        energy = data[:, 0]
        base = str(ROOT / "data/experiment_data/expdata") + "/"
        observed = {
            "p": readamsproflxvals(base, convtoE=False),
            "He": readamsHEflxvals(base, convtoE=False),
            "BC": readamsBCratio(base),
        }
        limits = {"p": 30, "He": 30, "BC": 10}
        counts = {"p": 36, "He": 37, "BC": 40}
        species = {
            "p": (("p", 1, 1, 0.938272046),),
            "He": (("NUC_2003", 2, 3, 3 * 0.931494),
                   ("NUC_2004", 2, 4, 3.727379508)),
            "BC": (("NUC_5010", 5, 10, 10 * 0.931494),
                   ("NUC_5011", 5, 11, 11 * 0.931494),
                   ("NUC_6012", 6, 12, 12 * 0.931494),
                   ("NUC_6013", 6, 13, 13 * 0.931494),
                   ("NUC_6014", 6, 14, 14 * 0.931494)),
        }
        parts = {}
        rows = []
        for mode in ("p", "He", "BC"):
            points = [(float(axis), float(vals[0]), float(vals[1]), vals[2])
                      for axis, vals in observed[mode].items() if vals[2][0] >= limits[mode]]
            if len(points) != counts[mode]:
                raise ValueError(f"Unexpected observation count for {mode}")
            axis = np.array([item[0] for item in points])
            obs = np.array([item[1] for item in points])
            error = np.array([item[2] for item in points])
            model = np.zeros(len(points))
            boron = np.zeros(len(points))
            carbon = np.zeros(len(points))
            phi = cfg["phi"][mode]
            for name, charge, massnum, mass in species[mode]:
                if mode == "BC":
                    kinetic = axis
                else:
                    kinetic = (np.sqrt((charge * axis) ** 2 + mass ** 2) - mass) / massnum
                if mode == "p":
                    primary = data[:, columns.index("Pri_p") + 1]
                    secondary = data[:, columns.index("Sec_p") + 1]
                    if np.any(primary <= 0) or np.any(secondary < 0):
                        raise ValueError("Invalid proton component")
                    flux = (primary + secondary) / 10000
                else:
                    flux = data[:, columns.index(name) + 1] / 10000
                _, toa = SM_output(energy, flux, PhiP=phi, Mass=mass / massnum,
                                   output_energies=kinetic, charge=charge, massnum=massnum)
                if mode == "BC":
                    if name.startswith("NUC_5"):
                        boron += toa
                    else:
                        carbon += toa
                else:
                    total = massnum * kinetic
                    model += toa * charge * np.sqrt(total * (total + 2 * mass)) / (
                        massnum * (total + mass))
            if mode == "BC":
                if np.any(carbon <= 0):
                    raise ValueError("Nonpositive carbon denominator")
                model = boron / carbon
            result = chisquare(obs, model, error, return_points=True)
            parts[mode] = result["chi2"]
            for i, item in enumerate(points):
                rows.append({
                    "run": rec["id"], "observable": mode, "axis": item[0],
                    "lower": item[3][0], "upper": item[3][1],
                    "observed": obs[i], "model": model[i], "error": result["sigma"][i],
                    "residual": result["residual"][i],
                    "contribution": result["contribution"][i], "phi": phi,
                })
        total = float(sum(parts.values()))
        if not np.isfinite(total) or total < 0:
            raise ValueError("Invalid total chi-square")
        out = ROOT / "outputs/task2" / (rec["id"] + "-residual.csv")
        with out.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        with out.open("rb") as handle:
            digest = hashlib.file_digest(handle, "sha256").hexdigest()
        rec.update({"status": "scored", "components": parts, "total": total,
                    "points": str(out), "pointsHash": digest, "count": counts})
    except Exception as exc:
        rec.update({"status": "evaluation_failed", "error": str(exc), "total": None})
    Path(rec["record"]).write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    return rec

# %%
def get_pointsInBounds(bounds, X, y):
    X_der = X.copy().reset_index(drop=True)
    y_der = y.copy().reset_index(drop=True)
    
    for col, (low, high) in zip(X_der.columns, bounds):
        X_der = X_der[(X_der[col]>=low) & (X_der[col]<=high)]
        
    by = y_der.loc[X_der.index].reset_index(drop=True)
    bX = X_der.reset_index(drop=True)
    
    return (bX, by)

# %%
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--runs", type=int, default=2)
    parser.add_argument("--resume")
    args = parser.parse_args()
    if args.runs not in (1, 2):
        raise ValueError("Task 2 accepts one or two local runs")
    with (Path(__file__).parent / "config.yaml").open(encoding="utf-8") as handle:
        cfg = yaml.safe_load(handle)["local"]
    names = list(cfg["bounds"])
    if set(names) != set(cfg["seed"]):
        raise ValueError("Seed and temporary bounds differ")
    seen = set()
    first = submit_task(cfg["seed"], cfg, seen, dry=True)
    second = dict(cfg["seed"])
    second[names[0]] = cfg["bounds"][names[0]][1]
    if second == cfg["seed"]:
        second[names[0]] = cfg["bounds"][names[0]][0]
    other = submit_task(second, cfg, seen, dry=True)
    if first["xmlHash"] == other["xmlHash"] or first["source"] == other["source"]:
        raise ValueError("Preflight candidates share XML or output")
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
    sample = Path(cfg["sample"])
    format_ok = False
    if sample.is_file():
        with sample.open(encoding="utf-8") as handle:
            header = handle.readline().split()
        format_ok = (header[:2] == ["Energy", "[GeV]"] and
                     all(header.count(name) == 1 for name in
                         ("Pri_p", "Sec_p", "NUC_2003", "NUC_2004",
                          "NUC_5010", "NUC_5011", "NUC_6012", "NUC_6013", "NUC_6014")))
        if not format_ok:
            raise ValueError("Historical sample format is invalid")
    check = {
        "status": "passed", "first": first["record"], "second": other["record"],
        "differentXml": True, "differentOutput": True, "observations": counts,
        "sample": str(sample), "sampleFormat": format_ok,
        "sampleUse": "header check only; never scored",
    }
    check_path = ROOT / "outputs/task2" / (
        datetime.now().astimezone().strftime("%Y-%m-%d") + "_check-" + uuid.uuid4().hex[:12] + ".json")
    check_path.write_text(json.dumps(check, indent=2) + "\n", encoding="utf-8")
    print(f"Preflight: {check_path}", flush=True)
    if args.check:
        return

    opt = Optimizer([Real(*cfg["bounds"][name], name=name) for name in names],
                    base_estimator="GP", n_initial_points=1, random_state=cfg["seedValue"])
    seen = set()
    point = dict(cfg["seed"])
    history = []
    path = ROOT / "outputs/task2" / (
        datetime.now().astimezone().strftime("%Y-%m-%d") + "_search-" + uuid.uuid4().hex[:12] + ".json")
    for index in range(args.runs):
        prior = None
        if index == 0 and args.resume:
            prior = json.loads(Path(args.resume).read_text(encoding="utf-8"))
            if prior["status"] not in ("evaluation_failed", "simulated"):
                raise ValueError("Only a completed simulation can be resumed")
            if "sourceParam" not in prior:
                source_param = Path(cfg["binary"]).parent / "config_files/template.source.param"
                log = Path(prior["log"]).read_text(encoding="utf-8")
                if "Using config_files/template.source.param!" not in log:
                    raise ValueError("Cannot establish source file used by prior run")
                if source_param.stat().st_mtime > datetime.fromisoformat(prior["start"]).timestamp():
                    raise ValueError("Fallback source file changed after prior run")
                param_path = Path(prior["xml"]).with_suffix(".source.param")
                shutil.copy2(source_param, param_path)
                with param_path.open("rb") as handle:
                    prior["sourceHash"] = hashlib.file_digest(handle, "sha256").hexdigest()
                prior["sourceParam"] = str(param_path)
                prior["sourceMode"] = "fallback during run; copied after for replay"
            core = Path(cfg["binary"]).parent / ".libs/DRAGON"
            with core.open("rb") as handle:
                prior["coreHash"] = hashlib.file_digest(handle, "sha256").hexdigest()
            prior["coreBinary"] = str(core)
        rec = obj_func(point, cfg, seen, rec=prior)
        rec["index"] = index + 1
        if rec["status"] == "scored":
            opt.tell([point[name] for name in names], rec["total"])
            point = dict(zip(names, opt.ask()))
            rec["nextProposal"] = point
        else:
            rec["nextProposal"] = None
        Path(rec["record"]).write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
        history.append(rec)
        path.write_text(json.dumps(history, indent=2) + "\n", encoding="utf-8")
        print(f"Run {index + 1}: {rec['status']} {rec['id']} chi2={rec['total']}", flush=True)
        if rec["status"] != "scored":
            raise RuntimeError(f"Run stopped: {rec['error']}; record: {rec['record']}")
    print(f"Ordered record: {path}", flush=True)

if __name__ == "__main__":
    main()
