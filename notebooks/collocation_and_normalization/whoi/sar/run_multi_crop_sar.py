import pandas as pd
import pickle
from multiprocessing import Pool

from crop_sar import crop_images_one_buoy

data_dir = "/lustre/storeB/project/IT/geout/machine-ocean/data_raw/sentinel/"

# in_situ_obs_with_sar_params is a copy of in_situ_obs and is filled with sar params.
with open(data_dir + 'in_situ_obs_with_sar_params.pickle', 'rb') as handle:
        in_situ_obs = pickle.load(handle)
    
n_processes = len(in_situ_obs.keys())
with Pool(n_processes) as pool: 
    results = pool.map(crop_images_one_buoy, in_situ_obs.keys())
    
    
    

