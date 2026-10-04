# %% [markdown]
# ### Imports, Loading Model & Defining Optimization

# %%
#Required modules
import math
import pandas as pd
import numpy as np

import matplotlib.pyplot as plt

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

from GD import generate_saveFolderName, load_data, load_interpolation_data, update_data, recenter_data, get_best_point, closest_points, get_distweights, get_expweights

# %% [markdown]
# ### Loading Configuration Files

paramorder=["lowindx","sindex","lowbreak","lowsoft","nuccut","spiralwidth"]+["DR","DE","alvel","convel","diffnorm","diffexp","lowdiffbreak","lowdiffbreaksoft","diffbreak","diffbreaksoft","lowexp","highexp"]

paramstrdict={"lowindx":r'$\gamma_l$',"lowbreak":r'$R_{bi}$',"lowsoft":r'$s_{bi}$',"sindex":r'$\gamma_h$',"nuccut":r'$R_{cut}$',"spiralwidth":r'$w_{sa}$',"DR":r'$r_s$',"DE":r'$z_s$',"diffnorm":r'$D_0$',"diffexp":r'$\delta$',"lowexp":r'$\delta_l$',"lowdiffbreak":r'$R_{bl}$',"lowdiffbreaksoft":r'$s_l$',"highexp":r'$\delta_h$',"diffbreak":r'$R_{bh}$',"diffbreaksoft":r'$s_h$',"alvel":r'$v_a$',"convel":r'$v_c$'}


#"indxscan":"sindex","ncut":"nuccut","deltscan":"diffexp","lowindex":"lowindx","lowdelt":"lowexp","lowdeltbreak":"lowdiffbreak",
#                "lowdbreaksoft":"lowdiffbreaksoft","Dscan":"diffnorm", "diffscaleheight":"DE","diffscaleradius":"DR","reaccscan":"alvel",
#                "highdelt":"highexp","deltbreak":"diffbreak","dbreaksoft":"diffbreaksoft","lowbreak":"lowbreak","lowsoft":"lowsoft","SW":"spiralwidth","convel":"convel"}

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


def get_distances(X_scaled,point):
    X_der = X_scaled.copy().reset_index(drop=True)
    point_der = point.copy().iloc[0]
    distances = np.linalg.norm(X_der-point_der, axis=1)
    return pd.DataFrame(distances,columns=["Distance"])



def create_ParameterSpacePairplots(points, failpoints, point, folder, tag):
    d=len(points.columns)
    num_plots = math.ceil(d/2)
    fig, axes = plt.subplots(math.ceil(num_plots/3), 3, figsize=(16, 4*math.ceil(num_plots/3)))
    
    for i in range(math.ceil(num_plots/3)):
        for j in range(3):
            ax = axes[i, j]
            cur_d = (i*3+j)*2
            if cur_d < d-1:
                dim1 = paramorder[cur_d] #points.columns[cur_d]
                dim2 = paramorder[cur_d+1] #points.columns[cur_d+1]
                ax.plot(failpoints[dim1], failpoints[dim2], marker=".", linestyle="",color="orange")     
                ax.plot(points[dim1], points[dim2], marker=".", linestyle="",color="green")                         
                ax.plot(point[dim1], point[dim2], marker=".", linestyle="",color="r")         
                ax.set_xlabel(paramstrdict[dim1],fontsize=24)
                ax.set_ylabel(paramstrdict[dim2],fontsize=24)                
            elif cur_d < d:
                dim1 = paramorder[cur_d] #points.columns[cur_d]
                dim2 = paramorder[0] #points.columns[0]
                ax.plot(failpoints[dim1], failpoints[dim2], marker=".", linestyle="",color="orange")  
                ax.plot(points[dim1], points[dim2], marker=".", linestyle="",color="green")                 
                ax.plot(point[dim1], point[dim2], marker=".", linestyle="",color="r")         
                ax.set_xlabel(paramstrdict[dim1],fontsize=24)
                ax.set_ylabel(paramstrdict[dim2],fontsize=24)
    #plt.suptitle(os.path.basename(folder))      
    plt.tight_layout() 
    plt.savefig(os.path.join(folder, "ParameterSpacePairplots-%s.png"%tag))      
    plt.close()
# %%


def create_ParameterSpacePairplot(points, point, folder, tag, dim1, dim2):
    fig, ax = plt.subplots(1, 1, figsize=(6, 4))
    
    
    ax.plot(points[dim1], points[dim2], marker=".", linestyle="")     
    ax.plot(point[dim1], point[dim2], marker=".", linestyle="",color="r")         
    ax.set_xlabel(paramstrdict[dim1])
    ax.set_ylabel(paramstrdict[dim2])

    #plt.suptitle(os.path.basename(folder))      
    plt.tight_layout() 
    plt.savefig(os.path.join(folder, "ParameterSpacePairplot-%s-%s-%s.png"%(tag,dim1,dim2)))      
    plt.close()


def create_LossDistanceplot(loss, distances, folder, tag, useweights=False, weights=None):
    
    fig, ax = plt.subplots(1, 1, figsize=(8, 4.5))
    dim1 = distances.columns[0]
    dim2 = loss.columns[0]
    if useweights:
        dim3 = weights.columns[0]
        sc=ax.scatter(distances[dim1], loss[dim2], c=weights[dim3], marker=".", cmap="cool")
        cbar = fig.colorbar(sc)
        cbar.set_label("weight", loc='top')
    else:
        ax.scatter(distances[dim1], loss[dim2], marker=".")
    #ax.plot(distances[dim1], loss[dim2], marker=".", linestyle="")     
    #ax.plot(point[dim1], point[dim2], marker=".", linestyle="",color="r")         
    ax.set_ylabel("loss parameter (neg. log. likelihood)")
    ax.set_xlabel("distance from best point")
         
    #plt.suptitle(os.path.basename(folder))      
    plt.tight_layout() 
    plt.savefig(os.path.join(folder, "LossDistanceplot-%s.png"%tag))      
    plt.close()

def main():
    # Initializing Variables
    # 0. Load settings from "config.yaml" file in same folder as this script and potentially overwrite parameters
    GD_settings, preset_parameters, comp_settings, paths = load_config()
    folder = os.path.join(paths["progress_dir"], "parameterspace")   
    print("folder: ",folder )    
    os.makedirs(folder, exist_ok=True)
    os.system("touch "+folder)
    print("Update and fit potentially new datapoints                                                        ",end = '\r', flush=True)
    new_nfiles=update_data(paths["fitSpectra_path"])
    lossparam=GD_settings["lossparameter"]

    X_data, y_data, X_scaled, y_scaled, Xscaler, yscaler, w_data, isinterpol , X_fault = load_data(paths["dragondata_path"],paths["interpoldata_path"], GD_settings=GD_settings, preset_parameters=preset_parameters)

    point_list, momentum_list, loss_list = get_best_point(X_data, y_data, isinterpol)
    
    point = point_list[-1].copy()
    point_scaled = pd.DataFrame(Xscaler.transform(point), columns=point.columns)
    X_f_scaled = pd.DataFrame(Xscaler.transform(X_fault.copy()), columns=point.columns)
    loss=pd.DataFrame([loss_list[-1]],columns=y_scaled.columns)
    loss_scaled = pd.DataFrame(yscaler.transform(loss.copy()), columns=loss.columns)
    
    create_ParameterSpacePairplots(X_data, X_fault, point, folder, "raw-"+lossparam)
    create_ParameterSpacePairplots(X_scaled, X_f_scaled, point_scaled, folder, "scaled-"+lossparam)
    
    create_ParameterSpacePairplot(X_data, point, folder, "raw-"+lossparam, "diffnorm","diffexp")
    create_ParameterSpacePairplot(X_scaled, point_scaled, folder, "scaled-"+lossparam, "diffnorm","diffexp")
    
    distances=get_distances(X_scaled,point_scaled)
    
    create_LossDistanceplot(y_data,distances, folder,"raw-"+lossparam)
    create_LossDistanceplot(y_scaled,distances, folder,"scaled-"+lossparam)
    
    if GD_settings["force_center"]:
        X_shifted=recenter_data(X_scaled,point_scaled)
        X_f_shifted=recenter_data(X_f_scaled,point_scaled)
        y_shifted=recenter_data(y_scaled,loss_scaled)
        point_shifted=recenter_data(point_scaled,point_scaled)
        
        create_ParameterSpacePairplots(X_shifted, X_f_shifted, point_shifted, folder, "shifted-"+lossparam)
        create_ParameterSpacePairplot(X_shifted, point_shifted, folder, "shifted-"+lossparam, "diffnorm","diffexp")
        create_LossDistanceplot(y_shifted,distances, folder,"shifted-"+lossparam)

        XMMscaler=MaxAbsScaler().fit(X_shifted)
        X_shifted=pd.DataFrame(XMMscaler.transform(X_shifted.copy()),columns=X_shifted.columns)
        X_f_shifted=pd.DataFrame(XMMscaler.transform(X_f_shifted.copy()),columns=X_f_shifted.columns)
        
        create_ParameterSpacePairplots(X_shifted, X_f_shifted, point_shifted, folder, "shifted-rescaled-"+lossparam)
        create_ParameterSpacePairplot(X_shifted, point_shifted, folder, "shifted-rescaled-"+lossparam, "diffnorm","diffexp")
        
        yMMscaler=MaxAbsScaler().fit(y_shifted)
        y_shifted=pd.DataFrame(yMMscaler.transform(y_shifted.copy()),columns=y_shifted.columns)
        
        eweights = get_expweights(y_scaled)
        dweights = get_distweights(X_scaled,point_scaled,int(GD_settings["dist_weight_power"]))       
    
        create_LossDistanceplot(y_shifted,distances, folder,"shifted-rescaled-"+lossparam)
        create_LossDistanceplot(y_shifted,distances, folder,"shifted-rescaled-distweight-"+lossparam, True, dweights)
        create_LossDistanceplot(y_shifted,distances, folder,"shifted-rescaled-expoweight-"+lossparam, True, eweights)

if __name__=="__main__": 
    main()
