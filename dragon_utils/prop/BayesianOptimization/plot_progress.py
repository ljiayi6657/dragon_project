# %%

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
        losses = save_data["losses"]
        bounds = save_data["bounds"]
        init_X = save_data["init_X"]
        init_y = save_data["init_y"]
    return points, losses, bounds, init_X, init_y

# %%
def get_magnitudes(momentum_list):
    magnitude_list = []
    for p in momentum_list:
        magnitude_list.append(np.linalg.norm(p.values, axis=1)[0])
    return magnitude_list

def top_results(X, y, n=1):
    #watch out that X, y have same indexing
    X_der = X.copy().reset_index(drop=True)
    y_der = y.copy().reset_index(drop=True)
    ycolumn = y_der.columns[0]
    top_indices = y_der.sort_values(by=ycolumn, ascending=True).head(n).index.tolist()
    top_y = y_der.loc[top_indices].reset_index(drop=True)
    top_X = X_der.loc[top_indices].reset_index(drop=True)
    return top_X, top_y


# %%
def create_trajectoryPairplots(points, losses, init_X, init_y, bounds, folder):
    points = pd.concat(points, ignore_index=True)
    d=len(points.columns)
    num_plots = math.ceil(d/2)
    fig, axes = plt.subplots(math.ceil(num_plots/3), 3, figsize=(16, 4*math.ceil(num_plots/3)))
    
    best_init_X, _ = top_results(init_X, init_y)
    best_cur_X, _ = top_results(points, pd.DataFrame(losses))
    
    for i in range(math.ceil(num_plots/3)):
        for j in range(3):
            ax = axes[i, j]
            cur_d = (i*3+j)*2
            if cur_d < d-1:
                dim1 = points.columns[cur_d]
                dim2 = points.columns[cur_d+1]
                dim1X = init_X.columns[cur_d]
                dim2X = init_X.columns[cur_d+1]
                
                ax.axvline(x=bounds[cur_d][0], color="black", linestyle="--", linewidth=2)
                ax.axvline(x=bounds[cur_d][1], color="black", linestyle="--", linewidth=2)
                ax.axhline(y=bounds[cur_d+1][0], color="black", linestyle="--", linewidth=2)
                ax.axhline(y=bounds[cur_d+1][1], color="black", linestyle="--", linewidth=2)
                
                ax.scatter(points[dim1], points[dim2], marker="o", color = "r", label="New Points")
                ax.scatter(init_X[dim1X], init_X[dim2X], marker="o", color = "b", label="Previous Points")
                ax.scatter(best_init_X[dim1X], best_init_X[dim2X], marker="*", s=200, color = "b", label="Best Previous Point")
                ax.scatter(best_cur_X[dim1], best_cur_X[dim2], marker="*", s=200, color = "r", label="Best New Guess")
                ax.set_xlabel(dim1X)
                ax.set_ylabel(dim2X)
            else:
                dim1 = points.columns[cur_d]
                dim2 = points.columns[0]
                dim1X = init_X.columns[cur_d]
                dim2X = init_X.columns[0]
                
                ax.axvline(x=bounds[cur_d][0], color="black", linestyle="--", linewidth=2)
                ax.axvline(x=bounds[cur_d][1], color="black", linestyle="--", linewidth=2)
                ax.axhline(y=bounds[0][0], color="black", linestyle="--", linewidth=2)
                ax.axhline(y=bounds[0][1], color="black", linestyle="--", linewidth=2)
                
                ax.scatter(points[dim1], points[dim2], marker="o", color="r", label="New Points")
                ax.scatter(init_X[dim1X], init_X[dim2X], marker="o", color = "b", label="Previous Points")
                ax.scatter(best_init_X[dim1X], best_init_X[dim2X], marker="*", s=200, color = "b", label="Best Previous Point")
                ax.scatter(best_cur_X[dim1], best_cur_X[dim2], marker="*", s=200, color = "r", label="Best New Guess")
                ax.set_xlabel(dim1X)
                ax.set_ylabel(dim2X)
    plt.legend()
    plt.suptitle(os.path.basename(folder))      
    plt.tight_layout() 
    plt.savefig(os.path.join(folder, "plots/trajectoryPairplots.png"))      
    plt.close()

# %%
def create_lossCurve(loss_list, init_y, folder):
    steps = [i for i in range(0, len(loss_list))]

    fig, ax1 = plt.subplots(1,1, sharex=True, figsize=(8,6))
      
    ax1.plot(steps[:len(loss_list)], loss_list, "o--", label="Loss", color="b")
    ax1.plot([0], min(init_y.values), "o--", label="Previous Minimum", color="r")
    ax1.grid(True)
    ax1.set_ylabel("Loss Parameter")
    ax1.legend()

    ax1.set_xlabel("Gradient Descent Steps")

    plt.suptitle(os.path.basename(folder))
    plt.tight_layout()
    plt.savefig(os.path.join(folder, "plots/lossMomentumCurve.png")) 
    plt.close()

# %%
def create_plots(path):
    folders = [os.path.join(path,f) for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]
    for folder in folders:
        if not os.path.exists(os.path.join(folder, "plots")): os.mkdir(os.path.join(folder, "plots"))
        point_list, loss_list, bounds, init_X, init_y = load_data(folder)
    
        create_lossCurve(loss_list, init_y, folder)
        create_trajectoryPairplots(point_list, loss_list, init_X, init_y, bounds, folder)

# %%
def main():
    config_filepath = f"/home/{getpass.getuser()}/CALETana/prop/BayesianOptimization/config.yaml"
    data_path = load_datapath(config_filepath)
    create_plots(data_path)
    

# %%
if __name__=="__main__":
    main()
