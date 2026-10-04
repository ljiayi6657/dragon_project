import yaml
import subprocess
import concurrent.futures
import queue
import itertools
from copy import deepcopy
import json
import time

def load_config(filepath):
    with open(filepath, "r") as file:
        return yaml.safe_load(file)

def get_configurations(old_config, trial_grid, trial_combos):
    # obtain all grid combinations and add them to the manually given combinations
    if not trial_grid and not trial_combos: raise ValueError("No simulation requests were given")
    
    grid_combos_list = []
    if trial_grid:
        grid_keys = trial_grid.keys()
        grid_values = trial_grid.values()
        grid_combinations = list(itertools.product(*grid_values))
        grid_combos_list = [dict(zip(grid_keys, combination)) for combination in grid_combinations]
    all_combos = grid_combos_list + trial_combos
    
    # obtain the new configuration dictionaries
    new_configs = []
    for combo in all_combos:
        main_config = deepcopy(old_config)
        iter_lowest_level(main_config, combo)
        new_configs.append(main_config)
    return new_configs
    
def iter_lowest_level(old_config, new_combo):
    # recursively analyze old_config until one arrives at lowest dict level, there rewrite values with new_combo values
    if isinstance(old_config, dict):
        for key, value in old_config.items():
            if isinstance(value, dict):
                iter_lowest_level(value, new_combo)
            else:
                for target_key, new_value in new_combo.items():
                    if target_key==key: old_config[key]=new_value               
    else: raise ValueError("Configuration file given doesn't have right format")

def manage_execution(configurations, ips):
    # Create a queue of all configurations to simulated (first in first out)
    config_queue = queue.Queue()
    for config in configurations:
        config_queue.put(config)
        
    # Create a thread manager for as many threads as IPs given
    max_simultaneous_scripts = len(ips)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_simultaneous_scripts) as executor:
        # fill dictionary of thread and configuration it runs on
        future_to_config = {}
        for i in range(max_simultaneous_scripts):
            if not config_queue.empty():
                config = config_queue.get()
                future_to_config[executor.submit(run_script, config, ips[i])] = config
                time.sleep(90)  #wait for submission, so that there is no overlap in calls to fitspectra-xxx
       
        # wait and check for new results as long as configuration queue or thread dictionary are no empty
        while not config_queue.empty() or future_to_config: 
            done, _ = concurrent.futures.wait(future_to_config, return_when=concurrent.futures.FIRST_COMPLETED)
            for future in done:
                config = future_to_config.pop(future)
                try:
                    ip = future.result()
                    print(f"Ended execution for computer: {ip}")
                except Exception as e:
                    print(f"Script failed on computer : {ip}")
                    print(f"Error message: {e.stderr.decode('utf-8')}")
                    
                if not config_queue.empty():
                    new_config = config_queue.get()
                    future_to_config[executor.submit(run_script, new_config, ip)]=new_config
            time.sleep(60)
    
def run_script(config, ip):
    # runs GD.py script with a certain configuration on ip
    iter_lowest_level(config, {"simulation_IP": ip})  #change IP in config_settings
    
    json_arguments = json.dumps(config)
    command = ["python", "GD.py", json_arguments]
    
    print(f"\n{'-'*14} Starting script on computer {ip} with configuration: {'-'*14}\n{config['GD_settings']}\n{config['comp_settings']}\n{'-'*80}\n")
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return_code=process.wait()
        if return_code==0: print(f"Gradient descent finished successfully on computer {ip}")
        else: print(f"Gradient descent failed on computer {ip}")
        _, stderr = process.communicate()
        if stderr: print("\033[91mFollowing errors occured:\033[0m\n", stderr.decode("utf-8"))
    except subprocess.CalledProcessError as e:
        print(f"Script execution failed with return code {e.returncode}")
        print(f"Error message: {e.stderr.decode('utf-8')}")
    return ip

def main():
    available_computers = [48, 49]      # List all computer IPs to which you want to submit tasks, dragon has to running on them!
    
    #------------- Submission Option A: ------------------ 
    # List all trial parameters that differ from each other or the settings in the "config.yaml" file as "param":[trials], e.g "degree":[2,3,4] in the dictionary below
    # take combinations of given parameters and submit them (all other params will be taken from original "config.yaml" file; IPs are adjusted automaticcal)
    trial_grid = {        
        "n_closest_points": ["Global", 1000],
        "weighting": ["None"],
        "learning_rate": [0.002]
    } 
    #------------- Submission Option B: ------------------ 
    # List all specific trial parameter combinations as dictionaries in below's list, e.g. [{"par1":val}, {"par2":val, "par3":val}, ...]
    trial_combos = [
        #{"n_closest_points": "Global", "weighting": "None", "learning_rate": 0.01}
        
        # {"run_mode": "Local", "weighting":"Exponential", "degree": 2, "alpha": 0.14, "learning_rate": 0.009}, #Momentum mode comparison
        # {"run_mode": "Global", "weighting":"Exponential", "degree": 2, "alpha": 0.09, "learning_rate": 0.011}, #Momentum mode comparison
        # {"run_mode": "Global", "degree": 2, "alpha": 0.04123, "learning_rate": 0.011}, #weighting comparison
        # {"run_mode": "Global", "fit_mode":"Auto", "learning_rate": 0.011}, # Auto fit comparison
        # {"run_mode": "Global", "weighting":"Exponential", "fit_mode":"Auto", "learning_rate": 0.011}, # weighting comparison with autofit
        # {"run_mode": "Global", "degree": 3, "alpha": 0.4824, "learning_rate": 0.011}, #degree comparison
        # {"run_mode": "Global", "fit_mode":"Auto", "learning_rate": 0.011, "momentum_decay": 0.25}, #decay comparison
        # {"run_mode": "Global", "fit_mode":"Auto", "learning_rate": 0.011, "momentum_decay": 0.1}, #decay comparison
        # {"run_mode": "Global", "fit_mode":"Auto", "learning_rate": 0.011, "momentum_decay": 0.01}, #decay comparison
        # {"run_mode": "Global", "weighting":"Exponential","fit_mode":"Auto", "learning_rate": 0.011, "momentum_decay": 0.1}, #decay comparison
        # {"run_mode": "Local", "fit_mode":"Auto", "learning_rate": 0.009, "momentum_decay": 0.25, "n_closest_points": 1000}, #decay comparison
        # {"run_mode": "Local", "fit_mode":"Auto", "learning_rate": 0.009, "momentum_decay": 0.1, "n_closest_points": 1000}, #decay comparison
        # {"run_mode": "Global", "fit_mode":"Auto", "learning_rate": 0.005}  # learning rate comparison
    ]
    # ------------ IMPORTANT: both of the above submission options are excecuted unless you specifically empty the dictionary/list that you don't want executed 
    
    config_filepath = "config.yaml"
    old_config = load_config(config_filepath)
    new_configs = get_configurations(old_config, trial_grid, trial_combos)
    manage_execution(new_configs, available_computers)

if __name__=="__main__": main()
