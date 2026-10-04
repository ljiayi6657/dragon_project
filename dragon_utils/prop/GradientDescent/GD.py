# %% [markdown]
# ### Imports, Loading Model & Defining Optimization

# %%
#Required modules
import pandas as pd
import numpy as np

from sklearn.preprocessing import StandardScaler, RobustScaler, PolynomialFeatures, SplineTransformer, MaxAbsScaler, FunctionTransformer 
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.model_selection import cross_val_score, KFold
from hyperopt import fmin, tpe, hp, Trials, STATUS_OK
from scipy.optimize import minimize

import subprocess
import os
import sys
import yaml
import pickle
from datetime import datetime
import time
import re
import json
from collections import OrderedDict
import logging
import random
import getpass

# %% [markdown]
# ### Loading Configuration Files

# %%
def load_config():
    try: script_dir = os.path.dirname(os.path.realpath(__file__))
    except: script_dir = f"/home/{getpass.getuser()}/CALETana/prop/GradientDescent"
    with open(os.path.join(script_dir, "config.yaml"), "r") as file:
        config = yaml.safe_load(file)
    GD_settings = config["GD_settings"]
    preset_parameters = config["preset_parameters"]
    comp_settings = config["comp_settings"]
    paths = config["paths"]
    return GD_settings, preset_parameters, comp_settings, paths


# %% [markdown]
# ### Updating Dragon Data

# %%
def update_data(fitSpectra_path):
    directory = os.path.dirname(fitSpectra_path)
    file_name = os.path.basename(fitSpectra_path)
    
    os.chdir(directory)
    #command = f"./{file_name}"  
    command = f"python {file_name}"    
    filenumber = None

    # Execute fitspectra-xxx in interactive mode (read write to console possible)
    with subprocess.Popen(command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1, universal_newlines=True) as process:
        logging.info("\n")
        logging.info("-"*20+"Fitting potential new simulations"+"-"*20)
        start_time = time.time()                                    # To check whether we are caught in a loop
        
        while True:
            output = process.stdout.readline().strip()              # IMPORTANT: in fitSpectra-xxx's "input('text')" prompts end all the lines with 'text\n', otherwise readline() cannnot read the input prompt and we wait forever!!!
            if type(output)!=str: output = output.decode()
            #print(output)
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

# %% [markdown]
# ### Load Data

# %%
def load_data(dragon_datapath,interpol_datapath,GD_settings,preset_parameters):
    logging.info("\n")
    logging.info("-"*20+"Loading and processing new data"+"-"*20)

    # 1. Load data and save in pd.DataFrame
    data_loaded = False
    while not data_loaded:
        try:
            with open(dragon_datapath, "rb") as file:
                hashdict,foundfiles,globpardict,pflxs,pfs,x2s,x2dict,vx2s,vx2dict,rx2s,rx2dict,px2s,px2dict,hx2s,hx2dict,fx2s,fx2dict,qx2s,qx2dict,vfx2s,vfx2dict,likes,likedict,mlikes,mlikedict,tlikes,tlikedict,qlikes,qlikedict,slikes,slikedict,mx2s,mx2dict,sx2s,cx2dict,cx2s,sx2dict,clikes,clikedict,tss,tsdict,faultfiles,faultpardict,corrfactlist = pickle.load(file)
                lossparamdict={"x":x2s,"v":vx2s,"r":rx2s,"p":px2s,"h":hx2s,"f":fx2s,"q":qx2s,"vf":vfx2s,"l":likes,"ml":mlikes,"tl":tlikes,"ql":qlikes,"sl":slikes,"m":mx2s,"s":sx2s,"c":cx2s,"cl":clikes}
                globpardict["Y"]=lossparamdict[GD_settings["lossparameter"]]
                data = pd.DataFrame.from_dict(globpardict)
                faultdata = pd.DataFrame.from_dict(faultpardict)
            data_loaded = True
        except Exception as e:
            logging.warning(f"Error occured: {e}")
            logging.info("Two runs might be trying to access data simultaneously. Waiting before trying again.")
            time.sleep(random.randint(0, 300)) 

    logging.info(f"Total simulations loaded: {len(data)+len(faultdata)}")
    logging.info(f"Number failed simulations: {len(faultfiles)}")

    # 1 a load interpolation data
    
    data["W"]=1.0
    data["iI"]=False
    if GD_settings["useinterpoldata"]:
        intpdata=load_interpolation_data(interpol_datapath,GD_settings)                
        intpdata["iI"]=True
        data = pd.concat([data,intpdata], ignore_index=True, axis=0).reset_index(drop=True)
        
    # 2. Process data by dropping nans and infs  
    init_len = len(data)
    
    if GD_settings["infliketreatment"]=="replace":
        if GD_settings["maxloss"]=="maxval":
            maxloss=data.loc[data["Y"]!=np.inf, "Y"].max()
            print("maxloss set to : ",maxloss)
        elif GD_settings["maxloss"]=="default":            
            if "l" in GD_settings["lossparameter"]:
                maxloss=-np.log(sys.float_info.min)
            else:
                maxloss=sys.float_info.max**0.1
        else:
            maxloss=int(GD_settings["maxloss"]) 
        data.replace([np.inf, -np.inf], maxloss, inplace=True)    
        faultreplace=faultdata.copy()
        faultreplace["Y"]=[maxloss]*len(faultdata)
        faultreplace["W"]=1.0
        faultreplace["iI"]=False
        data = pd.concat([data, faultreplace], ignore_index=True, axis=0).reset_index(drop=True)
        data = data.dropna().reset_index(drop=True)
        post_len = len(data)
    elif GD_settings["infliketreatment"]=="remove":
        maxloss=np.inf
        data.replace([np.inf, -np.inf], np.nan, inplace=True)
        faultdata = pd.concat([faultdata, data[data.isna().any(axis=1)].copy()], ignore_index=True, axis=0).drop(columns=["Y","W","iI"]).reset_index(drop=True)
        data = data.dropna().reset_index(drop=True)
        post_len = len(data)    
        logging.info(f"Number inf/nan simulations: {(init_len-post_len)}")
    logging.info(f"Final selected simulations: {post_len}")
    logging.info(f"Best neg. log-likelihood: { np.min(data['Y']) }")
    
    #data.replace([np.inf, -np.inf], np.nan, inplace=True)
    #faultdata = pd.concat([faultdata, data[data.isna().any(axis=1)].copy()], ignore_index=True, axis=0).drop(columns=["Y","W","iI"]).reset_index(drop=True)
    ###### Improvement possibility: handle inf/nan/fails differently by assigning high neg. log-likelihood ######
    #data = data.dropna().reset_index(drop=True)
    #post_len = len(data)
    
    #logging.info(f"Number inf/nan simulations: {(init_len-post_len)}")
    #logging.info(f"Final selected simulations: {post_len}")
    #logging.info(f"Best neg. log-likelihood: { np.min(data['Y']) }")

    # 3. Filter data for preset parameters
    if preset_parameters!=None:
        beforefilterlen=len(data)
        logging.info(f"Simulations before preset parameters filter: {beforefilterlen}")
        data = filter_points(data, preset_parameters)
        afterfilterlen=len(data)
        logging.info(f"Simulations before preset parameters filter: {afterfilterlen}")

    w_data = data[["W"]].copy()
    data = data.copy().drop(columns=w_data.columns)
    y_data = data[["Y"]].copy()
    data = data.copy().drop(columns=y_data.columns)
    isintpol = data[["iI"]].copy()
    X_data = data.copy().drop(columns=isintpol.columns)
    
    
    # 4. Fitting scalers to standardize data  
    if GD_settings["scaler"]=="Standard":
        Xscaler = StandardScaler()
        yscaler = StandardScaler()
    elif GD_settings["scaler"]=="Robust":
        Xscaler = RobustScaler()
        yscaler = RobustScaler()
    X_scaled = pd.DataFrame(Xscaler.fit_transform(X_data.copy()), columns=X_data.columns)
    y_scaled = pd.DataFrame(yscaler.fit_transform(y_data.copy()), columns=y_data.columns)
    return X_data, y_data, X_scaled, y_scaled, Xscaler, yscaler, w_data, isintpol, faultdata

# %% [markdown]
# ### Load/Save Previous Gradient Descent Or Current Best Point


def load_interpolation_data(interpol_datapath,GD_settings):
    logging.info("\n")
    logging.info("-"*20+"Loading and processing new interpolation data"+"-"*20)    
    data_loaded = False
    while not data_loaded:
        try:
            with open(interpol_datapath, "rb") as file:
                interpolmap=pickle.load(file)            
            data_loaded = True
        except Exception as e:
            logging.warning(f"Error occured: {e}")
            logging.info("Two runs might be trying to access data simultaneously. Waiting before trying again.")
            time.sleep(random.randint(0, 300))
    interpolpointdict={}
    parentinfodict1={}
    parentinfodict2={}
    firstentry=True
    lossparamdict={"x":0,"v":2,"r":3,"p":4,"h":5,"f":6,"q":7,"vf":8,"l":9,"ml":10,"tl":11,"ql":12,"sl":13,"m":14,"s":15}
    lossparamcode=lossparamdict[GD_settings["lossparameter"]]
    preweight=GD_settings["interpoldataweight"]
    for d,interpolfits in interpolmap.items():
        (parentfiledata,params,likes)=interpolfits
        #pfd: (p1s,p2s,ws,foundfiles[d[0]],foundfiles[d[1]])
        if firstentry:            
            for param in params[parentfiledata[2][0]].keys(): 
                interpolpointdict[param]=[]
                interpolpointdict["Y"]=[]
                #interpolpointdict["W"]=[]
                parentinfodict1[param]=[]
                parentinfodict2[param]=[]
                firstentry=False
        for w in parentfiledata[2]:
            for pn,pv in params[w].items(): 
                interpolpointdict[pn].append(pv)
            for pn,pv in parentfiledata[0].items(): 
                parentinfodict1[pn].append(pv)
            for pn,pv in parentfiledata[1].items(): 
                parentinfodict2[pn].append(pv)
            interpolpointdict["Y"].append(likes[w][lossparamcode])
            #interpolpointdict["W"].append(weight)
    interpoldata = pd.DataFrame.from_dict(interpolpointdict)
    parentinfo1 = pd.DataFrame.from_dict(parentinfodict1)
    parentinfo2 = pd.DataFrame.from_dict(parentinfodict2)
    if GD_settings["scaler"]=="Standard":
        interpol_scaler = StandardScaler()
    elif GD_settings["scaler"]=="Robust":
        interpol_scaler = RobustScaler()
    interpol_scale = pd.DataFrame(interpoldata.copy(), columns=interpoldata.columns)
    interpol_scale.drop(columns=["Y"], inplace=True)
    interpol_scaled = interpol_scaler.fit_transform(interpol_scale)
    parentinfo1_scaled = pd.DataFrame(interpol_scaler.transform(parentinfo1.copy()), columns=parentinfo1.columns)
    parentinfo2_scaled = pd.DataFrame(interpol_scaler.transform(parentinfo2.copy()), columns=parentinfo2.columns)
    distances = np.linalg.norm(parentinfo2-parentinfo1, axis=1)
    weights = np.power(distances+1.0,-int(GD_settings["dist_weight_power"]))
    interpoldata["W"]=preweight*weights
    return interpoldata
    
# %%
def save_current_data(points, momenta, losses, gradients, folder):
    # save data to file in folder
    with open(os.path.join(folder,"data.pkl"), "wb") as file:
        save_data = {"points": points, "momenta": momenta, "losses": losses, "gradients": gradients}
        pickle.dump(save_data, file)  
    logging.info("\n")
    logging.info("-"*20+"Saved new data"+"-"*20)

def generate_saveFolderName(path, comp_settings, settings):
    load_previous=comp_settings["load_previous"]
    IP=comp_settings["simulation_IP"]
    folder_prefix = get_folderPrefix(IP,settings)
    
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

def get_folderPrefix(IP,s):
    if s['fit_mode'] == "Auto": prefix = f"IP{IP}_{s['lossparameter']}_{s['model_type']}_{s['n_closest_points']}_{s['weighting']}_{s['fit_mode']}_{s['momentum_type']}_decay{s['momentum_decay']}_lr{s['learning_rate']}"
    else: prefix = f"IP{IP}_{s['lossparameter']}_{s['model_type']}_{s['n_closest_points']}_{s['weighting']}_deg{s['degree']}alpha{s['alpha']}_{s['momentum_type']}_decay{s['momentum_decay']}_lr{s['learning_rate']}"
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

def load_previous_descentData(folder):
    # loads most previous data with given settings from folder 
    with open(os.path.join(folder, "data.pkl"), "rb") as file:
        save_data = pickle.load(file)
        points = save_data["points"]
        momenta = save_data["momenta"]
        losses = save_data["losses"]
        gradients = save_data["gradients"]
    return points, momenta, losses, gradients

def get_best_point(X, y, iI):
    # returns the n best X,y parameters in terms of log-likelihood
    X_der = X.copy()[~iI["iI"]].reset_index(drop=True)
    y_der = y.copy()[~iI["iI"]].reset_index(drop=True)
    ycolumn = y_der.columns[0]    
    top_index = y_der.sort_values(by=ycolumn, ascending=True).head(1).index.tolist()
    top_y = y_der.loc[top_index].reset_index(drop=True)
    top_X = X_der.loc[top_index].reset_index(drop=True)
    return [top_X], [pd.DataFrame(0., index=range(1), columns=X_der.columns)], [top_y.values[0].item()]

def get_random_point(X, y, iI):
    X_der = X.copy()[~iI["iI"]].reset_index(drop=True)
    y_der = y.copy()[~iI["iI"]].reset_index(drop=True)
    ycolumn = y_der.columns[0]
    invy=[1.0/a for a in y_der[ycolumn].tolist()]
    norm=sum(invy)
    weights=[a/norm for a in invy]
    rand_indx = y_der.sample(1,weights=weights).index.tolist()
    rand_y = y_der.loc[rand_indx].reset_index(drop=True)
    rand_X = X_der.loc[rand_indx].reset_index(drop=True)
    return [rand_X], [pd.DataFrame(0., index=range(1), columns=X_der.columns)], [rand_y.values[0].item()]
    
def get_farthest_point(X, y, sX, iI, maxloss=False):
    bp, bm, bl = get_best_point(sX, y, iI)    
    X_der = X.copy()[~iI["iI"]].reset_index(drop=True)
    y_der = y.copy()[~iI["iI"]].reset_index(drop=True)
    sX_der = sX.copy()[~iI["iI"]].reset_index(drop=True)  
    if maxloss:
        y_filt_indices=y_der[y_der["Y"]<maxloss].index.tolist()
        X_der = X_der.copy().iloc[y_filt_indices].reset_index(drop=True)
        y_der = y_der.copy().iloc[y_filt_indices].reset_index(drop=True)
        sX_der = sX_der.copy().iloc[y_filt_indices].reset_index(drop=True)  
    bpf=pd.DataFrame(bp[0], columns=sX.columns).reindex_like(sX_der,method="nearest")  
    distances = np.linalg.norm(sX_der-bpf, axis=1)    
    far_indx = np.argsort(distances)[-1:]
    far_y = y_der.loc[far_indx].reset_index(drop=True)
    far_X = X_der.loc[far_indx].reset_index(drop=True)
    print("distance of farthest point ",distances[far_indx[0]])
    return [far_X], [pd.DataFrame(0., index=range(1), columns=X_der.columns)], [far_y.values[0].item()]




# %%
def checkSimulationProgress(X_data_all, y_data_all, X_fault, point_list, loss_list, isintpol):
    logging.info("\n")
    logging.info("-"*20+"Checking for finished simulations"+"-"*20)
    simulation_finished, simulation_infnan = False, False
    X_data=X_data_all.copy()[~isintpol["iI"]].reset_index(drop=True)
    y_data=y_data_all.copy()[~isintpol["iI"]].reset_index(drop=True)
    match = X_data[(X_data==point_list[-1].iloc[0]).all(axis=1)]
    #Check whether last point is in new data and save its new loss
    if not match.empty: 
        logging.info("A simulation has finished successfully")
        if(len(point_list)!=len(loss_list)): loss_list.append(y_data.iloc[match.index[0],0])
        logging.info(f"Point:\n{point_list[-1].iloc[0]}")
        logging.info(f"Loss: {loss_list[-1]}")
        simulation_finished = True
    if ((X_fault == point_list[-1].iloc[0]).all(axis=1)).any():  # Check whether last point simulation has failed
        logging.error(f"\033[91m Problem occured \033[0m: Simulation of point failed or is inf\n{point_list[-1].iloc[0]}")
        if(len(point_list)!=len(loss_list)): loss_list.append(np.inf)
        logging.info(f"Point:\n{point_list[-1].iloc[0]}")
        logging.info(f"Loss: {loss_list[-1]}")
        simulation_finished, simulation_infnan = True, True      # for failed simulations: take last working point and only take half of the last not working step size (momentum)         
    return simulation_finished, simulation_infnan

def checkPointAlreadyCalculated(new_point, X_data_all, X_fault, isintpol):
    already_calculated=False
    X_data=X_data_all.copy()[~isintpol["iI"]].reset_index(drop=True)
    match = X_data[(X_data==new_point.iloc[0]).all(axis=1)]
    if not match.empty: 
        logging.info("Point already in data list")
        already_calculated=True
    if ((X_fault == new_point.iloc[0]).all(axis=1)).any(): 
        logging.info("Point already in faultdata list")
        already_calculated=True
    return already_calculated


# %%
def get_expweights(y_scaled):
    y = y_scaled.copy().reset_index(drop=True)
    weights = np.exp(-y.iloc[:,0])
    eweights=pd.DataFrame(weights, columns=y.columns)
    eweights.rename(columns={"Y":"W"},inplace=True)
    return eweights
        
def get_distweights(X_scaled,point,power):
    #print("points:",X_scaled)
    X_der = X_scaled.copy().reset_index(drop=True)
    point_der = point.copy().iloc[0]
    distances = np.linalg.norm(X_der-point_der, axis=1)
    #print("distance max:",max(distances))
    #print("distance avg:",sum(distances)/len(distances))
    weights = np.power(distances+1.0,-power)
    #print("weight max:",max(weights))
    #print("weight avg:",sum(weights)/len(weights))
    #sys.exit(1)
    return pd.DataFrame(weights,columns=["W"])

def weighted_mse(y_true, y_pred, weights):
    return np.average((y_true-y_pred)**2, weights=weights)

def objective(X_scaled_raw, y_scaled_raw, params, weights=None, point_scaled=None, loss_scaled=None, model_type="Polynomial", force_center=False):
    degree = int(params["degree"])
    alpha = params["alpha"]
    if "knots" in params:
        nknots = int(params["knots"])
    else:
        nknots = None
    if "npoints" in params:
        npoints = int(params["npoints"])
        X_scaled, y_scaled = closest_points(X_scaled_raw, y_scaled_raw, point_scaled, npoints)    
    else:
        X_scaled, y_scaled = X_scaled_raw.copy(), y_scaled_raw.copy()
        
    if force_center:        
        X_shifted=recenter_data(X_scaled,point_scaled)
        XMMscaler=MaxAbsScaler().fit(X_shifted)
        X_shifted=pd.DataFrame(XMMscaler.transform(X_shifted.copy()),columns=X_shifted.columns)
        y_shifted=recenter_data(y_scaled,loss_scaled)
        yMMscaler=MaxAbsScaler().fit(y_shifted)
        y_shifted=pd.DataFrame(yMMscaler.transform(y_shifted.copy()),columns=y_shifted.columns)
    else:
        X_shifted,y_shifted=X_scaled, y_scaled   
        
    model=createRidgeModel(X_shifted, y_shifted, degree, alpha, point=point_scaled, loss=loss_scaled, distweightpower=None, model_type=model_type , knots=nknots, force_center=force_center, weights=weights)
    
    kf = KFold(n_splits=10, shuffle=True)
    mse_scores = []
    for train_index, test_index in kf.split(X_shifted):
        X_train, X_test = X_shifted.iloc[train_index], X_shifted.iloc[test_index]
        y_train, y_test = y_shifted.iloc[train_index], y_shifted.iloc[test_index]
        if isinstance(weights, pd.DataFrame):
            weights_train, weights_test = weights.iloc[train_index], weights.iloc[test_index]
            model.fit(X_train, y_train.values.ravel(), ridge__sample_weight=weights_train.values.ravel())
            y_pred = model.predict(X_test)
            mse_scores.append(weighted_mse(y_test.values.ravel(), y_pred, weights_test.values.ravel()))
        else:
            model.fit(X_train, y_train.values.ravel())
            y_pred = model.predict(X_test)
            mse_scores.append(np.average((y_test.values.ravel()-y_pred)**2))
    score = np.mean(mse_scores)
    return {"loss": score, "status": STATUS_OK}


def determine_hyperparams(X_scaled, y_scaled, w_data, point_list, loss_list, Xscaler, yscaler, GD_settings, preset_parameters):
    # Given some parameter bounds determine the best hyperparameters for the ridge regression with tree-structured parzen estimator (TPE)
    logging.info("\n")
    logging.info("-"*20+"Determining best fit hyperparameters"+"-"*20)
    point = point_list[-1].copy()
    point_scaled = pd.DataFrame(Xscaler.transform(point), columns=point.columns)
    loss=pd.DataFrame([loss_list[-1]],columns=y_scaled.columns)
    loss_scaled = pd.DataFrame(yscaler.transform(loss.copy()), columns=loss.columns)
    if GD_settings["n_closest_points"] in ["Global","Auto"]: closest_X_scaled, closest_y_scaled, closest_w_data = X_scaled.copy(), y_scaled.copy(), w_data.copy()
    else: closest_X_scaled, closest_y_scaled, closest_w_data = closest_points(X_scaled, y_scaled, w_data, point_scaled, int(GD_settings["n_closest_points"]))
    space = {# manual trials are showing that degree 1 is really bad, degree 4 is almost never yielding any improvement and probably compromising on extrapolation for momentum, alpha is usually in [0.05, 1]         
        "alpha": hp.loguniform("alpha", np.log(1e-2), np.log(1e2))
    }
    if GD_settings["model_type"]=="Spline": 
        space["knots"]=hp.quniform("knots", 2,int(GD_settings["max_knots"]),1)
    if GD_settings["max_degree"]>2: 
        space["degree"]=hp.quniform("degree", 2,int(GD_settings["max_degree"]),1)
    else:
        space["degree"]=hp.choice("degree",[2])
    if GD_settings["n_closest_points"] == "Auto": space["npoints"]=hp.loguniform("npoints", np.log(1e2), np.log(len(X_scaled)))
        
    if preset_parameters!=None:
        presence = [item in closest_X_scaled.columns for item in list(preset_parameters.keys())]
        for i, present in enumerate(presence):
            if not present: logging.warning(f"There is no parameter {list(preset_parameters.keys())[i]} in data which could be preset!")
        closest_X_scaled = closest_X_scaled.drop(columns=list(preset_parameters.keys()))
        point_scaled = point_scaled.drop(columns=list(preset_parameters.keys()))
        
    trials = Trials()
    if GD_settings["weighting"]=="Exponential":
        weights = get_expweights(y_scaled) * closest_w_data 
        best = fmin(
            fn=lambda params: objective(X_scaled_raw=closest_X_scaled, y_scaled_raw=closest_y_scaled, params=params, weights=weights, point_scaled=point_scaled, loss_scaled=loss_scaled, model_type=GD_settings["model_type"], force_center=GD_settings["force_center"]),
            space = space,
            algo = tpe.suggest,
            max_evals = 10**len(space.keys()),
            trials = trials
            )
    elif GD_settings["weighting"]=="Distance":        
        weights =  get_distweights(closest_X_scaled,point_scaled,int(GD_settings["dist_weight_power"])) * closest_w_data
        best = fmin(
            fn=lambda params: objective(X_scaled_raw=closest_X_scaled, y_scaled_raw=closest_y_scaled, params=params, weights=weights, point_scaled=point_scaled, loss_scaled=loss_scaled, model_type=GD_settings["model_type"], force_center=GD_settings["force_center"]),
            space = space,
            algo = tpe.suggest,
            max_evals = 10**len(space.keys()),
            trials = trials
            )
    elif GD_settings["weighting"]=="None":
        weights=closest_w_data
        best = fmin(
            fn=lambda params: objective(X_scaled_raw=closest_X_scaled, y_scaled_raw=closest_y_scaled, params=params, weights=weights, point_scaled=point_scaled, loss_scaled=loss_scaled, model_type=GD_settings["model_type"], force_center=GD_settings["force_center"]),
            space = space,
            algo = tpe.suggest,
            max_evals = 10**len(space.keys()),
            trials = trials
            )    
    else: raise ValueError("Not a valid weighting method for fitting")    
        
        
    if GD_settings["max_degree"]>2: 
        GD_settings["degree"]=best["degree"]
    else:
        GD_settings["degree"]=2
    GD_settings["alpha"]=best["alpha"]
    if GD_settings["model_type"]=="Spline": 
        GD_settings["knots"]=best["knots"]
    if GD_settings["n_closest_points"] == "Auto":  
        GD_settings["npoints"]=best["npoints"]
        if GD_settings["model_type"]=="Spline": 
            logging.info(f"Best parameters are: degree={best['degree']}, alpha={best['alpha']}, knots={best['knots']}, npoints={best['npoints']}")
        else:
            logging.info(f"Best parameters are: degree={best['degree']}, alpha={best['alpha']}, npoints={best['npoints']}")
    else:   
        if GD_settings["model_type"]=="Spline": 
            logging.info(f"Best parameters are: degree={best['degree']}, alpha={best['alpha']}, knots={best['knots']}")
        else:
            logging.info(f"Best parameters are: degree={best['degree']}, alpha={best['alpha']}")

# %% [markdown]
# ### Conduct Gradient Descent Step

# %%
# returns the n closest X,y parameters to a point in terms of euclidian distance in parameter space
def closest_points(X, y, w, point, n):
    X_der = X.copy().reset_index(drop=True)
    y_der = y.copy().reset_index(drop=True)
    w_der = w.copy().reset_index(drop=True)
    point_der = point.copy().iloc[0]
    distances = np.linalg.norm(X_der-point_der, axis=1)

    closest_indices = np.argsort(distances)[:n]
    closest_X = X_der.loc[closest_indices].reset_index(drop=True)
    closest_y = y_der.loc[closest_indices].reset_index(drop=True)
    closest_w = w_der.loc[closest_indices].reset_index(drop=True)
    return closest_X, closest_y, closest_w

def filter_points(X, preset_parameters):
    X_filt = X.copy().reset_index(drop=True)
    for col_name,value in  preset_parameters.items():
        dropindx=X_filt.index[X_filt[col_name]!=value]
        X_filt.drop(dropindx,inplace=True)
    filtered_X = X_filt.reset_index(drop=True)
    return filtered_X

def recenter_data(X_scaled,X_center):
    X_shifted=X_scaled.copy()-X_center.reindex_like(X_scaled,method="nearest")  
    return X_shifted

def recenter_data_inv(X_shifted,X_center):
    X_scaled=X_shifted.copy()+X_center.reindex_like(X_shifted,method="nearest")        
    return X_scaled

def createRidgeModel(X_scaled, y_scaled, degree, alpha, point=None, loss=None, distweightpower=None, model_type="Polynomial" , knots=None, force_center=False,  weights=pd.DataFrame([])):
    #if force_center:
    #    shift = FunctionTransformer(recenter_data, inverse_func=recenter_data_inv, kw_args={"X_center":point}, inv_kw_args={"X_center":point})
    #    X_shifted=recenter_data(X_scaled,point)
    #    y_shifted=recenter_data(y_scaled,loss)
    #else:
    #    X_shifted,y_shifted=X_scaled, y_scaled   
    # IMPORTANT: input data has to normalized for fit to work most effectively!
    if model_type=="Polynomial":
        mod = PolynomialFeatures(degree=degree, include_bias=False)        
    elif model_type=="Spline":
        mod = SplineTransformer(n_knots=knots, degree=degree, include_bias=False)
    
    ridge = Ridge(alpha=alpha,fit_intercept=not force_center)    
    X_tr_mod = mod.fit_transform(X_scaled)
        
    
    #if not weights.empty:
    ridge.fit(X_tr_mod, y_scaled, weights.values.ravel())
    
    
    #else:
    #    if weighting=="Exponential":
    #        tr_weights = get_expweights(y_scaled)
    #        ridge.fit(X_tr_mod, y_scaled, tr_weights.values.ravel()) 
    #    elif weighting=="Distance":
    #        tr_weights = get_distweights(X_scaled,point,distweightpower)
    #        ridge.fit(X_tr_mod, y_scaled, tr_weights.values.ravel()) 
    #    elif weighting=="None":
    #        ridge.fit(X_tr_mod, y_scaled) 
    #    else: raise ValueError("Not a valid data weighting option")
    
    #if force_center:
    #    if model_type=="Polynomial":
    #        pipeline = Pipeline([
    #            ("shift",shift),
    #            ("poly", mod),
    #            ("ridge", ridge)
    #        ])    
    #    elif model_type=="Spline":
    #        pipeline = Pipeline([
    #            ("shift",shift),
    #            ("spline", mod),
    #            ("ridge", ridge)
    #        ])    
    #else:
    if model_type=="Polynomial":
        pipeline = Pipeline([
            ("poly", mod),
            ("ridge", ridge)
        ])    
    elif model_type=="Spline":
        pipeline = Pipeline([
            ("spline", mod),
            ("ridge", ridge)
        ])    
    return pipeline

# return gradient of a scikitlearn ridge model given the polynomial transform and a point in parameter space
def gradient(point, model):
    column_names=point.columns
    # Obtain coefficients and associated names of type string "a^2 b f^3"
    feature_names= model.steps[0][1].get_feature_names_out()
    coefficients = model.steps[1][1].coef_[0]
    
    grad = np.zeros_like(point)[0]
    point = OrderedDict(zip(column_names, point.iloc[0]))
    for i in range(len(point)):
        for j, feature in enumerate(feature_names):
            terms = feature.split(" ")
            print(column_names[i],": ",coefficients[j],terms)
            if any([column_names[i] in term for term in terms]):
                power = sum([int(term.split("^")[-1]) if "^" in term else 1 for term in terms if column_names[i] in term])
                print("deriv factors: ",[point[term.split("^")[0]]**(int(term.split("^")[-1])-1) if "^" in term else 1 for term in terms if column_names[i] in term])
                prod = coefficients[j]*power*np.prod([point[term.split("^")[0]]**(int(term.split("^")[-1])-1) if "^" in term else 1 for term in terms if column_names[i] in term])
                print("not deriv factors: ",[point[term.split("^")[0]]**(int(term.split("^")[-1])) if "^" in term else point[term] for term in terms if not column_names[i] in term])
                prod = prod * np.prod([point[term.split("^")[0]]**(int(term.split("^")[-1])) if "^" in term else point[term] for term in terms if not column_names[i] in term])
                print(grad)
                grad[i]+=prod
    print(pd.DataFrame(grad, index=column_names))   
    print(pd.DataFrame(grad, index=column_names).T)
    return pd.DataFrame(grad, index=column_names).T

def numgradient(point, model, Xscaler, XMMscaler, yscaler, yMMscaler, preset_parameters, force_center,loss_scaled, minstep=0.0001,):
    grad = pd.DataFrame(np.zeros(len(point.columns)), index=point.columns).T
    posgrad = pd.DataFrame(np.zeros(len(point.columns)), index=point.columns).T
    neggrad = pd.DataFrame(np.zeros(len(point.columns)), index=point.columns).T
    point_scaled=pd.DataFrame(Xscaler.transform(point.copy()), columns=point.columns)
    if preset_parameters!=None: point_scaled = point_scaled.drop(columns=list(preset_parameters.keys()))  
    if force_center: 
        centerpoint_scaled=recenter_data(point_scaled,point_scaled)  
        centerpoint_scaled=pd.DataFrame(XMMscaler.transform(centerpoint_scaled.copy()),columns=centerpoint_scaled.columns)
    else:
        centerpoint_scaled=point_scaled.copy()    
    ycenter=scalepredict(model,centerpoint_scaled,force_center,yscaler,yMMscaler,loss_scaled)
    for col_name, value in point.iloc[0].items():
        if preset_parameters!=None and col_name in list(preset_parameters.keys()): continue
        negpoint=point.copy()
        negpoint[col_name]+=-minstep
        pospoint=point.copy()
        pospoint[col_name]+=minstep
        pospoint_scaled=pd.DataFrame(Xscaler.transform(pospoint.copy()), columns=pospoint.columns)
        if preset_parameters!=None: pospoint_scaled = pospoint_scaled.drop(columns=list(preset_parameters.keys()))        
        if force_center: 
            pospoint_scaled=recenter_data(pospoint_scaled,point_scaled)  
            pospoint_scaled=pd.DataFrame(XMMscaler.transform(pospoint_scaled.copy()),columns=pospoint_scaled.columns)
        negpoint_scaled=pd.DataFrame(Xscaler.transform(negpoint.copy()), columns=negpoint.columns)
        if preset_parameters!=None: negpoint_scaled = negpoint_scaled.drop(columns=list(preset_parameters.keys()))
        if force_center: 
            negpoint_scaled=recenter_data(negpoint_scaled,point_scaled)
            negpoint_scaled=pd.DataFrame(XMMscaler.transform(negpoint_scaled.copy()),columns=negpoint_scaled.columns)
        ypos=scalepredict(model,pospoint_scaled,force_center,yscaler,yMMscaler,loss_scaled)
        yneg=scalepredict(model,negpoint_scaled,force_center,yscaler,yMMscaler,loss_scaled)
        deltaY=ypos-yneg
        grad[col_name]+=deltaY/(minstep*2)
        pdeltaY=ypos-ycenter
        posgrad[col_name]+=deltaY/(minstep)
        ndeltaY=ycenter-yneg
        neggrad[col_name]+=deltaY/(minstep*2)
    return grad, posgrad, neggrad
    
def scalepredict(model,newpoint_scaled,force_center,yscaler,yMMscaler,loss_scaled):
    y=pd.DataFrame(model.predict(newpoint_scaled)[0], columns=["Y"])
    if force_center:
        y=pd.DataFrame(yMMscaler.inverse_transform(y.copy()),columns=y.columns)
        y=y+loss_scaled
    y=pd.DataFrame(yscaler.inverse_transform(y.copy()), columns=y.columns)
    return y.iloc[0]["Y"]
    
def evalatdist(dist,direction,startpoint,model,Xscaler,XMMscaler,yscaler,yMMscaler,preset_parameters,force_center,loss_scaled):
    startpoint_scaled=pd.DataFrame(Xscaler.transform(startpoint.copy()), columns=startpoint.columns)
    if preset_parameters!=None: startpoint_scaled = startpoint_scaled.drop(columns=list(preset_parameters.keys()))
    startpoint_original = startpoint_scaled.copy()
    if force_center: 
        startpoint_scaled=recenter_data(startpoint_scaled,startpoint_scaled)
        startpoint_scaled=pd.DataFrame(XMMscaler.transform(startpoint_scaled.copy()),columns=startpoint_scaled.columns)
    y0=scalepredict(model,startpoint_scaled,force_center,yscaler,yMMscaler,loss_scaled)
    step=dist[0]*direction
    newpoint=(startpoint+step).round(4)   
    newpoint_scaled=pd.DataFrame(Xscaler.transform(newpoint.copy()), columns=newpoint.columns)
    if preset_parameters!=None: newpoint_scaled = newpoint_scaled.drop(columns=list(preset_parameters.keys()))
    if force_center: 
        newpoint_scaled=recenter_data(newpoint_scaled,startpoint_original)
        newpoint_scaled=pd.DataFrame(XMMscaler.transform(newpoint_scaled.copy()),columns=newpoint_scaled.columns)
    y1=scalepredict(model,newpoint_scaled,force_center,yscaler,yMMscaler,loss_scaled)
    #print("evaldist: ",dist[0],y,y0,y-y0)
    return y1-y0

def evalprogress(newpoint,startpoint,model,Xscaler,XMMscaler,yscaler,yMMscaler,preset_parameters,force_center,loss_scaled):
    startpoint_scaled=pd.DataFrame(Xscaler.transform(startpoint.copy()), columns=startpoint.columns)
    if preset_parameters!=None: startpoint_scaled = startpoint_scaled.drop(columns=list(preset_parameters.keys()))
    startpoint_original = startpoint_scaled.copy()
    if force_center: 
        startpoint_scaled=recenter_data(startpoint_scaled,startpoint_scaled)
        startpoint_scaled=pd.DataFrame(XMMscaler.transform(startpoint_scaled.copy()),columns=startpoint_scaled.columns)    
    y0=scalepredict(model,startpoint_scaled,force_center,yscaler,yMMscaler,loss_scaled)
    if force_center:
        print("confirm that old loss is predicted correctly: ",y0)
    newpoint_scaled=pd.DataFrame(Xscaler.transform(newpoint.copy()), columns=newpoint.columns)
    if preset_parameters!=None: newpoint_scaled = newpoint_scaled.drop(columns=list(preset_parameters.keys()))
    if force_center: 
        newpoint_scaled=recenter_data(newpoint_scaled,startpoint_original)
        newpoint_scaled=pd.DataFrame(XMMscaler.transform(newpoint_scaled.copy()),columns=newpoint_scaled.columns)
    y1=scalepredict(model,newpoint_scaled,force_center,yscaler,yMMscaler,loss_scaled)
    return y1,y0

def AutoMomentum(last_point, Xscaler, XMMscaler, yscaler, yMMscaler, model, learning_rate, preset_parameters, gradcalc, force_center, loss_scaled):
    # 1. obtain gradient 
    if gradcalc=="Analytic":
        point_scaled = pd.DataFrame(Xscaler.transform(last_point.copy()), columns=last_point.columns)
        if preset_parameters!=None: point_scaled = point_scaled.drop(columns=list(preset_parameters.keys()))
        X_grad_scaled = gradient(point_scaled, model)    
        if preset_parameters!=None: 
            for column in list(preset_parameters.keys()):
                X_grad_scaled[column] = 0.0
            X_grad_scaled = X_grad_scaled[last_point.columns]
        X_grad = X_grad_scaled*Xscaler.scale_
    elif gradcalc=="Numeric":
        X_grad,X_pgrad,X_ngrad =numgradient(last_point, model, Xscaler, XMMscaler, yscaler, yMMscaler, preset_parameters, force_center, loss_scaled)
        #print(X_grad)
    #if preset_parameters!=None: 
    #    X_grad_reduced = X_grad.copy().drop(columns=list(preset_parameters.keys()))
    #    point_reduced = last_point.copy().drop(columns=list(preset_parameters.keys()))
    # 2 find optimal distance to progress along the negative gradient with the set learning rate used as an upper bound
    #for ep in range(20):
    #    dist=10**-ep
    #    negdistres=evalatdist([-dist],X_grad,last_point,model,Xscaler,preset_parameters)
    #    posdistres=evalatdist([dist],X_grad,last_point,model,Xscaler,preset_parameters)
    #    print(dist,negdistres,posdistres,negdistres<posdistres)
    bestdistres=minimize(evalatdist,(0.0),(X_grad,last_point,model,Xscaler,XMMscaler,yscaler,yMMscaler,preset_parameters,force_center,loss_scaled),bounds=[(-learning_rate,learning_rate)],method="Nelder-Mead",options={"maxiter":1e6})
    if bestdistres.success:    
        bestdist=bestdistres["x"][0]
        #print(bestdistres)
        print("best distance found by fit: ",bestdist)
    else:
        print("best distance fit failed, using neg. learning rate ",bestdist)
        bestdist=-learning_rate        
        
    # 2. given momentum calculate next step (while respecting parameter bounds)
    n=0
    while n<100:
        new_momentum = bestdist*X_grad    
        new_point = (last_point + new_momentum).round(4)   
        isinbounds=True
        for col_name, value in new_point.iloc[0].items():        
            if value < 0.0001:
                print("Parameter ",col_name," with value ",value," is out of bounds, trying to fix by taking half step size")                
                new_point[col_name]=0.0001
                isinbounds=False
        if not isinbounds:
            bestdist=bestdist*0.5
            n=n+1
            continue
        newloss,oldloss=evalprogress(new_point,last_point,model,Xscaler,XMMscaler,yscaler,yMMscaler,preset_parameters,force_center,loss_scaled)
        if newloss>oldloss:
            print("predicted loss at new point ",newloss," higher than at old point ",oldloss," , trying to fix by taking half step size")
            bestdist=bestdist*0.5
            n=n+1
        elif newloss<oldloss*0.5:
            print("predicted loss at new point ",newloss," less than 1/2 of ",oldloss," , unrealistic improvement, taking half step size")
            bestdist=bestdist*0.5
            n=n+1
        elif newloss==oldloss:
            print("predicted loss at new point ",newloss," equals loss at old point ",oldloss," (points merged) increasing step size by 50%")
            bestdist=bestdist*1.5            
        else:            
            print("predicted loss at new point ",newloss," is lower than at old point ",oldloss," , and all parameters in range -> using new point")
            break
    
    if n==100:
        print("number of adjustments has reached 100, taking last distance proposal") 
    newloss,oldloss=evalprogress(new_point,last_point,model,Xscaler,XMMscaler,yscaler,yMMscaler,preset_parameters,force_center,loss_scaled)
    
    
    new_momentum = (new_point-last_point).round(4)
        
    
    if preset_parameters!=None: 
        for column, value in preset_parameters.items():
            new_point[column] = round(max(0.0001,float(value)), 4)
            new_momentum[column] = 0.0
    return new_point, new_momentum, X_grad


def NesterovMomentum(last_point, last_momentum, Xscaler, model, momentum_decay, learning_rate, preset_parameters, gradcalc):
    # 1. obtain gradient from Nesterov momentum + rescale
    if gradcalc=="Analytic":
        point_scaled = pd.DataFrame(Xscaler.transform(last_point.copy()), columns=last_point.columns)
        momentum_scaled = last_momentum.copy()/Xscaler.scale_
        point_lookahead = point_scaled + momentum_scaled
        if preset_parameters!=None: point_lookahead = point_lookahead.drop(columns=list(preset_parameters.keys()))
        X_grad_scaled = gradient(point_lookahead, model)
        if preset_parameters!=None: 
            for column in list(preset_parameters.keys()):
                X_grad_scaled[column] = 0.0
            X_grad_scaled = X_grad_scaled[last_point.columns]
        X_grad = X_grad_scaled*Xscaler.scale_
    elif gradcalc=="Numeric":
        X_grad,X_pgrad,X_ngrad =numgradient(last_point, model, Xscaler, XMMscaler, yscaler, yMMscaler, preset_parameters, force_center, loss_scaled)
        print(X_grad)
    
    # 2. given momentum calculate next step (while respecting parameter bounds)
    new_momentum = momentum_decay*last_momentum - learning_rate*X_grad
    new_point = (last_point + new_momentum).round(4)
    for col_name, value in new_point.iloc[0].items():
        if value < 0.0001: new_point[col_name]=0.0001
    new_momentum = (new_point-last_point).round(4)
    
    if preset_parameters!=None: 
        for column, value in preset_parameters.items():
            new_point[column] = round(max(0.0001,float(value)), 4)
            new_momentum[column] = 0.0
    
    return new_point, new_momentum, X_grad

def NormalMomentum(last_point, last_momentum, Xscaler, XMMscaler, yscaler, yMMscaler, model, momentum_decay, learning_rate, preset_parameters, gradcalc, force_center, loss_scaled):
    # 1. obtain gradient
    if gradcalc=="Analytic":
        point_scaled = pd.DataFrame(Xscaler.transform(last_point.copy()), columns=last_point.columns)
        if preset_parameters!=None: point_scaled = point_scaled.drop(columns=list(preset_parameters.keys()))
        X_grad_scaled = gradient(point_scaled, model)
        if preset_parameters!=None: 
            for column in list(preset_parameters.keys()):
                X_grad_scaled[column] = 0.0
            X_grad_scaled = X_grad_scaled[last_point.columns]
        X_grad = X_grad_scaled*Xscaler.scale_
    elif gradcalc=="Numeric":
        X_grad,X_pgrad,X_ngrad =numgradient(last_point, model, Xscaler, XMMscaler, yscaler, yMMscaler, preset_parameters, force_center, loss_scaled)        
    # 2. given momentum calculate next step (while respecting parameter bounds)
    new_momentum = momentum_decay*last_momentum - learning_rate*X_grad
    new_point = (last_point + new_momentum).round(4)
    for col_name, value in new_point.iloc[0].items():
        if value < 0.0001: new_point[col_name]=0.0001
    new_momentum = (new_point-last_point).round(4)
    
    if preset_parameters!=None: 
        for column, value in preset_parameters.items():
            new_point[column] =  round(max(0.0001,float(value)), 4)
            new_momentum[column] = 0.0
    print(last_point)
    print(new_point)
    return new_point, new_momentum, X_grad
    
def failed_gradientStep(point_list, momentum_list, loss_list):
    # Take last point where simulation has not failed/was not infinity, and half the step size of the previous simulation that failed
    last_noninf_index = None
    for i in range(len(loss_list)-1, -1, -1):
        if loss_list[i] != np.inf:
            last_noninf_index = i
            break
    point = point_list[last_noninf_index].copy()
    momentum = momentum_list[-1].copy()*0.5
    new_point = (point + momentum).round(4)
    for col_name, value in new_point.iloc[0].items():
        if value < 0.0001: new_point[col_name]=0.0001
    new_momentum = (new_point-point).round(4)
    return new_point, new_momentum

def gradientStep(point_list, momentum_list, loss_list, gradient_list, X_scaled, y_scaled, w_data, Xscaler, yscaler, settings, simulation_infnan, preset_parameters):
    logging.info("\n")
    logging.info("-"*20+"Calculating gradient descent step and new point"+"-"*20)    
    if not simulation_infnan:
        point = point_list[-1].copy()
        point_scaled = pd.DataFrame(Xscaler.transform(point), columns=point.columns)
        #print("point: ",point)
        #print("point scaled: ",point_scaled)
        #print("point rescaled: ",pd.DataFrame(Xscaler.inverse_transform(point_scaled), columns=point.columns))
        loss=pd.DataFrame([loss_list[-1]],columns=y_scaled.columns)
        loss_scaled = pd.DataFrame(yscaler.transform(loss.copy()), columns=loss.columns)
        momentum = momentum_list[-1].copy()
        #print("loss: ",loss)
        #print("loss scaled: ",loss_scaled)
        #print("loss rescaled: ",pd.DataFrame(yscaler.inverse_transform(loss_scaled.copy()), columns=loss.columns))
        
        # a. Select points to which the ridge model is fitted
        if settings["n_closest_points"] == "Global": closest_X_scaled, closest_y_scaled, closest_w_data = X_scaled.copy(), y_scaled.copy(), w_data.copy()
        elif settings["n_closest_points"] == "Auto": closest_X_scaled, closest_y_scaled, closest_w_data = closest_points(X_scaled, y_scaled, w_data, point_scaled, int(settings["npoints"])) 
        else: closest_X_scaled, closest_y_scaled, closest_w_data = closest_points(X_scaled, y_scaled, w_data, point_scaled, int(settings["n_closest_points"]))
        
        # b. Fit weighted model to point
        if preset_parameters!=None:
            presence = [item in closest_X_scaled.columns for item in list(preset_parameters.keys())]
            for i, present in enumerate(presence):
                if not present: logging.warning(f"There is no parameter {list(preset_parameters.keys())[i]} in data which could be preset!")
            closest_X_scaled = closest_X_scaled.drop(columns=list(preset_parameters.keys()))
            point_reduced = point_scaled.drop(columns=list(preset_parameters.keys()))
        else:
            point_reduced=point_scaled
            
        if settings["force_center"]:
            print("force_center: shifting X and y so that intercept is (0,0)")        
            X_shifted=recenter_data(closest_X_scaled,point_reduced)
            XMMscaler=MaxAbsScaler().fit(X_shifted)
            X_shifted=pd.DataFrame(XMMscaler.transform(X_shifted.copy()),columns=X_shifted.columns)
            y_shifted=recenter_data(closest_y_scaled,loss_scaled)
            yMMscaler=MaxAbsScaler().fit(y_shifted)
            y_shifted=pd.DataFrame(yMMscaler.transform(y_shifted.copy()),columns=y_shifted.columns)
        else:
            X_shifted,y_shifted=closest_X_scaled, closest_y_scaled   
        
        if settings["weighting"]=="Exponential":
            weights = get_expweights(y_scaled) * closest_w_data  
            print("obtained exponential weights")
        elif settings["weighting"]=="Distance":        
            weights = get_distweights(closest_X_scaled,point_reduced,int(settings["dist_weight_power"])) * closest_w_data        
            print("obtained distance weights")
        elif settings["weighting"]=="None":
            weights=closest_w_data
        else: raise ValueError("Not a valid weighting method for fitting")    
        
        
        model = createRidgeModel(X_shifted, y_shifted, int(settings["degree"]), settings["alpha"],point_reduced,loss_scaled,int(settings["dist_weight_power"]),settings["model_type"],int(settings["knots"]),settings["force_center"],weights)
        print("ridge model created")
        # c. Obtain new point from given momentum method
        if settings["momentum_type"] == "Nesterov": new_point, new_momentum, new_gradient = NesterovMomentum(point, momentum, Xscaler, model, settings["momentum_decay"], settings["learning_rate"], preset_parameters, settings["gradient_calc"])
        if settings["momentum_type"] == "Normal": new_point, new_momentum, new_gradient = NormalMomentum(point, momentum, Xscaler, XMMscaler, yscaler, yMMscaler, model, settings["momentum_decay"], settings["learning_rate"], preset_parameters, settings["gradient_calc"], settings["force_center"], loss_scaled)
        if settings["momentum_type"] == "Auto": new_point, new_momentum, new_gradient = AutoMomentum(point, Xscaler, XMMscaler, yscaler, yMMscaler, model, settings["learning_rate"], preset_parameters, settings["gradient_calc"], settings["force_center"], loss_scaled)
        print("calculated momentum")
    else: # d. If simulation is inf/nan then take last working point with half of previous tried momentum step instead
        new_point, new_momentum = failed_gradientStep(point_list, momentum_list, loss_list)
        new_gradient = gradient_list[-1]
      
    point_list.append(new_point)
    momentum_list.append(new_momentum)
    gradient_list.append(new_gradient)
    logging.info(f"New Point:\n{new_point.iloc[0]}")
    logging.info(f"New Momentum:\n{new_momentum.iloc[0]}")
    logging.info(f"Gradient At Old Point:\n{new_gradient.iloc[0]}")

# %% [markdown]
# ### Submit Task To Computer

# %%
def submit_task(point, dragonbkg_path, IP):
    logging.info("\n")
    logging.info("-"*20+"Submitting new point to simulation"+"-"*20)

    dragonbkg_folder = os.path.dirname(dragonbkg_path)
    dragonbkg_name = os.path.basename(dragonbkg_path)
    os.chdir(dragonbkg_folder)
    command = "./"+dragonbkg_name+" $DP " + str(IP)
    logging.info("submission command: "+command)
    param_dict={"indxscan":"sindex","ncut":"nuccut","deltscan":"diffexp","lowindex":"lowindx","lowdelt":"lowexp","lowdeltbreak":"lowdiffbreak",
                "lowdbreaksoft":"lowdiffbreaksoft","Dscan":"diffnorm", "diffscaleheight":"DE","diffscaleradius":"DR","reaccscan":"alvel",
                "highdelt":"highexp","deltbreak":"diffbreak","dbreaksoft":"diffbreaksoft","lowbreak":"lowbreak","lowsoft":"lowsoft","SW":"spiralwidth","convel":"convel"}
    marker = "#Autoconfigblock"

    for _, row in point.iterrows():
        # parse the parameters saved in point into the dragonbkg format
        new_params = "\n"
        for key, value in param_dict.items():
            if value not in row.keys():
                continue
            par = row[value]
            if par<0.0001: par = 0.0001
            if key in ["deltscan","Dscan","reaccscan","indxscan"]: new_params+=f"{key}=[{par:.4f}]\n"
            else: new_params+=f"{key}={par:.4f}\n"
            
        # change parameters in dragonbkg file   
        with open(dragonbkg_name, "r") as file:
            content = file.read()
        start_index = content.find(marker)
        end_index = content.find(marker, start_index + len(marker))
        if start_index != -1 and end_index != -1:
            new_content = content[:start_index+len(marker)] + new_params + content[end_index:]
            with open(dragonbkg_name, "w") as file:
                file.write(new_content)
                
        # execute dragonbkg
            with subprocess.Popen(command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1, universal_newlines=True) as process:
                while True:
                    start_time = time.time()                    # To check whether we are caught in a loop
                    output = process.stdout.readline().strip()  # IMPORTANT: in dragonbkg's "input('text')" prompts end all the lines with 'text\n', otherwise readline() cannnot read the input prompt and we wait forever!!!
                    if type(output)!=str: output = output.decode()
                    if output: 
                        start_time=time.time()
                        logging.info(f"{output}")
                        if any(content in output for content in ["copy to remote PC", "add to execution list", "overwrite the file"]):
                            process.stdin.write("y\n")
                            process.stdin.flush()
                            logging.info("y")
                    if output == "" and process.poll() is not None: break
                    if time.time() - start_time > 300: raise TimeoutError("No processable communication for > 5 minutes. Terminated simulation fitting!")

# %% [markdown]
# ### Main

# %%
def main(overwrite_args=None):
    # Initializing Variables
    # 0. Load settings from "config.yaml" file in same folder as this script and potentially overwrite parameters
    GD_settings, preset_parameters, comp_settings, paths = load_config()
    
    if overwrite_args!=None: 
        GD_settings = overwrite_args["GD_settings"]
        preset_parameters = overwrite_args["preset_parameters"]
        comp_settings = overwrite_args["comp_settings"]
        paths = overwrite_args["paths"]
    
    save_folder = generate_saveFolderName(paths["progress_dir"], comp_settings, GD_settings)
    logging.basicConfig(
        level = logging.DEBUG,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        filename = os.path.join(save_folder, "output.log")
    )
    logging.info(preset_parameters)
    logging.info(comp_settings)
    
    point_list = []
    momentum_list = []
    gradient_list = []
    loss_list = []

    current_steps = 0           # Counter for how many descent steps have been taken
    current_nfiles = 0          # To check whether new dataload is necessary
    initialization = True       # During first loop load initial data


    while True:    
        
        print("Update and fit potentially new datapoints                                                        ",end = '\r', flush=True)
        new_nfiles=update_data(paths["fitSpectra_path"])
        if new_nfiles==None: new_nfiles=current_nfiles
        logging.info(f"new_nfiles: {new_nfiles}")
        logging.info(f"current_nfiles: {current_nfiles}")
        
        print("Load newest data if there were new files                                                         ",end = '\r', flush=True)
        if (new_nfiles > current_nfiles) or initialization: 
            current_nfiles = new_nfiles
            X_data, y_data, X_scaled, y_scaled, Xscaler, yscaler, w_data, isinterpol , X_fault = load_data(paths["dragondata_path"],paths["interpoldata_path"], GD_settings=GD_settings, preset_parameters=preset_parameters)        
        print("When first starting script either load previous data or take current best point as starting point",end = '\r', flush=True)
        if initialization:
            initialization=False
            if comp_settings["load_previous"]==True: point_list, momentum_list, loss_list, gradient_list = load_previous_descentData(save_folder)
            elif GD_settings["start_point"]=="Best": point_list, momentum_list, loss_list = get_best_point(X_data, y_data, isinterpol)
            elif GD_settings["start_point"]=="Random": point_list, momentum_list, loss_list = get_random_point(X_data, y_data, isinterpol)
            elif GD_settings["start_point"]=="Farthest": point_list, momentum_list, loss_list = get_farthest_point(X_data, y_data, X_scaled, isinterpol)
            elif GD_settings["start_point"]=="FarGood": point_list, momentum_list, loss_list = get_farthest_point(X_data, y_data, X_scaled, isinterpol,float(np.median(y_data)))
            simulation_finished = True
            simulation_infnan = False
        else:   
            print("Check if previous task has finished successfully or with inf output                              ",end = '\r', flush=True)
            simulation_finished, simulation_infnan = checkSimulationProgress(X_data, y_data, X_fault, point_list, loss_list, isinterpol)
    
        if simulation_finished:
            print("Loss of last calculated point: ",loss_list[-1],"                                                 ")
            if current_steps+1>comp_settings["max_gradient_steps"]: 
                if comp_settings["autorestart"]:
                    initialization=True  
                    current_steps = 0           
                    current_nfiles = 0
                    continue
                    print("Gradient descent run completed, restarting")
                else:
                    print("Gradient descent run completed, exiting program")
                sys.exit(0)
            current_steps+=1
            
            print("Calculate best fit hyperparameters if fit_mode is Auto                                           ",end = '\r', flush=True)
            if GD_settings["fit_mode"]=="Auto" and not simulation_infnan: determine_hyperparams(X_scaled, y_scaled, w_data, point_list, loss_list, Xscaler, yscaler, GD_settings, preset_parameters)
            
            print("Calculate next descent step                                                                      ",end = '\r', flush=True)
            gradientStep(point_list, momentum_list, loss_list, gradient_list, X_scaled, y_scaled, w_data, Xscaler, yscaler, GD_settings, simulation_infnan, preset_parameters)    
            
            if int(comp_settings["simulation_IP"])==0:
                print("Test run complete - IP is 0, exit")
                sys.exit(0)
                
            if not checkPointAlreadyCalculated(point_list[-1], X_data, X_fault, isinterpol):                        
                print("Step: %d/%d -- Submit new point to simulation"%(current_steps,comp_settings["max_gradient_steps"]))
                submit_task(point_list[-1], paths["dragonbkg_path"], int(comp_settings["simulation_IP"]))
            else:
                print("Step: %d/%d -- Point already calculated "%(current_steps,comp_settings["max_gradient_steps"]))
                point_list.pop(-1)
                momentum_list.pop(-1)
                gradient_list.pop(-1)
                continue
            print("Save current progress to savefile                                                                ",end = '\r', flush=True)
            save_current_data(point_list, momentum_list, loss_list, gradient_list, save_folder) 
        
        nw=0
        while nw<300:
            print("Waiting for tasks to finish %d/300s                                                              "%(nw),end = '\r', flush=True)
            time.sleep(1)
            nw=nw+1
        # wait 5 minutes until next check of whether a task has finished


if __name__=="__main__": 
    try: 
        json_data = sys.argv[1]
        data = json.loads(json_data)
    except:
        data=None
    main(data)
