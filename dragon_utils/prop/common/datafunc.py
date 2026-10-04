
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

def update_data(fitSpectra_path):
    directory = os.path.dirname(fitSpectra_path)
    file_name = os.path.basename(fitSpectra_path)
    
    os.chdir(directory)
    #command = f"./{file_name}"  
    command = f"python {file_name}"    
    filenumber = None

    # Execute fitspectra-xxx in interactive mode (read write to console possible)
    with subprocess.Popen(command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1, universal_newlines=True) as process:
        logging.debug("\n")
        logging.debug("-"*20+"Fitting potential new simulations"+"-"*20)
        start_time = time.time()                                    # To check whether we are caught in a loop
        
        while True:
            output = process.stdout.readline().strip()              # IMPORTANT: in fitSpectra-xxx's "input('text')" prompts end all the lines with 'text\n', otherwise readline() cannnot read the input prompt and we wait forever!!!
            if type(output)!=str: output = output.decode()
            
            if output: 
                start_time=time.time()
                if "starting prefit" in output:             # read out current simulation number
                    match = re.search(r"\d+", output)
                    if match: filenumber = int(match.group())
                if "select order parameter" in output: break        # if we arrive at ordering of finished fits, end the fitting
                logging.debug(f"{output}")
                if "enter maximum age of files" in output: 
                    process.stdin.write("0\n")
                    process.stdin.flush()
                    logging.debug("0")
                if "use saved prefit data?" in output:
                    process.stdin.write("y\n")
                    process.stdin.flush()
                    logging.debug("y")
                
    
            if output == "" and process.poll() is not None: break   # if there is no output and no further communication, end the fitting
            if time.time() - start_time > 300: raise TimeoutError("No processable communication for > 5 minutes. Terminated simulation fitting!")
    if filenumber == None: 
        logging.warning("No new simulation number could be obtained. Two conflicting requests trying to fit likely. Waiting random time before next request.")
        time.sleep(random.randint(0, 300))      
    return filenumber

# %% [markdown]
# ### Load Data

# %%
def load_data(dragon_datapath,interpol_datapath,settings,preset_parameters):
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
    if settings["useinterpoldata"]:
        intpdata=load_interpolation_data(interpol_datapath,settings)                
        intpdata["iI"]=True
        data = pd.concat([data,intpdata], ignore_index=True, axis=0).reset_index(drop=True)
        
    # 2. Process data by dropping nans and infs  
    init_len = len(data)
    
    if settings["infliketreatment"]=="replace":
        if settings["maxloss"]=="maxval":
            maxloss=data.loc[data["Y"]!=np.inf, "Y"].max()
            print("maxloss set to : ",maxloss)
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
        faultreplace["W"]=1.0
        faultreplace["iI"]=False
        data = pd.concat([data, faultreplace], ignore_index=True, axis=0).reset_index(drop=True)
        data = data.dropna().reset_index(drop=True)
        post_len = len(data)
    elif settings["infliketreatment"]=="remove":
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
        faultdata = filter_points(faultdata, preset_parameters)

    w_data = data[["W"]].copy()
    data = data.copy().drop(columns=w_data.columns)
    y_data = data[["Y"]].copy()
    data = data.copy().drop(columns=y_data.columns)
    isintpol = data[["iI"]].copy()
    X_data = data.copy().drop(columns=isintpol.columns)
    
    
    # 4. Fitting scalers to standardize data  
    if settings["scaler"]=="Standard":
        Xscaler = StandardScaler()
        yscaler = StandardScaler()
    elif settings["scaler"]=="Robust":
        Xscaler = RobustScaler()
        yscaler = RobustScaler()
    X_scaled = pd.DataFrame(Xscaler.fit_transform(X_data.copy()), columns=X_data.columns)
    y_scaled = pd.DataFrame(yscaler.fit_transform(y_data.copy()), columns=y_data.columns)
    #print("Lengths of X, y, sX, sy:")
    #print(len(X_data), len(y_data), len(X_scaled), len(y_scaled))
    return X_data, y_data, X_scaled, y_scaled, Xscaler, yscaler, w_data, isintpol, faultdata

# %% [markdown]
# ### Load/Save Previous Gradient Descent Or Current Best Point


def load_interpolation_data(interpol_datapath,settings):
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
    lossparamdict={"x":0,"v":2,"r":3,"p":4,"h":5,"f":6,"q":7,"vf":8,"l":9,"ml":10,"tl":11,"ql":12,"sl":13,"m":14,"s":15,"c":16,"cl":17}
    lossparamcode=lossparamdict[settings["lossparameter"]]
    preweight=settings["interpoldataweight"]
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
    if settings["scaler"]=="Standard":
        interpol_scaler = StandardScaler()
    elif settings["scaler"]=="Robust":
        interpol_scaler = RobustScaler()
    interpol_scale = pd.DataFrame(interpoldata.copy(), columns=interpoldata.columns)
    interpol_scale.drop(columns=["Y"], inplace=True)
    interpol_scaled = interpol_scaler.fit_transform(interpol_scale)
    parentinfo1_scaled = pd.DataFrame(interpol_scaler.transform(parentinfo1.copy()), columns=parentinfo1.columns)
    parentinfo2_scaled = pd.DataFrame(interpol_scaler.transform(parentinfo2.copy()), columns=parentinfo2.columns)
    distances = np.linalg.norm(parentinfo2-parentinfo1, axis=1)
    weights = np.power(distances+1.0,-int(settings["dist_weight_power"]))
    interpoldata["W"]=preweight*weights
    return interpoldata
    

def get_best_point(X, y, iI):
    return get_best_points(X, y, iI, 1)


def get_best_points(X, y, iI, n):
    # returns the n best X,y parameters in terms of log-likelihood
    X_der = X.copy()[~iI["iI"]].reset_index(drop=True)
    y_der = y.copy()[~iI["iI"]].reset_index(drop=True)
    ycolumn = y_der.columns[0]    
    top_index = y_der.sort_values(by=ycolumn, ascending=True).head(n).index.tolist()
    top_y = y_der.loc[top_index].reset_index(drop=True)
    top_X = X_der.loc[top_index].reset_index(drop=True)
    return [top_X], [pd.DataFrame(0., index=range(n), columns=X_der.columns)], [top_y.values[0].item()]


def filter_points(X, preset_parameters):
    X_filt = X.copy().reset_index(drop=True)
    for col_name,value in preset_parameters.items():
        dropindx=X_filt.index[X_filt[col_name]!=value]
        X_filt.drop(dropindx,inplace=True)
    filtered_X = X_filt.reset_index(drop=True)
    return filtered_X


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


def recenter_data(X_scaled,X_center):
    X_shifted=X_scaled.copy()-X_center.reindex_like(X_scaled,method="nearest")  
    return X_shifted

