# %%
### Imports
import math
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
from sklearn.model_selection import train_test_split


import multiprocessing
import subprocess


import re
import os
import sys
import joblib
from collections import OrderedDict
import pickle
from datetime import datetime
import time
import logging
import io
import getpass
import random
import yaml

sys.path.append('../common')
from datafunc import update_data

def mute():
    sys.stdout = open(os.devnull, 'w')

def load_data(dragon_datapath,settings,preset_parameters):
    logging.info("\n")
    logging.info("-"*20+"Loading and processing new data"+"-"*20)

    # 1. Load data and save in pd.DataFrame
    data_loaded = False
    while not data_loaded:
        try:
            with open(dragon_datapath, "rb") as file:
                hashdict,foundfiles,globpardict,pflxs,pfs,x2s,x2dict,vx2s,vx2dict,rx2s,rx2dict,px2s,px2dict,hx2s,hx2dict,fx2s,fx2dict,qx2s,qx2dict,vfx2s,vfx2dict,likes,likedict,mlikes,mlikedict,tlikes,tlikedict,qlikes,qlikedict,slikes,slikedict,mx2s,mx2dict,sx2s,sx2dict,cx2s,cx2dict,clikes,clikedict,tss,tsdict,faultfiles,faultpardict,corrfactlist = pickle.load(file)
                lossparamdict={"x":x2s,"v":vx2s,"r":rx2s,"p":px2s,"h":hx2s,"f":fx2s,"q":qx2s,"vf":vfx2s,"l":likes,"ml":mlikes,"tl":tlikes,"ql":qlikes,"sl":slikes,"m":mx2s,"s":sx2s,"c":cx2s,"cl":clikes}
                globpardict["Y"]=lossparamdict[settings["lossparameter"]]
                hashs=[]
                for ff in foundfiles:
                    hashs.append(hashdict[ff])
                globpardict["hash"]=hashs
                data = pd.DataFrame.from_dict(globpardict)
                faultdata = pd.DataFrame.from_dict(faultpardict)
            data_loaded = True
        except Exception as e:
            logging.warning(f"Error occured: {e}")
            logging.info("Two runs might be trying to access data simultaneously. Waiting before trying again.")
            time.sleep(random.randint(0, 300)) 

    logging.info(f"Total simulations loaded: {len(data)+len(faultdata)}")
    logging.info(f"Number failed simulations: {len(faultfiles)}")


    # 2. Process data by replacing nans and infs with maximum finite likelihood or removing them  
    init_len = len(data)    
    if settings["infliketreatment"]=="replace":
        if settings["maxloss"]=="maxval":
            maxloss=data.loc[data["Y"]!=np.inf, "Y"].max()
            #logging.info("maxloss set to : ",maxloss)
        elif settings["maxloss"]=="default":            
            if "l" in settings["lossparameter"]:
                maxloss=-np.log(sys.float_info.min)
            else:
                maxloss=sys.float_info.max**0.1
        else:
            maxloss=int(settings["maxloss"]) 
        data.replace([np.inf, -np.inf], maxloss, inplace=True)    
        faultreplace=faultdata.copy()
        faultreplace["Y"]=[maxloss]*len(faultdata)
        data = pd.concat([data, faultreplace], ignore_index=True, axis=0).reset_index(drop=True)
        data = data.dropna().reset_index(drop=True)
        post_len = len(data)
    elif settings["infliketreatment"]=="remove":
        maxloss=np.inf
        data.replace([np.inf, -np.inf], np.nan, inplace=True)
        faultdata = pd.concat([faultdata, data[data.isna().any(axis=1)].copy()], ignore_index=True, axis=0).drop(columns=["Y","hash"]).reset_index(drop=True)
        ###### Improvement possibility: handle inf/nan/fails differently by assigning high neg. log-likelihood ######
        data = data.dropna().reset_index(drop=True)
        post_len = len(data)    
        logging.info(f"Number inf/nan simulations: {(init_len-post_len)}")
    logging.info(f"Final selected simulations: {post_len}")
    logging.info(f"Best neg. log-likelihood: { np.min(data['Y']) }")

     # 3. Filter data for preset parameters and drop preset parameter columns
        
    if preset_parameters!=None:
        beforefilterlen=len(data)
        logging.info(f"Simulations before preset parameters filter: {beforefilterlen}")
        data = filter_data(data, preset_parameters)
        afterfilterlen=len(data)
        logging.info(f"Simulations after preset parameters filter: {afterfilterlen}")
        data = data.drop(columns=list(preset_parameters.keys()))
        faultdata = faultdata.drop(columns=list(preset_parameters.keys()))
    
    y_data = data[["Y"]].copy()
    hash_data = data[["hash"]].copy()
    X_data = data.copy().drop(columns=[y_data.columns[0],hash_data.columns[0]])
    
    # 4. Fitting scalers to standardize data    
    Xscaler= StandardScaler()
    yscaler = StandardScaler()
    X_scaled = pd.DataFrame(Xscaler.fit_transform(X_data.copy()), columns=X_data.columns)
    y_scaled = pd.DataFrame(yscaler.fit_transform(y_data.copy()), columns=y_data.columns)
    
    #logging.info("Lengths of X, y, sX, sy:")
    #logging.info(len(X_data), len(y_data), len(X_scaled), len(y_scaled))
    return X_data, y_data, X_scaled, y_scaled, Xscaler, yscaler, faultdata, hash_data, maxloss

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
    return top_X, top_y.values[0].item()

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
    
def filter_data(X, preset_parameters):
    X_filt = X.copy().reset_index(drop=True)
    for col_name,value in  preset_parameters.items():
        dropindx=X_filt.index[X_filt[col_name]!=value]
        X_filt.drop(dropindx,inplace=True)
    filtered_X = X_filt.reset_index(drop=True)
    return filtered_X

def get_distances(X_scaled,point):
    X_der = X_scaled.copy().reset_index(drop=True)
    point_der = point.copy().iloc[0]
    distances = np.linalg.norm(X_der-point_der, axis=1)
    return pd.DataFrame(distances,columns=["Distance"])
    
def get_farthest_point(X, y, sX, maxloss=False):
    bp, bl = top_results(sX, y, 1)
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
    #logging.info("len min max distances:",len(distances),min(distances),max(distances))
    far_indx = np.argsort(distances)[-1:]
    far_y = y_der.loc[far_indx].reset_index(drop=True)
    far_X = X_der.loc[far_indx].reset_index(drop=True)
    if maxloss:
        logging.info(f"distance of farthest point with loss {far_y.values[0].item()} being less than {maxloss} : {distances[far_indx[0]]}")
    else:
        logging.info(f"distance of farthest point {distances[far_indx[0]]}")
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
                        logging.debug(f"{output}")
                        if any(content in output for content in ["copy to remote PC", "add to execution list", "overwrite the file"]):
                            process.stdin.write("y\n")
                            process.stdin.flush()
                            logging.debug("y")
                    if output == "" and process.poll() is not None: break
                    if time.time() - start_time > 300: raise TimeoutError("No processable communication for > 5 minutes. Terminated simulation fitting!")


# %%
def load_previous_data(folder):
    highest_file, _ = highest_fileandID(folder)
    if highest_file==None: 
        raise FileNotFoundError("There are no saved in the given folder files!")
    else:
        with open(os.path.join(folder, highest_file), "rb") as file:
            save_data = pickle.load(file)
            points = save_data["points"]
            losses = save_data["losses"]
    return points, losses

def save_current_data(X, y, points, losses, bounds, folder):
    with open(os.path.join(folder, "data.pkl"), "wb") as file:
        save_data = {"points": points, "losses": losses, "init_X": X, "init_y": y}
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
    except: script_dir = f"/home/{getpass.getuser()}/CALETana/prop/MarkovChain"
    with open(os.path.join(script_dir, "config.yaml"), "r") as file:
        config = yaml.safe_load(file)
    MC_settings = config["MC_settings"]
    preset_parameters = config["preset_parameters"]
    comp_settings = config["comp_settings"]
    NN_settings = config["NN_settings"]
    paths = config["paths"]
    return MC_settings, preset_parameters, comp_settings, NN_settings, paths

# %%
def generate_saveFolderName(paths, load_previous, settings):
    path=paths["progress_dir"]
    folder_prefix = get_folderPrefix(settings)+"-"+paths["fitmode"]
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
    prefix = f"{s['lossparameter']}"
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


def getstringfromdict(dic):
    string=""
    for k,v in dic.items():
        string=string+k+str(v)
    return string.replace(".","d")

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

def likepredict(X_scaled, y_scaled, preset_parameters, ANN_save_folder, losspar, hyperparams, multitrain=False, ngpu=0):    
    logging.info("\n")
    logging.info("-"*20+"Starting ANN training "+"-"*20)    
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers
    start_time = time.time()
    hyperparstr=getstringfromdict(hyperparams)        
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y_scaled, test_size=0.1)

    nfeature=len(X_train.columns)
    npoints=len(y_train)
    lsf=hyperparams["LSF"]
    nepoch=hyperparams["NEP"]
    n_processlayers=hyperparams["NCL"]
    batchsplit=hyperparams["BSP"]
    layerscale=max(int(npoints*lsf),nfeature)
    gpus=tf.config.list_physical_devices('GPU')    
    tf.config.set_visible_devices(gpus[ngpu], 'GPU')
    tf.config.experimental.set_memory_growth(gpus[ngpu], True)
    logical_devices = tf.config.list_logical_devices('GPU')    
    assert len(logical_devices)==1
    with tf.device(logical_devices[0]):
        logging.info(f"used GPU: {gpus[ngpu]} device: {logical_devices[0]}")
        input_layer = layers.Input(shape=(nfeature,))
        scale_layer = layers.Dense(units = nfeature, activation = "linear")(input_layer)
        processlayers=[scale_layer]
        for nl in range(n_processlayers):
            processlayers.append(layers.Dense(units = layerscale, activation = hyperparams["ACF"])(processlayers[nl]))
            #logging.info("adding common processing layer ",nl," with ",layerscale," units")       
        y_output = layers.Dense(units = 1, activation = "linear", name = "y_output")(processlayers[-1])
    
        model = keras.Model(inputs = input_layer, outputs = [y_output])
        
        optimizer = keras.optimizers.Nadam()
        #lr_schedule = keras.optimizers.schedules.ExponentialDecay(initial_learning_rate=0.1,decay_steps=100,decay_rate=0.95)
        #optimizer = keras.optimizers.SGD(learning_rate=lr_schedule)
        #optimizer = keras.optimizers.RMSprop(learning_rate=lr_schedule)
        #optimizer = keras.optimizers.Lion(learning_rate=lr_schedule)

        model.compile(optimizer = optimizer,loss = {'y_output':keras.losses.MeanSquaredError(name="train_error")},metrics = {'y_output':tf.keras.metrics.MeanAbsoluteError(name="error")})
        #model.compile(optimizer = optimizer,loss = {'y1_output':keras.losses.MeanAbsoluteError()},metrics = {'y1_output':tf.keras.metrics.MeanAbsolutePercentageError()})
        
        #plot_model(model, show_shapes = True)
        #training process
        trainhist=model.fit(X_train, y_train, epochs = nepoch, batch_size = int(npoints/batchsplit)+1 ,validation_data = (X_test, y_test), verbose = 0)     
        history=trainhist.history        
        if multitrain:
            multitstr="-%d"%multitrain
        else:
            multitstr=""
        modelsavefile=ANN_save_folder+"/ANN_like_%s_%s%s.keras"%(losspar,hyperparstr,multitstr)
        model.save(modelsavefile) 
        logging.info(f"ANN training completed, saved file {modelsavefile}")
        del model        
    return

def randomStep(point_list, startpointindex, Xscaler, yscaler, X_scaled, MC_settings, NN_settings, paths):
    logging.info("\n")
    logging.info("-"*20+"Calculating random step and new point"+"-"*20)    
    
    point = point_list[startpointindex].copy()
    point_scaled = pd.DataFrame(Xscaler.transform(point), columns=point.columns)

    logging.info(point)
        
    parnames=point_scaled.columns
    step=MC_settings["step_length"]
    while True:
        if MC_settings["NN_assist"]:
            procs=[]
            results=[]
            q=multiprocessing.Queue()
            procs.append(multiprocessing.Process(target=NN_selectfromrandom,args=(point_scaled, yscaler, MC_settings, NN_settings, paths, q)))        
            procs[-1].start()
            while len(procs)>0:
                procs[0].join()
                procs.pop(0)    
            while not q.empty():
                results.append(q.get())
            new_point_scaled = results[0]
        else:
            new_point_scaled = [point_scaled[p].iloc[0]+random.gauss(-step,step) for p in parnames]    
            new_point_scaled = pd.DataFrame([new_point_scaled], columns=point.columns)
        closestpointdist=min(get_distances(X_scaled,new_point_scaled)["Distance"])
        if closestpointdist>MC_settings["min_dist"]:
            logging.info(f'distance to closest point {closestpointdist} larger than set minimum distance {MC_settings["min_dist"]} -> accept point')
            break
        else:
            logging.info(f'distance to closest point {closestpointdist} smaller than set minimum distance {MC_settings["min_dist"]} -> reject point')
        
    
    new_point=pd.DataFrame(Xscaler.inverse_transform(new_point_scaled), columns=point.columns)
    
    new_point=new_point.round(4)
    for col_name, value in new_point.iloc[0].items():
        if value < 0.0001: new_point[col_name]=0.0001            
    logging.info(new_point)
        
    point_list.append(new_point)
    logging.info(f"New Point:\n{new_point.iloc[0]}")

def NN_selectfromrandom(point_scaled, yscaler, MC_settings, NN_settings, paths, q=False):
    import tensorflow as tf
    from tensorflow import keras
    
    ANN_save_folder=paths["ANN_save_folder"]
    hyperparmanames=["LSF","ACF","NEP","NCL","BSP"]
    hyperparams={}
    for hpn in hyperparmanames:
        hyperparams[hpn]=NN_settings[hpn]  
    hyperparstr=getstringfromdict(hyperparams)
    n_train=NN_settings["n_train"]
    step=MC_settings["step_length"]
    nrandpoints=NN_settings["n_rand_points"]
    parnames=point_scaled.columns
    randmods=[[point_scaled[p].iloc[0]+random.gauss(-step,step) for p in parnames] for i in range(int(nrandpoints))]
    predictions=[]
    for nt in range(1,n_train+1): 
        if n_train>1:
            multitstr="-%d"%nt
        else:
            multitstr=""
        model=keras.models.load_model(ANN_save_folder+"/ANN_like_%s_%s%s.keras"%(MC_settings["lossparameter"],hyperparstr,multitstr))                 
        evalmods=pd.DataFrame(randmods, columns=point_scaled.columns)   
        prediction=yscaler.inverse_transform(model.predict(evalmods))
        del model
        predictions.append(prediction)
    sumprediction=sum(predictions)
    best_pred_ind=np.argmin(sumprediction)
    best_pred=sumprediction[best_pred_ind]/n_train
    best_allpred=[]
    for nt in range(n_train):
        best_allpred.append(predictions[nt][best_pred_ind])
    logging.info(f"best prediction: {best_pred} ({best_allpred}) at index: {best_pred_ind}")        
    new_best_point_scaled=evalmods.iloc[[best_pred_ind]]
    if q:
        q.put(new_best_point_scaled)
    else:
        return new_best_point_scaled
    return


# %%
def main():
    # Initializing Variables
    # 0. Load settings from "config.yaml" file in same folder as this script and potentially overwrite parameters
    MC_settings, preset_parameters, comp_settings, NN_settings, paths = load_config()
    
    save_folder = generate_saveFolderName(paths, comp_settings["load_previous"], MC_settings)
    logging.basicConfig(
        level = logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        filename = os.path.join(save_folder, "output.log")
    )
    os.system("ln -sfn "+os.path.join(save_folder, "output.log")+" nowlog.txt" )
    logging.info(MC_settings)
    logging.info(comp_settings)
    logging.info(NN_settings)
    
    point_list = []
    loss_list = []

    current_steps = 0           # Counter for how many descent steps have been taken
    current_nfiles = 0          # To check whether new dataload is necessary
    initialization = True       # During first loop load initial data
    startpointindex=-1
    
    while True:    

        logging.debug("Update and fit potentially new datapoints")
        new_nfiles=update_data(paths["fitSpectra_path"]%paths["fitmode"])
        if new_nfiles==None: new_nfiles=current_nfiles
        logging.debug(f"new_nfiles: {new_nfiles}")
        logging.debug(f"current_nfiles: {current_nfiles}")
                
        if (new_nfiles > current_nfiles) or initialization: 
            logging.info("Loading newest data as there were new files or we are at initialization")
            current_nfiles = new_nfiles    
            X_data, y_data, X_scaled, y_scaled, Xscaler, yscaler, X_fault, hashs, maxloss = load_data(paths["dragondata_path"]%(paths["fitmode"],paths["expstr"]),MC_settings,preset_parameters)
            
            
        
        if initialization:
            logging.info("initialization: When first starting script either load previous data or take designated starting point")
            initialization=False
            if comp_settings["load_previous"]==True: point_list, loss_list, startpointindex = load_previous_descentData(save_folder)  
            elif MC_settings["start_point"]=="Best":
                start_X, start_y = top_results(X_data, y_data, 1)
                point_list.append(start_X)
                loss_list.append(start_y)
                startpointindex=0
            elif MC_settings["start_point"]=="FarGood":
                medloss=float(np.median(y_data))    
                start_X, start_y = get_farthest_point(X_data, y_data, X_scaled, medloss)
                point_list.append(start_X)
                loss_list.append(start_y)
                startpointindex=0
            elif MC_settings["start_point"]=="GoodFar":
                best_X, best_y = top_results(X_data, y_data, 1)
                point_scaled = pd.DataFrame(Xscaler.transform(best_X.copy()), columns=best_X.columns)
                dists=get_distances(X_scaled,point_scaled)
                meddist=float(np.median(dists["Distance"]))    
                farpointind=dists.index[dists["Distance"]>meddist].tolist()                
                far_y=y_data.loc[farpointind]
                bestfarind=far_y.idxmin()
     
                start_X=X_data.loc[bestfarind].copy().reset_index(drop=True)
                start_y=y_data.loc[bestfarind].iloc[0]['Y']
                point_list.append(start_X)
                loss_list.append(start_y)
            elif MC_settings["start_point"]=="Hash":
                foundhhash=False
                for row in hashs.iterrows():
                    if MC_settings["start_hash"] == row[1].values[0]:
                        logging.info(f'found hash:\n{row[1].values[0]}\n{MC_settings["start_hash"]}\nat index:{row[0]}')
                        starthashpos=row[0]
                        foundhhash=True
                        break
                if foundhhash==True:                    
                    #logging.info("point:\n",X_data.loc[starthashpos],"\nloss:\n",y_data.loc[starthashpos])
                    start_X=X_data.loc[[starthashpos]].copy().reset_index(drop=True)
                    point_list.append(start_X)        
                    loss_list.append(y_data.loc[[starthashpos]].values[0].item())
                    logging.info(f"{point_list[0]}\n{loss_list[0]}")
                    startpointindex=0
                else:
                    logging.info(f'could not find hash: {MC_settings["start_hash"]}')
                    sys.exit(1)
            if MC_settings["base_ref_point"]=="Best":
                norm_y=min(y_data['Y'])*MC_settings["base_ref_factor"]
            elif MC_settings["base_ref_point"]=="Start":
                norm_y=loss_list[-1]*MC_settings["base_ref_factor"]
            if MC_settings["NN_assist"]:                
                hyperparmanames=["LSF","ACF","NEP","NCL","BSP"]
                hyperparams={}
                for hpn in hyperparmanames:
                    hyperparams[hpn]=NN_settings[hpn]  
                procs=[]         
                if int(NN_settings["n_train"])>1:
                    for nt in range(1,int(NN_settings["n_train"])+1):
                        procs.append(multiprocessing.Process(target=likepredict,args=(X_scaled, y_scaled, preset_parameters, paths["ANN_save_folder"], MC_settings["lossparameter"], hyperparams, nt, 0)))        
                        procs[-1].start()
                        if nt<int(NN_settings["n_train"]):
                            while len(procs)>0:
                                procs[0].join()
                                procs.pop(0) 
                else:                    
                    procs.append(multiprocessing.Process(target=likepredict,args=(X_scaled, y_scaled, preset_parameters, paths["ANN_save_folder"], MC_settings["lossparameter"], hyperparams, False, 0)))        
                    procs[-1].start()
                
        logging.info("Check if previous task has finished successfully or with inf output ")
        simulation_finished, simulation_infnan = checkSimulationProgress(X_data, y_data, X_fault, point_list, loss_list, maxloss)
        
        if simulation_finished:
            logging.info(f"Loss of last calculated point: {loss_list[-1]}")
            if current_steps+1>comp_settings["max_steps"]: 
                if comp_settings["autorestart"]:
                    initialization=True  
                    current_steps = 0           
                    current_nfiles = 0
                    continue
                    logging.info("Markov Chain has reached preset length, restarting")
                else:
                    logging.info("Markov Chain has reached preset length, exiting program")
                sys.exit(0)
            current_steps+=1    
            logging.info("Calculate next random step")
            if not simulation_infnan:
                if loss_list[-1]<=loss_list[startpointindex]:
                    logging.info(f"accept new point with better loss {loss_list[-1]} than old point {loss_list[startpointindex]}")
                    startpointindex=len(loss_list)-1                      
                    if loss_list[-1]*MC_settings["base_ref_factor"]<norm_y:
                        norm_y=loss_list[-1]*MC_settings["base_ref_factor"]
                        logging.info("loss offset for probability calculation updated")
                else:
                    olddist=get_distances(point_list[0],point_list[startpointindex])["Distance"][0]
                    newdist=get_distances(point_list[0],point_list[-1])["Distance"][0]
                    if MC_settings["accept_far_only"] and olddist>newdist:  
                        logging.info(f"keep old point because new point closer to start point, distances old,new: {olddist},{newdist}")
                    else:                    
                        accept_point_prob = math.tan(pow(0.25*math.pi*(loss_list[startpointindex]-norm_y)/(loss_list[-1]-norm_y),MC_settings["accept_prob_exponent"]))          
                        logging.info(f"probability to accept new point: {accept_point_prob}")
                        randval=random.uniform(0,1)
                        if randval<accept_point_prob:
                            logging.info(f"accept new point based on random value roll: {randval}")
                            startpointindex=len(loss_list)-1  
                        else:
                            logging.info(f"keep old point based on random value roll: {randval}")
            if MC_settings["NN_assist"]:   
                while len(procs)>0:
                    procs[0].join()
                    procs.pop(0)       
                
            randomStep(point_list, startpointindex, Xscaler, yscaler, X_scaled, MC_settings, NN_settings, paths)
            newpointdist=get_distances(point_list[0],point_list[-1])["Distance"][0]
            logging.info(f"Distance of new point to start point: {newpointdist}")
            if int(comp_settings["simulation_IP"])==0:
                logging.info("Test run complete - IP is 0, exit")
                sys.exit(0)
        
            logging.info("Step: %d/%d -- Submit new point to simulation"%(current_steps,comp_settings["max_steps"]))
            submit_task(point_list[-1], paths["dragonbkg_path"], int(comp_settings["simulation_IP"]), preset_parameters)
            if MC_settings["NN_assist"]:     
                if int(NN_settings["n_train"])>1:
                    for nt in range(1,int(NN_settings["n_train"])+1):
                        procs.append(multiprocessing.Process(target=likepredict,args=(X_scaled, y_scaled, preset_parameters, paths["ANN_save_folder"], MC_settings["lossparameter"], hyperparams, nt, 0)))        
                        procs[-1].start()
                        if nt<int(NN_settings["n_train"]):
                            while len(procs)>0:
                                procs[0].join()
                                procs.pop(0) 
                else:                                
                    procs.append(multiprocessing.Process(target=likepredict,args=(X_scaled, y_scaled, preset_parameters, paths["ANN_save_folder"], MC_settings["lossparameter"], hyperparams, False, 0)))        
                    procs[-1].start()
        nw=0
        while nw<300:
            print("Waiting for tasks to finish %d/300s                                                              "%(nw),end = '\r', flush=True)
            time.sleep(1)
            nw=nw+1
        # wait 5 minutes until next check of whether a task has finished
        
if __name__ == "__main__":
    main()
