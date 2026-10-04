# %%
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import pickle
import yaml
import os
import re
import math
import getpass

# %%
def load_datapath(filepath):
    with open(filepath, "r") as file:
        config = yaml.safe_load(file)
    return config["paths"]["progress_dir"]

# %%
def load_data(folder):
    # loads most previous data with given settings from folder 
    with open(os.path.join(folder, "data.pkl"), "rb") as file:
        save_data = pickle.load(file)
        points = save_data["points"]
        momenta = save_data["momenta"]
        losses = save_data["losses"]
        gradients = save_data["gradients"]
    return points, momenta, losses, gradients

# %%
def get_magnitudes(momentum_list):
    magnitude_list = []
    for p in momentum_list:
        magnitude_list.append(np.linalg.norm(p.values, axis=1)[0])
    return magnitude_list

# %%
def create_trajectoryPairplots(points, folder):
    points = pd.concat(points, ignore_index=True)
    
    d=len(points.columns)
    num_plots = math.ceil(d/2)
    fig, axes = plt.subplots(math.ceil(num_plots/3), 3, figsize=(16, 4*math.ceil(num_plots/3)))
    
    for i in range(math.ceil(num_plots/3)):
        for j in range(3):
            ax = axes[i, j]
            cur_d = (i*3+j)*2
            if cur_d < d-1:
                dim1 = points.columns[cur_d]
                dim2 = points.columns[cur_d+1]
                ax.plot(points[dim1], points[dim2], marker="o", linestyle="--")
                ax.plot(points[dim1][0], points[dim2][0], marker="o", linestyle="--", color="r")
                ax.set_xlabel(dim1)
                ax.set_ylabel(dim2)
            elif cur_d < d:
                dim1 = points.columns[cur_d]
                dim2 = points.columns[0]
                ax.plot(points[dim1], points[dim2], marker="o", linestyle="--")
                ax.plot(points[dim1][0], points[dim2][0], marker="o", linestyle="--", color="r")
                ax.set_xlabel(dim1)
                ax.set_ylabel(dim2)
    plt.suptitle(os.path.basename(folder))      
    plt.tight_layout() 
    plt.savefig(os.path.join(folder, "plots/trajectoryPairplots.png"))      
    plt.close()

# %%
def create_lossCurve(momentum_list, loss_list, gradient_list, folder):
    # loss_list[0]=loss_list[0].item()
    momentum_magnitudes = get_magnitudes(momentum_list)
    if not len([m for m in momentum_magnitudes if m > 0.0]) > 0:
        momentum_magnitudes=[]
    gradient_magnitudes = get_magnitudes(gradient_list)
    n = max(len(momentum_magnitudes), len(gradient_magnitudes), len(loss_list))
    steps = [i for i in range(0, n)]
    
    pattern = r"lr(\d+\.\d+)"
    match = re.search(pattern, os.path.basename(folder))
    if match: learning_rate = float(match.group(1))
    else: learning_rate = 1
    gradient_magnitudes = [mag*learning_rate for mag in gradient_magnitudes]
        
    
    
    fig, (ax1, ax2) = plt.subplots(2,1, sharex=True, figsize=(8,6))
      
    ax1.plot(steps[:len(loss_list)], loss_list, "o-", label="loss parameter", color="b")
    ax1.plot([0,len(loss_list)], [loss_list[0],loss_list[0]], "--", label="best loss at start", color="k", linewidth=0.5, alpha=0.6)
    ax1.grid(True)
    ax1.set_ylabel("Neg. Log-Likelihood")
    ax1.legend()
        
    #if len(momentum_magnitudes)>0:
    #    ax2.plot(steps, momentum_magnitudes, "o--", label="Momentum", color="r")
    ax2.grid(True)
    ax2.plot(steps[:len(gradient_magnitudes)], gradient_magnitudes, "o--", label="Gradient (scaled by LR)", color="g")
    ax2.set_xlabel("Gradient Descent Steps")
    ax2.set_ylabel("Vector Magnitude") 
    ax2.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    ax2.xaxis.set_tick_params(top=True)
    ax2.legend()
    
    plt.suptitle(os.path.basename(folder))
    plt.tight_layout()
    plt.savefig(os.path.join(folder, "plots/lossMomentumCurve.png")) 
    plt.close()

def create_lossCurves(momentum_lists, loss_lists, gradient_lists, pips,folder, maxsteps=False):
    infodict={}
    infodict[32] = ["max -log(p)","Exponential"]
    infodict[44] = ["max -log(p)","No"]
    infodict[48] = ["sl","Distance"]
    infodict[49] = ["sl","Exponential"]
    infodict[53] = ["sum -log(p)","No"]
    infodict[54] = ["sum -log(p)","Distance"]
    infodict[46] = ["max -log(p)","Distance"]
    infodict[47] = ["sl","No"]
    infodict[45] = ["sum -log(p)","Exponential"]
    colors=["darkcyan","orange","magenta"]
    fig, ax1 = plt.subplots(1,1, sharex=True, figsize=(8,4.5))
    n = max([len(ll)for ll in loss_lists])
    if maxsteps:
        n=min(n,maxsteps+1)
    steps = [i for i in range(0, n)]
    ax1.plot([0,n], [loss_lists[0][0],loss_lists[0][0]], "--", label="best loss at start", color="r", linewidth=0.7, alpha=0.8)
    
    for loss_list,color,ip in zip(loss_lists,colors,pips):
        print(ip)
        info=infodict[ip]
        m=min(len(loss_list),n)
        ax1.plot(steps[:m], loss_list[:m], "o--", label="Loss parameter %s ; %s weights"%(info[0],info[1]), color=color)
        
    ax1.grid(True)
    ax1.set_ylabel("Neg. Log-Likelihood")
    ax1.legend()    
    plt.tight_layout()
    plt.savefig(os.path.join(folder, "plots/combiLossMomentumCurve.png"))     
    print("saved in ",folder)
    plt.close()


# %%
def create_plots(path,ips,maxsteps):
    folders = [os.path.join(path,f) for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]
    folderinfodict={}
    for folder in folders:
        folderdate=None
        folderIP=0
        if os.path.isfile(os.path.join(folder, "output.log")):
            for line in open(os.path.join(folder, "output.log")).readlines():
                if "load_previous" in line:
                    folderdate=line.partition(" INFO")[0]
                    folderIP=int((line.partition("'simulation_IP': ")[2]).partition(",")[0])    
                    break
            if not "IP"+str(folderIP)+"_" in folder:
                IPfolder=folder.rpartition("/")[0]+"/IP"+str(folderIP)+"_"+folder.rpartition("/")[2]
                if os.path.exists(IPfolder):
                    IPdata=os.path.join(IPfolder, "data.pkl")
                    Rdata=os.path.join(folder, "data.pkl")
                    IPlog=os.path.join(IPfolder, "output.log")
                    Rlog=os.path.join(folder, "output.log")
                    if os.path.isfile(Rdata) and os.path.isfile(IPdata):   
                        if os.path.getmtime(Rdata) > os.path.getmtime(IPdata):
                            os.system ("cp "+Rdata+" "+IPdata)
                    elif os.path.isfile(Rdata):
                        os.system ("mv "+Rdata+" "+IPdata)
                    if os.path.isfile(Rlog) and os.path.isfile(IPlog):   
                        if os.path.getmtime(Rlog) > os.path.getmtime(IPlog):
                            os.system ("cp "+Rlog+" "+IPlog)
                    elif os.path.isfile(Rlog):
                        os.system ("mv "+Rlog+" "+IPlog)
                    os.system("rm -r "+folder)           
                elif not os.path.exists(IPfolder):
                    os.system("mv "+folder+" "+IPfolder)
                    print(folder+"\nmoved to\n"+IPfolder)                    
                else:
                    os.system("rm -r "+folder)  
                folderinfodict[folderdate]=[IPfolder,folderIP]    
            elif folderIP==0:
                os.system("rm -r "+folder)  
            else:            
                folderinfodict[folderdate]=[folder,folderIP]
            
    point_lists=[]
    momentum_lists=[]
    loss_lists=[]
    gradient_lists=[]
    pips=[]
    pfolders=[]
    for folderdate in reversed(sorted(folderinfodict.keys())):           
        folderinfo=folderinfodict[folderdate]
        folder=folderinfo[0]        
        os.system("touch "+folder)
        folderip=folderinfo[1]        
        if not os.path.exists(folder):
            continue
        if os.path.isfile(os.path.join(folder, "data.pkl")):            
            point_list, momentum_list, loss_list, gradient_list = load_data(folder)
            if folderip in ips:
                point_lists.append(point_list)
                momentum_lists.append(momentum_list)
                loss_lists.append(loss_list)
                gradient_lists.append(gradient_list)
                ips.remove(folderip)
                pips.append(folderip)
                pfolders.append(folder)
            os.system("touch "+folder)
            if len(point_list) > 0:
                if not os.path.exists(os.path.join(folder, "plots")): os.mkdir(os.path.join(folder, "plots"))   
                create_lossCurve(momentum_list, loss_list, gradient_list, folder)
                create_trajectoryPairplots(point_list, folder)
        else:
            os.system("rm -r "+folder)      
    print(pips)
    create_lossCurves(momentum_lists, loss_lists, gradient_lists, pips , pfolders[0], maxsteps)

# %%
def main():
    nplots=int(sys.argv[1])
    ips=[]
    for i in range(nplots):
        ips.append(int(sys.argv[i+2]))
    if len(sys.argv)>nplots+2:
        maxsteps=int(sys.argv[nplots+2])
        print("maxsteps: ",maxsteps)
    else:
        maxsteps=False
    config_filepath = f"/home/{getpass.getuser()}/CALETana/prop/GradientDescent/config.yaml"
    data_path = load_datapath(config_filepath)
    # data_path = "/home/ehanser/CALETana/MLProject/GradientDescent/DescentData copy" 
    create_plots(data_path,ips,maxsteps)
    

# %%
if __name__=="__main__":
    main()
