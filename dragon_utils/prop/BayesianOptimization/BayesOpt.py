# %%
### Imports
import numpy as np
import pandas as pd

from sklearn.metrics import mean_squared_error
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C
from skopt.plots import plot_evaluations, plot_objective
from skopt.space import Real, Integer, Space
from skopt.plots import plot_convergence
from skopt import gp_minimize
from sklearn.preprocessing import StandardScaler
from scipy.spatial import KDTree

import re
import os
import sys
import joblib
from collections import OrderedDict
import pickle
from datetime import datetime
import subprocess
import time
import logging
import getpass
import random
import yaml

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
def submit_task(point, dragonbkg_path, IP, preset_parameters):
    logging.info("\n")
    logging.info("-"*20+"Submitting new point to simulation"+"-"*20)

    dragonbkg_folder = os.path.dirname(dragonbkg_path)
    dragonbkg_name = os.path.basename(dragonbkg_path)
    os.chdir(dragonbkg_folder)
    command = "./"+dragonbkg_name+" $DP " + str(IP)
    param_dict={"indxscan":"sindex","ncut":"nuccut","deltscan":"diffexp","lowindex":"lowindx","lowdelt":"lowexp","lowdeltbreak":"lowdiffbreak",
                "lowdbreaksoft":"lowdiffbreaksoft","Dscan":"diffnorm", "diffscaleheight":"DE","diffscaleradius":"DR","reaccscan":"alvel",
                "highdelt":"highexp","deltbreak":"diffbreak","dbreaksoft":"diffbreaksoft","lowbreak":"lowbreak","lowsoft":"lowsoft","SW":"spiralwidth","convel":"convel"}
    marker = "#Autoconfigblock"

    for _, row in point.iterrows():
        # parse the parameters saved in point into the dragonbkg format
        new_params = "\n"
        for key, value in param_dict.items():
            if value not in row.keys():
                if value in preset_parameters.keys():
                    par = preset_parameters[value] 
                else:
                    continue
            else:
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
def obj_func(parameters, point_list, loss_list, Xscaler, computerIP, paths, cur_files, bounds, save_folder, init_X, init_y, bayes_settings, preset_parameters):
    parameters = Xscaler.inverse_transform([parameters])[0].round(4)
    point_list.append(pd.DataFrame(parameters).T)
    point_list[-1].columns=init_X.columns
    logging.info(f"New parameters:\n{point_list[-1]}")
    
    submit_task(point_list[-1], paths["dragonbkg_path"], computerIP, preset_parameters)
    
    while(True):
        simulation_finished, simulation_infnan = False, False
        
        new_nfiles=update_data(paths["fitSpectra_path"])
        
        if (new_nfiles > cur_files): 
            current_nfiles = new_nfiles
            X_data, y_data, X_scaled, y_scaled, Xscaler, yscaler, X_fault, maxloss = load_data(paths["dragondata_path"],bayes_settings,preset_parameters)
          
            simulation_finished, simulation_infnan = checkSimulationProgress(X_data, y_data, X_fault, point_list, loss_list, maxloss)
        
        if simulation_finished:
            save_current_data(init_X, init_y, point_list, loss_list, bounds, save_folder)
            # if not simulation_infnan: return yscaler.transform(loss_list[-1])
            if not simulation_infnan:
                print("simulation completed, loss parameter: ",loss_list[-1])
                if loss_list[-1]>maxloss:
                     print("loss > maxloss, replaced with maxloss")
                     loss_list[-1]=maxloss
                     return maxloss
                else:
                    return loss_list[-1]
            else:
                print("simulation completed, but fit to data returned inf or nan")
                return maxloss
        
        # loss_list.append(1)
        # return 1  
        
        time.sleep(600)

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
    # Initializing Variables
    # 0. Load settings from "config.yaml" file in same folder as this script and potentially overwrite parameters
    bayes_settings, preset_parameters, comp_settings, paths = load_config()
    
    save_folder = generate_saveFolderName(paths["progress_dir"], comp_settings["load_previous"], bayes_settings)
    logging.basicConfig(
        level = logging.DEBUG,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        filename = os.path.join(save_folder, "output.log")
    )
    logging.info(bayes_settings)
    logging.info(comp_settings)
    
    point_list = []
    loss_list = []
    bounds = []

    print("Update and fit potentially new datapoints                                                                ",end = '\r', flush=True)
    new_nfiles=update_data(paths["fitSpectra_path"])
    
    print("Load newest data                                                                                         ",end = '\r', flush=True)
    X_data, y_data, X_scaled, y_scaled, Xscaler, yscaler, X_fault, maxloss = load_data(paths["dragondata_path"],bayes_settings,preset_parameters)

    print("Load closest points                                                                                      ",end = '\r', flush=True)
    
    
    if bayes_settings["start_point"]=="Best":
        start_X, start_y = top_results(X_data, y_data, 1)
    elif bayes_settings["start_point"]=="FarGood":
        medloss=float(np.median(y_data))    
        start_X, start_y = get_farthest_point(X_data, y_data, X_scaled, medloss)
        
    if bayes_settings["n_closest_points"]=="Global": nX, ny = X_data, y_data
    else: nX, ny = closest_points(X_data, y_data, start_X, int(bayes_settings["n_closest_points"]))
    
    print("Determine parameter bounds for later optimization (grown such that volume increased by factor)           ",end = '\r', flush=True)
    bounds, bounds_scaled = determine_bounds(nX, Xscaler, float(bayes_settings["volume_factor"]))
    
    print("Extract all values within bounds grown double of volume factor (to already get info outside of box)      ",end = '\r', flush=True)
    bX, by = get_pointsInBounds(bounds, X_data, y_data)
    x0 = pd.DataFrame(Xscaler.transform(bX), columns=X_data.columns).values.tolist()
    # y0 = pd.DataFrame(yscaler.transform(ny), columns=y_data.columns)[y_data.columns[0]].tolist()
    y0 = by[y_data.columns[0]].tolist()
    
    print("Run bayesian optimization                                                                                ",end = '\r', flush=True)
    n_jobs = os.cpu_count()-1
    res = gp_minimize(
                    func = lambda params: obj_func(
                                            parameters=params, 
                                            point_list=point_list, 
                                            loss_list=loss_list, 
                                            Xscaler=Xscaler,
                                            computerIP=int(comp_settings["simulation_IP"]),
                                            paths = paths, 
                                            cur_files=new_nfiles,
                                            bounds = bounds,
                                            save_folder = save_folder,
                                            init_X = bX,
                                            init_y = by,
                                            bayes_settings=bayes_settings,
                                            preset_parameters=preset_parameters
                                            ),
                    dimensions = bounds_scaled,                 # List of search space dimensions
                    # base_estimator = gpe,                     # Gaussian process estimator to use for optimization
                    n_calls = int(bayes_settings["n_calls"]),   # Budget: number of calls to func
                    n_initial_points=0,                         # Number of evaluations of func with initialization points
                    # initial_point_generator = "lhs",          # Sets a initial points generator  
                    acq_func = "EI",                            # Function to minimize over the gaussian prior
                    x0 = x0,                                    # Initial input points
                    y0 = y0,                                    # Evaluation of initial input points
                    verbose = 1,                  
                    kappa = 1.96,                               # Controls how much of the variance in the predicted values should be taken into account
                    xi = 0.001,                                 # Controls how much improvement one wants over the previous best values
                    noise = 10**-10,                            # Expected noise in output
                    n_jobs=n_jobs
                    )

    save_current_data(bX, by, point_list, loss_list, bounds, save_folder) 

if __name__ == "__main__":
    main()
