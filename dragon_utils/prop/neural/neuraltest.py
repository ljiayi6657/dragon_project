#!/usr/bin/python3

import os, sys, time, math, glob, random, itertools

import pandas as pd
import numpy as np

from sklearn.preprocessing import StandardScaler, RobustScaler, PolynomialFeatures, SplineTransformer, MaxAbsScaler, FunctionTransformer 
from sklearn.model_selection import train_test_split

import subprocess

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

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.layers import IntegerLookup
from tensorflow.keras.layers import Normalization
from tensorflow.keras.layers import StringLookup
from tensorflow.keras import mixed_precision

policy = mixed_precision.Policy('mixed_float16')
mixed_precision.set_global_policy(policy)


import multiprocessing
import subprocess


#print("now importing mpl..."
import matplotlib as mpl
#print("imported mpl"
mpl.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as color
import matplotlib.mlab as mlab
import matplotlib.cm as cmx

print("TensorFlow version:", tf.__version__)

def main():
    multitrain=20
    physical_devices = tf.config.list_physical_devices('GPU')    
    print("Physical GPUs:", physical_devices)    
      
    #logical_devices = tf.config.list_logical_devices('GPU')
    #print("Logical GPUs:", logical_devices)
    nproc=len(physical_devices)
    if 0:
        physical_devices = tf.config.list_physical_devices('GPU')
        print("Num GPUs:", len(physical_devices))
        print(physical_devices) 
        physical_devices = tf.config.list_physical_devices('GPU')
        try:
          tf.config.set_logical_device_configuration(
            physical_devices[0],
            [tf.config.LogicalDeviceConfiguration(memory_limit=2048),
             tf.config.LogicalDeviceConfiguration(memory_limit=2048),
             tf.config.LogicalDeviceConfiguration(memory_limit=2048)])

          logical_devices = tf.config.list_logical_devices('GPU')
          assert len(logical_devices) == 3
        except:
          print("Invalid device or cannot modify logical devices once initialized.")
          sys.exit(1)
          
    #testparpredict(multitrain,nproc)
    testlikepredict(multitrain,nproc)

     
def testparpredict(multitrain,nproc):
    NN_settings, preset_parameters, comp_settings, paths = load_config()
    save_folder="/home/motz/CALETana/prop/neural/NN_test" 
    ANN_save_folder="/ssdhome/motz/neural/NN_test"    
    X_data, Y_data, X_scaled, Y_scaled, Xscaler, Yscaler= load_flux_data(paths["dragondata_path"],paths["interpoldata_path"], NN_settings=NN_settings, preset_parameters=preset_parameters)    
    errordict={}
    errerrdict={}
    serrordict={}
    hyperparmanames=["LSF","NEP","BSP","NCL","NSL"]
    hyperparamvals={}
    hyperparamvals["LSF"]=[3]  #[0.3,0.5,0.8]
    hyperparamvals["NEP"]=[10000]
    hyperparamvals["BSP"]=[10]
    hyperparamvals["NCL"]=[1]
    hyperparamvals["NSL"]=[4,6,8]
    hyperlistlist=[hyperparamvals[hpn] for hpn in hyperparmanames]
    hyperparamcombos=list(itertools.product(*hyperlistlist))   
    nhp=0
    nhptot=len(hyperparamcombos)
    procs=[]
    n=0
    for hpc in hyperparamcombos:
        nhp=nhp+1
        hyperparams={}
        hyperparstr=""
        for hpn,hpv in zip(hyperparmanames,hpc):
            hyperparams[hpn]=hpv  
            hyperparstr=hyperparstr+hpn+str(hpv).replace(".","d")
        #print(nhp,"/",nhptot," -- training NN for hyperparams: ",hyperparams)        
        for mti in range(1,multitrain+1):
            if checktrainingexist_param(Y_data,hyperparams,save_folder,ANN_save_folder,preset_parameters,mti):
                continue
            n=n+1
            while True:
                if len(procs)<nproc:          
                    procs.append(multiprocessing.Process(target=parampredict,args=(X_scaled, Y_scaled, Yscaler, preset_parameters,save_folder,ANN_save_folder,hyperparams, mti,n%nproc)))        
                    procs[-1].start()
                    break
                else:
                    procs[0].join()
                    procs.pop(0)
    while len(procs)>0:
        procs[0].join()
        procs.pop(0)        
    for hpc in hyperparamcombos:
        hyperparams={}
        hyperparstr=""
        for hpn,hpv in zip(hyperparmanames,hpc):
            hyperparams[hpn]=hpv  
            hyperparstr=hyperparstr+hpn+str(hpv).replace(".","d")
        error,errerr,serrdict=reeval_param(Y_data,hyperparams,save_folder,ANN_save_folder,preset_parameters,multitrain)
        errordict[error]=hyperparams
        errerrdict[error]=errerr
    serrordict[hyperparstr]=serrdict
    besterror=min(errordict.keys())
    besthyperparam=errordict[besterror]
    
    print("separate errors:")
    for hp in serrordict.keys():
        print(hp)
        ed=serrordict[hp]
        for pn in ed.keys():
            print(pn,ed[pn])
            
    print("averaged errordict:")
    print(errordict)
    print("best error (uncertainty): ",besterror," (",errerrdict[besterror],")")
    print("best hyperparams: ",besthyperparam)    
        
    return
   
   
def testlikepredict(multitrain,nproc):
    NN_settings, preset_parameters, comp_settings, paths = load_config()
    save_folder="/home/motz/CALETana/prop/neural/NN_test" 
    ANN_save_folder="/ssdhome/motz/neural/NN_test"    
    X_data, y_data, X_scaled, y_scaled, Xscaler, yscaler, w_data, isintpol, X_fault =load_like_data(paths["dragondata_path"],paths["interpoldata_path"], NN_settings=NN_settings, preset_parameters=preset_parameters)    
    
    
    hyperparmanames=["LSF","ACF","NEP","NCL","BSP"]
    hyperparamvals={}
    hyperparamvals["LSF"]=[0.5,0.6] #[0.3,0.5,0.8]
    hyperparamvals["ACF"]=["gelu"]
    hyperparamvals["NEP"]=[10000,12000]
    hyperparamvals["NCL"]=[3]
    hyperparamvals["BSP"]=[10]
    hyperlistlist=[hyperparamvals[hpn] for hpn in hyperparmanames]
    hyperparamcombos=list(itertools.product(*hyperlistlist))    
    losspar=NN_settings["lossparameter"]
    nhp=0
    nhptot=len(hyperparamcombos)
    procs=[]
    n=0
    for mti in range(1,multitrain+1):
        X_train, X_test, y_train, y_test = preparelikedata(X_scaled, y_scaled, preset_parameters)
        for hpc in hyperparamcombos:
            nhp=nhp+1
            hyperparams={}
            hyperparstr=""
            for hpn,hpv in zip(hyperparmanames,hpc):
                hyperparams[hpn]=hpv  
                hyperparstr=hyperparstr+hpn+str(hpv).replace(".","d")
            #print(nhp,"/",nhptot," -- training NN for hyperparams: ",hyperparams)        
        
            if checktrainingexist_like(y_data,hyperparams,save_folder,ANN_save_folder, losspar, preset_parameters,mti):
                continue
            n=n+1
            while True:
                if len(procs)<nproc:
                    procs.append(multiprocessing.Process(target=likepredict,args=(X_train, X_test, y_train, y_test, preset_parameters, save_folder, ANN_save_folder, losspar, hyperparams, mti, n%nproc)))        
                    procs[-1].start()
                    break
                else:
                    procs[0].join()
                    procs.pop(0)
    while len(procs)>0:
        procs[0].join()
        procs.pop(0)        
    
    errordict,errerrdict=reeval_like(X_data, y_data, X_scaled, y_scaled, Xscaler, yscaler, isintpol, preset_parameters, save_folder , ANN_save_folder, losspar, hyperparmanames, hyperparamcombos, multitrain)
        
    #getpoint,new_point,new_prediction=getrandommodel(X_data, y_data, X_scaled, y_scaled, Xscaler, yscaler, isintpol, preset_parameters, save_folder)
            
    besterror=min(errordict.keys())
    besterrerr=errerrdict[besterror]
    besthyperparam=errordict[besterror]
    print("errordict:")
    for er in sorted(errordict.keys()):    
        print(er,"(",errerrdict[er],") : ",errordict[er])
    print("------------------------------------")
    print("best error: ",besterror," (error:",besterrerr,")")
    print("best hyperparams: ",besthyperparam)
            
    return
    

    
def generate_saveFolderName(path, comp_settings, settings):
    IP=comp_settings["simulation_IP"]
    folder_prefix = get_folderPrefix(IP,settings)
    date = datetime.now().strftime("%Y-%m-%d")
    highest_folder, id = get_folderID(folder_prefix, path)
    folder_name = f"{folder_prefix}_{date}_{id+1}"
    save_path = os.path.join(path, folder_name)
    os.makedirs(save_path, exist_ok=True)
    with open(os.path.join(save_path, "output.log"),"w") as file: pass
        
    return save_path

def get_folderPrefix(IP,s):
    prefix = f"IP{IP}_{s['lossparameter']}"
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
def load_config():
    try: script_dir = os.path.dirname(os.path.realpath(__file__))
    except: script_dir = f"/home/{getpass.getuser()}/CALETana/prop/neural"
    with open(os.path.join(script_dir, "config.yaml"), "r") as file:
        config = yaml.safe_load(file)
    NN_settings = config["NN_settings"]
    preset_parameters = config["preset_parameters"]
    comp_settings = config["comp_settings"]
    paths = config["paths"]
    return NN_settings, preset_parameters, comp_settings, paths
        
    
def load_flux_data(dragon_datapath,interpol_datapath,NN_settings,preset_parameters):
    logging.info("\n")
    logging.info("-"*20+"Loading and processing new data"+"-"*20)
    indxdct={0:"p",2:"he",3:"he3/he4",5:"ap/p",6:"apt"}   
    PLidct={0:"p",2:"he3",3:"he4"}   
    #dPLidct={0:"p",2:"he3",3:"he4"}   
    # 1. Load data and save in pd.DataFrame
    data_loaded = False
    while not data_loaded:
        #try:
        with open(dragon_datapath, "rb") as file:
                hashdict,foundfiles,globpardict,globpflxs,pfs,x2s,x2dict,vx2s,vx2dict,rx2s,rx2dict,px2s,px2dict,hx2s,hx2dict,fx2s,fx2dict,qx2s,qx2dict,vfx2s,vfx2dict,likes,likedict,mlikes,mlikedict,tlikes,tlikedict,qlikes,qlikedict,slikes,slikedict,mx2s,mx2dict,sx2s,sx2dict,tss,tsdict,faultfiles,faultpardict,corrfactlist = pickle.load(file)                             
                fluxdata=pd.DataFrame.from_records(globpflxs)
                paramdata = pd.DataFrame.from_dict(globpardict)                
        data_loaded = True
            
        #except Exception as e:
        #    logging.warning(f"Error occured: {e}")
        #    logging.info("Two runs might be trying to access data simultaneously. Waiting before trying again.")
        #    time.sleep(random.randint(0, 300)) 
    if preset_parameters!=None:
        beforefilterlen=len(paramdata)
        logging.info(f"Simulations before preset parameters filter: {beforefilterlen}")
        (paramdata,fluxdata) = filter_points([paramdata,fluxdata], preset_parameters)
        afterfilterlen=len(paramdata)
        logging.info(f"Simulations before preset parameters filter: {afterfilterlen}")
    X_datas=[]
    energyfiltered=[e for e in list(fluxdata.columns) if e>0.1 and e<1e5]
    for indx in sorted(indxdct.keys()):
        if indx==2:
            X_datas.append(pd.DataFrame(np.array([[(j[2]+j[3])*i**2.7 for j in fluxdata[i]] for i in energyfiltered]).T, columns=[indxdct[2]+"_"+str(cn) for cn in energyfiltered]))
        elif indx==3:
            X_datas.append(pd.DataFrame(np.array([[j[3]/j[2] for j in fluxdata[i]] for i in energyfiltered]).T, columns=[indxdct[3]+"_"+str(cn) for cn in energyfiltered]))
        elif indx==5:
            X_datas.append(pd.DataFrame(np.array([[(j[5]+j[6])/j[0] for j in fluxdata[i]] for i in energyfiltered]).T, columns=[indxdct[5]+"_"+str(cn) for cn in energyfiltered]))
        elif indx==6:
            continue
        else:        
            X_datas.append(pd.DataFrame(np.array([[j[indx]*i**2.7 for j in fluxdata[i]] for i in energyfiltered]).T, columns=[indxdct[indx]+"_"+str(cn) for cn in energyfiltered]))
    for indx in sorted(PLidct.keys()):
        X_datas.append(pd.DataFrame(np.array([[np.log(k[indx]/j[indx])/np.log(m/i) for j,k in zip(fluxdata[i],fluxdata[m])] for i,m in zip(energyfiltered[:-1],energyfiltered[1:])]).T, columns=[PLidct[indx]+"_"+str(cn) for cn in energyfiltered[:-1]])) 
    #for indx in sorted(dPLidct.keys()):
    #    X_datas.append(pd.DataFrame(np.array([[np.log(k[indx]/j[indx])/np.log(m/i) for j,k in zip(fluxdata[m],fluxdata[n],fluxdata[o])] for i,m in zip(energyfiltered[:-2],energyfiltered[1:-1],energyfiltered[:-2])]).T, columns=[PLidct[indx]+"_"+str(cn) for cn in energyfiltered[1:-1]])) 
        #print(indx)
        #print(X_datas[-1])
    X_data=pd.concat(X_datas,join="inner",axis=1).fillna(0)    
    Y_data=paramdata
    #print("unscaled flux data:")
    #print(X_data)
    #print(Y_data)    
    
    #print("scaling now:")
    
    if NN_settings["scaler"]=="Standard":
        Xscaler = StandardScaler()
        Yscaler = StandardScaler()
    elif NN_settings["scaler"]=="Robust":
        Xscaler = RobustScaler()
        Yscaler = RobustScaler()
    X_scaled = pd.DataFrame(Xscaler.fit_transform(X_data.copy()), columns=X_data.columns)
    Y_scaled = pd.DataFrame(Yscaler.fit_transform(Y_data.copy()), columns=Y_data.columns)    
    #print(X_scaled)
    #print(Y_scaled)
    return X_data, Y_data, X_scaled, Y_scaled, Xscaler, Yscaler
  
def load_like_data(dragon_datapath,interpol_datapath,NN_settings,preset_parameters):
    logging.info("\n")
    logging.info("-"*20+"Loading and processing new data"+"-"*20)

    # 1. Load data and save in pd.DataFrame
    data_loaded = False
    while not data_loaded:
        try:
            with open(dragon_datapath, "rb") as file:
                hashdict,foundfiles,globpardict,pflxs,pfs,x2s,x2dict,vx2s,vx2dict,rx2s,rx2dict,px2s,px2dict,hx2s,hx2dict,fx2s,fx2dict,qx2s,qx2dict,vfx2s,vfx2dict,likes,likedict,mlikes,mlikedict,tlikes,tlikedict,qlikes,qlikedict,slikes,slikedict,mx2s,mx2dict,sx2s,sx2dict,cx2s,cx2dict,tss,tsdict,faultfiles,faultpardict,corrfactlist = pickle.load(file)
                lossparamdict={"x":x2s,"v":vx2s,"r":rx2s,"p":px2s,"h":hx2s,"f":fx2s,"q":qx2s,"vf":vfx2s,"l":likes,"ml":mlikes,"tl":tlikes,"ql":qlikes,"sl":slikes,"m":mx2s,"s":sx2s,"c":cx2s}
                globpardict["Y"]=lossparamdict[NN_settings["lossparameter"]]
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
    if NN_settings["useinterpoldata"]:
        intpdata=load_interpolation_data(interpol_datapath,NN_settings)                
        intpdata["iI"]=True
        data = pd.concat([data,intpdata], ignore_index=True, axis=0).reset_index(drop=True)
        
    # 2. Process data by dropping nans and infs  
    init_len = len(data)
    
    if NN_settings["infliketreatment"]=="replace":
        if NN_settings["maxloss"]=="maxval":
            maxloss=data.loc[data["Y"]!=np.inf, "Y"].max()
            print("maxloss set to : ",maxloss)
        elif NN_settings["maxloss"]=="default":            
            if "l" in NN_settings["lossparameter"]:
                maxloss=-np.log(sys.float_info.min)
            else:
                maxloss=sys.float_info.max**0.1
        else:
            maxloss=int(NN_settings["maxloss"]) 
        data.replace([np.inf, -np.inf], maxloss, inplace=True)    
        faultreplace=faultdata.copy()
        faultreplace["Y"]=[maxloss]*len(faultdata)
        faultreplace["W"]=1.0
        faultreplace["iI"]=False
        data = pd.concat([data, faultreplace], ignore_index=True, axis=0).reset_index(drop=True)
        data = data.dropna().reset_index(drop=True)
        post_len = len(data)
    elif NN_settings["infliketreatment"]=="remove":
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
        data = filter_points([data], preset_parameters)[0]
        afterfilterlen=len(data)
        logging.info(f"Simulations before preset parameters filter: {afterfilterlen}")

    w_data = data[["W"]].copy()
    data = data.copy().drop(columns=w_data.columns)
    y_data = data[["Y"]].copy()
    data = data.copy().drop(columns=y_data.columns)
    isintpol = data[["iI"]].copy()
    X_data = data.copy().drop(columns=isintpol.columns)
    
    
    # 4. Fitting scalers to standardize data  
    if NN_settings["scaler"]=="Standard":
        Xscaler = StandardScaler()
        yscaler = StandardScaler()
    elif NN_settings["scaler"]=="Robust":
        Xscaler = RobustScaler()
        yscaler = RobustScaler()
    X_scaled = pd.DataFrame(Xscaler.fit_transform(X_data.copy()), columns=X_data.columns)
    y_scaled = pd.DataFrame(yscaler.fit_transform(y_data.copy()), columns=y_data.columns)
    return X_data, y_data, X_scaled, y_scaled, Xscaler, yscaler, w_data, isintpol, faultdata

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

def filter_points(datas, preset_parameters):
    X=datas[0]
    X_filt = X.copy().reset_index(drop=True)    
    Y_filts=[]
    for y in datas[1:]:
        Y_filts.append(y.copy().reset_index(drop=True))
    for col_name,value in  preset_parameters.items():
        dropindx=X_filt.index[X_filt[col_name]!=value]        
        X_filt.drop(dropindx,inplace=True)
        for y in Y_filts:
            y.drop(dropindx,inplace=True)
    filtered_X = X_filt.reset_index(drop=True)
    filtered=[filtered_X]
    for y in Y_filts:
        filtered.append(y.reset_index(drop=True))
    return filtered

def get_best_point(X, y, iI):
    # returns the n best X,y parameters in terms of log-likelihood
    X_der = X.copy()[~iI["iI"]].reset_index(drop=True)
    y_der = y.copy()[~iI["iI"]].reset_index(drop=True)
    ycolumn = y_der.columns[0]    
    top_index = y_der.sort_values(by=ycolumn, ascending=True).head(1).index.tolist()
    top_y = y_der.loc[top_index].reset_index(drop=True)
    top_X = X_der.loc[top_index].reset_index(drop=True)
    return top_X,top_y.values[0].item()
    
def getstringfromdict(dic):
    string=""
    for k,v in dic.items():
        string=string+k+str(v)
    return string.replace(".","d")

def preparelikedata(X_scaled, y_scaled, preset_parameters):
    if preset_parameters!=None:
        presence = [item in X_scaled.columns for item in list(preset_parameters.keys())]
        for i, present in enumerate(presence):
            if not present: logging.warning(f"There is no parameter {list(preset_parameters.keys())[i]} in data which could be preset!")
        X_scaled = X_scaled.drop(columns=list(preset_parameters.keys()))
        
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y_scaled, test_size=0.3)
    return X_train, X_test, y_train, y_test

def likepredict(X_train, X_test, y_train, y_test, preset_parameters, save_folder, ANN_save_folder, losspar, hyperparams, multitrain=False, ngpu=0):    
    start_time = time.time()
    hyperparstr=getstringfromdict(hyperparams)
    
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
        print("used GPU: ",gpus[ngpu]," device: ",logical_devices[0])
        input_layer = layers.Input(shape=(nfeature,))
        scale_layer = layers.Dense(units = nfeature, activation = "linear")(input_layer)
        processlayers=[scale_layer]
        for nl in range(n_processlayers):
            processlayers.append(layers.Dense(units = layerscale, activation = hyperparams["ACF"])(processlayers[nl]))
            #print("adding common processing layer ",nl," with ",layerscale," units")       
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
        model.save(ANN_save_folder+"/ANN_like_test_%s_%s%s.keras"%(losspar,hyperparstr,multitstr)) 
        print(model.summary())
        del model
    train_duration=time.time()-start_time   
    print("duration required for training: ",train_duration)
    #print("history elements:",history.keys())
    infotuple=(train_duration,gpus[ngpu],preset_parameters,len(y_train)+len(y_test))
    err = history['error']
    val_err = history['val_error']
    loss = history['loss']
    val_loss = history['val_loss']

    epochs_range = range(nepoch)
    

    plt.figure(figsize=(10, 10))
    plt.subplot(2, 1, 1)
    plt.plot(epochs_range, err, label = 'Training Error')
    plt.plot(epochs_range, val_err, label = 'Validation Error')
    plt.legend(loc = 'lower right')
    plt.title('Training and Validation Error', fontsize = 15)

    plt.subplot(2, 1, 2)
    plt.plot(epochs_range, loss, label = 'Training Loss')
    plt.plot(epochs_range, val_loss, label = 'Validation Loss')
    plt.legend(loc = 'upper right')
    plt.ylim(bottom = 0)
    plt.title('Training and Validation Loss', fontsize = 15)
    plt.subplots_adjust(left=0.06, right=0.98, top=0.92, bottom=0.1)
    plt.savefig(save_folder+"/ANN_like_train_info_%s_%s%s.png"%(losspar,hyperparstr,multitstr),dpi=600)   
    saveresults(save_folder+"/ANN_like_aux_data_%s_%s%s.dat"%(losspar,hyperparstr,multitstr),[history, X_train, X_test, y_train, y_test, infotuple])
    return
    
def parampredict(X_scaled, y_scaled, yscaler, preset_parameters,save_folder, ANN_save_folder, hyperparams, multitrain=False,ngpu=0):    
    start_time = time.time()
    hyperparstr=getstringfromdict(hyperparams)
    if preset_parameters!=None:
        presence = [item in y_scaled.columns for item in list(preset_parameters.keys())]
        for i, present in enumerate(presence):
            if not present: logging.warning(f"There is no parameter {list(preset_parameters.keys())[i]} in data which could be preset!")
        y_scaled = y_scaled.drop(columns=list(preset_parameters.keys()))
    
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y_scaled, test_size=0.3)

    nfeature=len(X_train.columns)
    npoints=len(y_train)
    n_out=len(y_scaled.columns)
    lsf=hyperparams["LSF"]
    nepoch=hyperparams["NEP"]
    batchsplit=hyperparams["BSP"]
    n_processlayers=hyperparams["NCL"]
    n_separatelayers=hyperparams["NSL"]
    print("nfeature:",nfeature)
    print("npoints:",npoints)
    print("nout:",n_out)    
    layerscale=max(int(npoints*lsf),nfeature)
    gpus=tf.config.list_physical_devices('GPU')    
    tf.config.set_visible_devices(gpus[ngpu], 'GPU')
    tf.config.experimental.set_memory_growth(gpus[ngpu], True)
    logical_devices = tf.config.list_logical_devices('GPU')    
    assert len(logical_devices)==1
    with tf.device(logical_devices[0]):
        print("used GPU: ",gpus[ngpu]," device: ",logical_devices[0])
        input_layer = layers.Input(shape=(nfeature,))
        scale_layer = layers.Dense(units = nfeature, activation = "linear")(input_layer)
        processlayers=[scale_layer]
        for nl in range(n_processlayers):
            processlayers.append(layers.Dense(units = layerscale, activation = "tanh")(processlayers[nl]))
            #print("adding common processing layer ",nl," with ",layerscale," units")       
        Y_processls=[]    
        Y_outputs=[]
        Y_trains=[]
        Y_tests=[]
        seplayerscale=int(layerscale/n_out)+1
        for par in list(y_scaled.columns):   
            Y_processls.append([])
            Y_processls[-1].append(layers.Dense(units = seplayerscale, activation = "tanh")(processlayers[-1]))
            #print("adding processing layer ",0," for parameter ",par," with ",seplayerscale," units")       
            for nl in range(n_separatelayers-1):
                #print("adding processing layer ",nl+1," for parameter ",par," with ",seplayerscale," units")  
                Y_processls[-1].append(layers.Dense(units = seplayerscale, activation = "tanh")(Y_processls[-1][-1]))
            on=par+"_output"
            Y_trains.append(np.array(y_train[par]))
            Y_tests.append(np.array(y_test[par]))
            Y_outputs.append(layers.Dense(units = 1, activation = "linear", name = on )(Y_processls[-1][-1]))
        
        #strategy = tf.distribute.MirroredStrategy()
        #print('Number of devices: {}'.format(strategy.num_replicas_in_sync))
        

        #Define the model with the input layer and a list of outputs
        model = keras.Model(inputs = input_layer, outputs = Y_outputs)
        #model = keras.Model(inputs = input_layer, outputs = [y1_output])

        #specify the optimizer and compile with the loss function for both outputs
        #
        #optimizer = keras.optimizers.Nadam()
        #lr_schedule = keras.optimizers.schedules.ExponentialDecay(initial_learning_rate=0.01,decay_steps=300,decay_rate=0.99)
        #optimizer = keras.optimizers.SGD(learning_rate=lr_schedule)
        #optimizer = keras.optimizers.RMSprop(learning_rate=lr_schedule)
        #optimizer = keras.optimizers.Lion(learning_rate=lr_schedule)
        optimizer = keras.optimizers.Adadelta(learning_rate=1.0)

        all_losses={}
        all_metrics={}
        for par,out in zip(list(y_scaled.columns),Y_outputs):
            all_losses[par+"_output"]=keras.losses.MeanSquaredError(name=par+"_train_error")
            all_metrics[par+"_output"]=keras.metrics.MeanAbsoluteError(name=par+"_error")
            
        model.compile(optimizer = optimizer,loss = all_losses,metrics = all_metrics)
        #model.compile(optimizer = optimizer,loss = {'Y_output':keras.losses.MeanSquaredError(name="train_error")},metrics = {'Y_output':tf.keras.metrics.MeanAbsoluteError(name="error")})
        
        #training process
        trainhist=model.fit(X_train, Y_trains, epochs = nepoch, batch_size = int(npoints/batchsplit)+1 ,validation_data = (X_test, Y_tests), verbose = 0)     
        history=trainhist.history
        if multitrain:
            multitstr="-%d"%multitrain
        else:
            multitstr=""
        
        model.save(ANN_save_folder+"/ANN_param_test_%s%s.keras"%(hyperparstr,multitstr)) 
        print(model.summary())
        del model
    train_duration=time.time()-start_time   
    print("duration required for training: ",train_duration)
    infotuple=(train_duration,gpus[ngpu],preset_parameters,len(y_scaled))
    #print("history elements:",history.keys())
    errs={}
    val_errs={}
    losss={}
    val_losss={}
    for par in list(y_scaled.columns):
        errs[par] = history[par+'_output_'+par+'_error']
        val_errs[par] = history['val_'+par+'_output_'+par+'_error']
        losss[par] = history[par+'_output_loss']
        val_losss[par] = history['val_'+par+'_output_loss']
        
    epochs_range = range(nepoch)
    cmap = mpl.colormaps['plasma']
    parlist=list(y_scaled.columns)
    colors = cmap(np.linspace(0, 1, len(parlist)))
    coldict={}
    for c,p in zip(colors,parlist):
        coldict[p]=c
    legsize=5

    plt.figure(figsize=(10, 10))
    plt.subplot(2, 1, 1)
    n=0
    for par in parlist:
        plt.plot(epochs_range, errs[par], linestyle=":", color=coldict[par], alpha=0.5, label = par+' Training Error')
        plt.plot(epochs_range, val_errs[par], color=coldict[par], label = par+' Validation Error')
    plt.legend(loc = 'lower right', prop={'size':legsize})
    plt.yscale('log')
    plt.xlim(-nepoch*0.05,nepoch*1.2)
    plt.title('Training and Validation Error', fontsize = 15)

    plt.subplot(2, 1, 2)
    for par in parlist:
        plt.plot(epochs_range, losss[par], linestyle=":", alpha=0.5, color=coldict[par], label = par+' Training Loss')
        plt.plot(epochs_range, val_losss[par], color=coldict[par], label = par+' Validation Loss')
    plt.legend(loc = 'upper right', prop={'size':legsize})
    plt.yscale('log')  
    plt.xlim(-nepoch*0.05,nepoch*1.2)
    plt.title('Training and Validation Loss', fontsize = 15)
    plt.subplots_adjust(left=0.06, right=0.98, top=0.92, bottom=0.1)
    
    
    plt.savefig(save_folder+"/ANN_param_train_info_%s%s.png"%(hyperparstr,multitstr),dpi=600)   
    saveresults(save_folder+"/ANN_param_aux_data_%s%s.dat"%(hyperparstr,multitstr),[history, X_train, X_test, y_train, y_test, yscaler, infotuple])
    return
    
def reeval_like(X_data, y_data, X_scaled, y_scaled, Xscaler, yscaler, isintpol, preset_parameters, save_folder, ANN_save_folder, losspar, hyperparamnames, hyperparamcombos, multitrain=False):
    errordict={}
    errerrdict={}
    predictions={}
    truevals={}
    if not multitrain:
        nmulti=2
    else:
        nmulti=multitrain+1    
    for mti in range(1,nmulti):
        predictions[mti]=[]
    for hpc in hyperparamcombos:
        hyperparams={}
        for hpn,hpv in zip(hyperparamnames,hpc):
            hyperparams[hpn]=hpv  
        hyperparstr=getstringfromdict(hyperparams)
        avgerrs=[]
        
        for mti in range(1,nmulti):
            if multitrain:
                multitstr="-%d"%mti
            else:
                multitstr=""
            model = keras.models.load_model(ANN_save_folder+"/ANN_like_test_%s_%s%s.keras"%(losspar,hyperparstr,multitstr)) 
            (history, X_train, X_test, y_train, y_test, infotuple) = loadresults(save_folder+"/ANN_like_aux_data_%s_%s%s.dat"%(losspar,hyperparstr,multitstr))
            y_confirm=yscaler.inverse_transform(y_test)
            if not mti in truevals.keys():                
                truevals[mti]=y_confirm
            evalres=model.predict(X_test)
            del model
            #print(evalres)
            evalresrs=yscaler.inverse_transform(evalres)    
            predictions[mti].append([p[0] for p in list(evalresrs)])
            errs=[]            
            for pr,rr in zip(list(evalresrs),list(y_confirm)): 
                errs.append(abs(pr[0]-rr[0]))
            avgerr=sum(errs)/len(errs)
            print("mti ",mti," average error on Y: ",avgerr)
            avgerrs.append(avgerr)
        avgavgerr=sum(avgerrs)/len(avgerrs)    
        errresiduals=[err-avgavgerr for err in avgerrs]
        avgerrerr=math.sqrt(sum([r**2 for r in errresiduals])/len(errresiduals))
        print(losspar," -- hyperparams ",hyperparstr," average average error on y: ",avgavgerr)
        errordict[avgavgerr]=hyperparams
        errerrdict[avgavgerr]=avgerrerr
        
    for mti in range(1,nmulti):
        avgprederrs=[]
        avgpreds=[]
        avgpredvars=[]
        for prs in zip(*predictions[mti]):
            avgpreds.append(sum(prs)/len(prs))
        for pr,rr in zip(avgpreds,list(truevals[mti])):
            avgprederrs.append(abs(pr-rr[0]))
        avgprederr=sum(avgprederrs)/len(avgprederrs)
        for pr in zip(*predictions[mti],avgpreds):
            residuals=[pr[i]-pr[-1] for i in range(len(pr)-1)]
            avgpredvars.append(math.sqrt(sum([r**2 for r in residuals]))/len(residuals))
        avgpredvar=sum(avgpredvars)/len(avgpredvars)
        avgpred=sum(avgpreds)/len(avgpreds)
        print("mti ",mti," average error for averaged prediction: ",avgprederr)
        print("mti ",mti," average variance of prediction: ",avgpredvar, " ; maximum variance:",max(avgpredvars))
        print("mti ",mti," average value of prediction: ",avgpred, " ; maximum value:",max(avgpreds))
        print("--------------------------------------------------------------------")
    return errordict,errerrdict
   
def checktrainingexist_like(y_data,hyperparams,save_folder,ANN_save_folder, losspar, preset_parameters,nmulti):    
    hyperparstr=getstringfromdict(hyperparams)
    if nmulti>0:
        multitstr="-%d"%nmulti
    else:
        multitstr=""
    filename=ANN_save_folder+"/ANN_like_test_%s_%s%s.keras"%(losspar,hyperparstr,multitstr)
    if not os.path.isfile(filename):
        print("found no saved training file")
        return False
    (history, X_train, X_test, y_train, y_test, infotuple) = loadresults(save_folder+"/ANN_like_aux_data_%s_%s%s.dat"%(losspar,hyperparstr,multitstr))
    if len(infotuple)>2:
        prepar=infotuple[2]
    else:
        print("found saved training file, but it is an older format") 
        return False
    if not prepar==preset_parameters:
        print("found saved training file, but it is for different preset parameters") 
        return False
    if len(infotuple)>3:
        npoints=infotuple[3]
    if len(y_data)==npoints:
        print("found saved training file with same number of datapoints")
        return True
    else:
        print("found saved training file, but it has a different number of datapoints (",npoints," vs ",len(y_data),")")
        return False
   
def checktrainingexist_param(Y_data,hyperparams,save_folder,ANN_save_folder,preset_parameters,nmulti):    
    hyperparstr=getstringfromdict(hyperparams)
    if nmulti>0:
        multitstr="-%d"%nmulti
    else:
        multitstr=""
    filename=ANN_save_folder+"/ANN_param_test_%s%s.keras"%(hyperparstr,multitstr)
    if not os.path.isfile(filename):
        print("found no saved training file")
        return False
    (history, X_train, X_test, y_train, y_test, yscaler, infotuple) = loadresults(save_folder+"/ANN_param_aux_data_%s%s.dat"%(hyperparstr,multitstr))
    if len(infotuple)>2:
        prepar=infotuple[2]
    else:
        print("found saved training file, but it is an older format") 
        return False
    if not prepar==preset_parameters:
        print("found saved training file, but it is for different preset parameters") 
        return False
    if len(infotuple)>3:
        npoints=infotuple[3]
    if len(Y_data)==npoints:
        print("found saved training file with same number of datapoints")
        return True
    else:
        print("found saved training file, but it has a different number of datapoints (",npoints," vs ",len(Y_data),")")
        return False
        
        
        
   
def reeval_param(Y_data,hyperparams,save_folder,ANN_save_folder,preset_parameters, multitrain=False):    
    hyperparstr=getstringfromdict(hyperparams)
    parnames=list(Y_data.columns)
    avgerrdict={}
    residualdict={}
    predictdict={}
    truedict={}
    avgavgerrs=[]
    if not multitrain:
        nmulti=2
    else:
        nmulti=multitrain+1
        
    for mti in range(1,nmulti):
        residualdict[mti]=[]
        predictdict[mti]=[]
        truedict[mti]=[]
        if multitrain:
            multitstr="-%d"%mti
        else:
            multitstr=""
        model = keras.models.load_model(ANN_save_folder+"/ANN_param_test_%s%s.keras"%(hyperparstr,multitstr))    
        (history, X_train, X_test, y_train, y_test, yscaler, infotuple) = loadresults(save_folder+"/ANN_param_aux_data_%s%s.dat"%(hyperparstr,multitstr))
        if preset_parameters!=None:
            for pp in list(preset_parameters.keys()):
                y_test.insert(parnames.index(pp),column=pp,value=0)        
        y_confirm=yscaler.inverse_transform(y_test)
               
        evalres=model.predict(X_test)
        if preset_parameters!=None:
            for pp in list(preset_parameters.keys()):
                evalres.insert(parnames.index(pp), evalres[0])
        evalresmod=np.array([[ev[i][0] for i in range(len(ev))] for ev in evalres]).T
        evalresrs=yscaler.inverse_transform(evalresmod)
            
        errs=[]
        n=0        
        for pr,rr in zip(list(evalresrs),list(y_confirm)): 
            n=n+1
            #print(n,"-----------------------")
            #print(list(pr))
            #print(list(rr.round(4)))            
            residualdict[mti].append(pr-rr)
            predictdict[mti].append(pr)
            truedict[mti].append(rr)
        #avgrr=sum(truedict[mti])/len(truedict[mti])
        medrr=np.median(truedict[mti])
        for r in residualdict[mti]:
            errs.append(abs(r)/medrr)
        avgerrs=sum(errs)/len(errs)
        if preset_parameters!=None:
            for pp in list(preset_parameters.keys()):
                avgerrs[parnames.index(pp)]=0.0        
        print("average fraction errors on Y: ")
        for pn,er in zip(list(Y_data.columns),list(avgerrs)):
            if not pn in avgerrdict.keys():
                avgerrdict[pn]=[]  
            avgerrdict[pn].append(er)
            print(pn,er)        
        avgerr=sum(avgerrs)/len(avgerrs)
        avgavgerrs.append(avgerr)
    avgavgerr=sum(avgavgerrs)/len(avgavgerrs)
    errresiduals=[err-avgavgerr for err in avgavgerrs]
    avgerrerr=math.sqrt(sum([r**2 for r in errresiduals])/len(errresiduals))
    del model
    plotparamresiduals(hyperparstr,parnames,preset_parameters,residualdict,predictdict,truedict,save_folder)
    return avgavgerr,avgerrerr,avgerrdict
    
def plotparamresiduals(hyperparstr,parnames,preset_parameters,residualdict,predictdict,truedict,save_folder):
    totallsts={}
    for pn in parnames:
        totallsts[pn]=[[],[],[]]
    for mti in sorted(residualdict.keys()):
        multitstr="-%d"%mti
        fig = plt.figure(figsize=(15,8))
        fig.patch.set_facecolor('white')
        axs=[]
        taxs=[]
        for pn,np in zip(parnames,list(range(len(parnames)))):
            if pn in preset_parameters.keys():
                continue
            lsts=[[a[np] for a in residualdict[mti]],[a[np] for a in predictdict[mti]],[a[np] for a in truedict[mti]]]
            totallsts[pn]=[totallsts[pn][i]+lsts[i] for i in range(3)]
            axs.append(fig.add_subplot(4,5,np+1))
            plotdisthistos(lsts,axs[-1])
            axs[-1].title.set_text(pn)
            taxs.append(axs[-1].twiny())
            plotreshistos(lsts,taxs[-1])
            #axs[-1].set_xlabel("", fontsize=20)
            #axs[-1].set_ylabel("number of samples", fontsize=20)
        fig.tight_layout()
        plt.savefig(save_folder+'/ANN_param_residualplot_%s%s.png'%(hyperparstr,multitstr),dpi=600)  
        plt.close(fig)
        del fig
    fig = plt.figure(figsize=(15,8))
    fig.patch.set_facecolor('white')
    axs=[]
    taxs=[]
    for pn,np in zip(parnames,list(range(len(parnames)))):
        if pn in preset_parameters.keys():
                continue
        #print(pn,len(totallsts[pn]))
        axs.append(fig.add_subplot(4,5,np+1))
        plotdisthistos(totallsts[pn],axs[-1])
        axs[-1].title.set_text(pn)
        taxs.append(axs[-1].twiny())
        plotreshistos(totallsts[pn],taxs[-1])
    fig.tight_layout()
    plt.savefig(save_folder+'/ANN_param_residualplot_%s%s.png'%(hyperparstr,"total"),dpi=600)  
    plt.close(fig)
    del fig
    
def plotdisthistos(lsts,ax):
    mini = np.min(lsts[1]+lsts[2])
    maxi = np.max(lsts[1]+lsts[2])
    colors=["m","r","g"]
    for lst,col in zip(lsts[1:],colors[1:]):   
        n, bins, patches = ax.hist(lst, 100, range=(mini, maxi), facecolor=col, alpha=0.5, density=False)
    
def plotreshistos(lsts,ax):
    mini = np.min(lsts[0])
    maxi = np.max(lsts[0])   
    n, bins, patches = ax.hist(lsts[0], 100, range=(mini, maxi), facecolor="m", alpha=0.5, density=False)
    
    

def getrandommodel(X_data, y_data, X_scaled, y_scaled, Xscaler, yscaler, isintpol, preset_parameters, save_folder,ntry=10): 
    model = keras.models.load_model(save_folder+"/ANN_like_test.keras")
        
    best_point,best_like=get_best_point(X_data, y_data, isintpol)
    
    best_point_scaled=pd.DataFrame(Xscaler.transform(best_point.copy()), columns=best_point.columns)
    
    if preset_parameters!=None:
        presence = [item in X_scaled.columns for item in list(preset_parameters.keys())]
        for i, present in enumerate(presence):
            if not present: logging.warning(f"There is no parameter {list(preset_parameters.keys())[i]} in data which could be preset!")
        X_scaled = X_scaled.drop(columns=list(preset_parameters.keys()))
        best_point_scaled = best_point_scaled.drop(columns=list(preset_parameters.keys()))
        
    parnames=best_point_scaled.columns
    #print(parnames)
    foundnewpoint=False
    n=0
    while n<ntry:
        n=n+1
        
        randmods=[[best_point_scaled[p].iloc[0]+random.gauss(-0.01,0.01) for p in parnames] for i in range(int(1e6))]
            
        evalmods=pd.DataFrame(randmods, columns=best_point_scaled.columns)
        
        
        prediction=yscaler.inverse_transform(model.predict(evalmods))
        best_pred_ind=np.argmin(prediction)
        best_pred=prediction[best_pred_ind]
        print("best prediction: ",best_pred," at index: ",best_pred_ind)
        if best_pred<best_like:
            print("found point with better predicted like (",best_pred,") than current best point (",best_like,")")     
            new_best_point_scaled=evalmods.iloc[[best_pred_ind]]
            #print(new_best_point_scaled)
            #print(best_point_scaled)
            if preset_parameters!=None: 
                for column, value in preset_parameters.items():
                    new_best_point_scaled[column] = 0.0
            new_best_point=pd.DataFrame(Xscaler.inverse_transform(new_best_point_scaled), columns=best_point.columns)   
            foundnewpoint=True
            break
    if foundnewpoint:            
        new_best_point=new_best_point.round(4)
        for col_name, value in new_best_point.iloc[0].items():
            if value < 0.0001: new_best_point[col_name]=0.0001
        if preset_parameters!=None: 
            for column, value in preset_parameters.items():
                new_best_point[column] = round(max(0.0001,float(value)), 4)
                
        print(new_best_point)
        return True,new_best_point,best_pred
    else:
        return False,None,None
    
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
                if " starting prefit" in output:             # read out current simulation number
                    match = re.search(r"\d+", output)
                    if match: filenumber = int(match.group())
    
            if output == "" and process.poll() is not None: break   # if there is no output and no further communication, end the fitting
            if time.time() - start_time > 300: raise TimeoutError("No processable communication for > 5 minutes. Terminated simulation fitting!")
    if filenumber == None:         
        logging.warning("No new simulation number could be obtained. Two conflicting requests trying to fit likely. Waiting random time before next request.")
        time.sleep(random.randint(0, 300))      
    return filenumber

def example3():


    data_path = "./ENB2012_data.csv"

    df = pd.read_csv(data_path)
 
    #Train test split
    x_train, x_test = train_test_split(df, test_size = 0.2)

    #train values
    Y1_train = np.array(x_train["Y1"])
    Y2_train = np.array(x_train["Y2"])

    #test values
    Y1_test = np.array(x_test["Y1"])
    Y2_test = np.array(x_test["Y2"])

    #remove the target values from the dataset
    x_train = x_train.drop(["Y1","Y2"], axis = 1)
    x_test = x_test.drop(["Y1","Y2"], axis = 1)

    #Normalizing the data set
    x_train_norm = (x_train-x_train.mean())/x_train.std()
    x_test_norm = (x_test-x_test.mean())/x_test.std()
        
    #show the first 5 rows
    print(df.head())
    # defining layers
    input_layer = layers.Input(shape=(len(x_train.columns),))
    dense_layer_1 = layers.Dense(units = 128, activation = "relu")(input_layer) 
    dense_layer_2 = layers.Dense(units = 128, activation = "relu")(dense_layer_1)
    dense_layer_3 = layers.Dense(units = 64, activation = "relu")(dense_layer_2)

    #Y1 output
    y1_output = layers.Dense(units = 1, activation = "linear", name = "y1_output")(dense_layer_2)

    #Y2 output
    y2_output = layers.Dense(units = 1, activation = "linear", name = "y2_output")(dense_layer_3)

    #Define the model with the input layer and a list of outputs
    model = keras.Model(inputs = input_layer, outputs = [y1_output, y2_output])

    #specify the optimizer and compile with the loss function for both outputs
    optimizer = tf.keras.optimizers.SGD(learning_rate=0.001)

    model.compile(optimizer = optimizer,loss = {'y1_output':'mse', 'y2_output':'mse'},metrics = {'y1_output':tf.keras.metrics.RootMeanSquaredError(),'y2_output':tf.keras.metrics.RootMeanSquaredError()})
    #plot_model(model, show_shapes = True)
    #training process
    model.fit(x_train_norm, (Y1_train, Y2_train), epochs = 2000, batch_size = 10,validation_data = (x_test_norm, (Y1_test, Y2_test)), verbose = 2)
    return

def example2():
    dataframe = pd.read_csv("./heart.csv")
    print(dataframe.shape)
    print(dataframe.head())
    val_dataframe = dataframe.sample(frac=0.2, random_state=1337)
    train_dataframe = dataframe.drop(val_dataframe.index)

    print("Using %d samples for training and %d for validation"% (len(train_dataframe), len(val_dataframe)))
    
    train_ds = dataframe_to_dataset(train_dataframe)
    val_ds = dataframe_to_dataset(val_dataframe)
    for x, y in train_ds.take(1):
        print("Input:", x)
        print("Target:", y)
    
    train_ds = train_ds.batch(32)
    val_ds = val_ds.batch(32)
    
    # Categorical features encoded as integers
    sex = keras.Input(shape=(1,), name="sex", dtype="int64")
    cp = keras.Input(shape=(1,), name="cp", dtype="int64")
    fbs = keras.Input(shape=(1,), name="fbs", dtype="int64")
    restecg = keras.Input(shape=(1,), name="restecg", dtype="int64")
    exang = keras.Input(shape=(1,), name="exang", dtype="int64")
    ca = keras.Input(shape=(1,), name="ca", dtype="int64")

    # Categorical feature encoded as string
    thal = keras.Input(shape=(1,), name="thal", dtype="string")

    # Numerical features
    age = keras.Input(shape=(1,), name="age")
    trestbps = keras.Input(shape=(1,), name="trestbps")
    chol = keras.Input(shape=(1,), name="chol")
    thalach = keras.Input(shape=(1,), name="thalach")
    oldpeak = keras.Input(shape=(1,), name="oldpeak")
    slope = keras.Input(shape=(1,), name="slope")

    all_inputs = [sex,cp,fbs,restecg,exang,ca,thal,age,trestbps,chol,thalach,oldpeak,slope]

    # Integer categorical features
    sex_encoded = encode_categorical_feature(sex, "sex", train_ds, False)
    cp_encoded = encode_categorical_feature(cp, "cp", train_ds, False)
    fbs_encoded = encode_categorical_feature(fbs, "fbs", train_ds, False)
    restecg_encoded = encode_categorical_feature(restecg, "restecg", train_ds, False)
    exang_encoded = encode_categorical_feature(exang, "exang", train_ds, False)
    ca_encoded = encode_categorical_feature(ca, "ca", train_ds, False)

    # String categorical features
    thal_encoded = encode_categorical_feature(thal, "thal", train_ds, True)

    # Numerical features
    age_encoded = encode_numerical_feature(age, "age", train_ds)
    trestbps_encoded = encode_numerical_feature(trestbps, "trestbps", train_ds)
    chol_encoded = encode_numerical_feature(chol, "chol", train_ds)
    thalach_encoded = encode_numerical_feature(thalach, "thalach", train_ds)
    oldpeak_encoded = encode_numerical_feature(oldpeak, "oldpeak", train_ds)
    slope_encoded = encode_numerical_feature(slope, "slope", train_ds)

    all_features = layers.concatenate([sex_encoded,cp_encoded,fbs_encoded,restecg_encoded,exang_encoded,slope_encoded,ca_encoded,thal_encoded,age_encoded,trestbps_encoded,chol_encoded,thalach_encoded,oldpeak_encoded])
    x = layers.Dense(32, activation="relu")(all_features)
    x = layers.Dropout(0.5)(x)
    output = layers.Dense(1, activation="sigmoid")(x)
    model = keras.Model(all_inputs, output)
    model.compile("adam", "binary_crossentropy", metrics=["accuracy"])
    #keras.utils.plot_model(model, show_shapes=True, rankdir="LR")
    
    model.fit(train_ds, epochs=50, validation_data=val_ds)
    return

def example1():

    mnist = tf.keras.datasets.mnist

    (x_train, y_train), (x_test, y_test) = mnist.load_data()
    x_train, x_test = x_train / 255.0, x_test / 255.0

    model = tf.keras.models.Sequential([tf.keras.layers.Flatten(input_shape=(28, 28)),tf.keras.layers.Dense(128, activation='relu'),tf.keras.layers.Dropout(0.2),tf.keras.layers.Dense(10)])

    predictions = model(x_train[:1]).numpy()
    print(predictions)
    
    tf.nn.softmax(predictions).numpy()

    loss_fn = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)

    loss_fn(y_train[:1], predictions).numpy()

    model.compile(optimizer='adam',loss=loss_fn,metrics=['accuracy'])

    model.fit(x_train, y_train, epochs=5)

    model.evaluate(x_test,  y_test, verbose=2)

    probability_model = tf.keras.Sequential([model,tf.keras.layers.Softmax()])

    print(probability_model(x_test[:5]))

def dataframe_to_dataset(dataframe):
    dataframe = dataframe.copy()
    labels = dataframe.pop("target")
    ds = tf.data.Dataset.from_tensor_slices((dict(dataframe), labels))
    ds = ds.shuffle(buffer_size=len(dataframe))
    return ds

def encode_numerical_feature(feature, name, dataset):
    # Create a Normalization layer for our feature
    normalizer = Normalization()

    # Prepare a Dataset that only yields our feature
    feature_ds = dataset.map(lambda x, y: x[name])
    feature_ds = feature_ds.map(lambda x: tf.expand_dims(x, -1))

    # Learn the statistics of the data
    normalizer.adapt(feature_ds)

    # Normalize the input feature
    encoded_feature = normalizer(feature)
    return encoded_feature

def encode_categorical_feature(feature, name, dataset, is_string):
    lookup_class = StringLookup if is_string else IntegerLookup
    # Create a lookup layer which will turn strings into integer indices
    lookup = lookup_class(output_mode="binary")

    # Prepare a Dataset that only yields our feature
    feature_ds = dataset.map(lambda x, y: x[name])
    feature_ds = feature_ds.map(lambda x: tf.expand_dims(x, -1))

    # Learn the set of possible string values and assign them a fixed integer index
    lookup.adapt(feature_ds)

    # Turn the string input into integer indices
    encoded_feature = lookup(feature)
    return encoded_feature

  

def saveresults(rfn,results):
    sfile=open(rfn,'wb')   
    pickle.dump(results, sfile,protocol=-1)
    sfile.close

def loadresults(rfn):
    sfile=open(rfn,'rb')   
    loadthing=pickle.load(sfile)
    sfile.close
    return loadthing
    
    


if __name__ == '__main__':
    multiprocessing.set_start_method('spawn')
    sys.exit(main())    
