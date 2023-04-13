import matplotlib.pyplot as plt
import sys
from nansat import Nansat
import time
import os
import datetime
import pytz
import pickle

os.environ["TZ"] = "UTC"
time.tzset()
utc_timezone = pytz.timezone("UTC")

sys.path.append("../../nansat/")
sys.path.append("../../..")
import sar


##### read pickled imported in-situ measurements metadata with attached colocated Sentinel-1 sat products metadata
# (to avoid having to rerun the API search)

#with open('../../in_situ_obs.pickle', 'rb') as handle:
#    in_situ_obs = pickle.load(handle)
# in_situ_obs_with_sar_params is a copy of in_situ_obs and is filled with sar params.
    
#with open(data_dir + 'in_situ_obs_with_sar_params.pickle', 'rb') as handle:
#    in_situ_obs = pickle.load(handle)

def crop_images_one_buoy(buoy):
    data_dir = "/lustre/storeB/project/IT/geout/machine-ocean/data_raw/sentinel/"
    #for buoy in in_situ_obs.keys():
    with open(data_dir + 'in_situ_obs_with_sar_params.pickle', 'rb') as handle:
        in_situ_obs = pickle.load(handle)
        
    station_lat = in_situ_obs[buoy]['lat'][0]
    station_lon = in_situ_obs[buoy]['lon'][0]
    print(buoy)
    count_products = 0
    count_not_available = 0
    crop_size = [3, 9]
    for product in in_situ_obs[buoy]['products']:
        fname = in_situ_obs[buoy]['products'][product]['filename']
        #n = Nansat(data_dir + fname)
        #grid_lons_original, grid_lats_original = n.get_geolocation_grids()
        #x, y = sar.latlon2xy(grid_lats_original, grid_lons_original, station_lat, station_lon)
        
        if 'sar_params' not in in_situ_obs[buoy]['products'][product]:
            in_situ_obs[buoy]['products'][product]['sar_params'] = {}
        
        for size in crop_size:
            if str(size) not in in_situ_obs[buoy]['products'][product]['sar_params']:
               # try:
                    #print('Getting SAR params...')
                    s0, s0_norm, inc, az, grid_lons, grid_lats, pol = sar.sar_params(
                        sar_fn = data_dir + fname,
                        station_lon=station_lon,
                        station_lat=station_lat,
                        x_size=size,
                        y_size=size
                    )

                    crop_param_dict = {
                        'x_size' : size,
                        'y_size' : size,
                        's0' : s0, 
                        's0_norm' : s0_norm,
                        'inc' : inc,
                        'az' : az,
                        'grid_lons' : grid_lons,
                        'grid_lats' : grid_lats,
                        'pol' : pol
                    }

                    in_situ_obs[buoy]['products'][product]['sar_params'][str(size)] = crop_param_dict
                    count_products = count_products + 1

                    # Save the results every 10 iterations
                    if not count_products % 10:
                        with open(data_dir + 'in_situ_obs_with_sar_params.pickle', 'wb') as handle:
                            pickle.dump(in_situ_obs, handle, protocol=pickle.HIGHEST_PROTOCOL)

                        with open(data_dir + 'in_situ_obs_with_sar_params.pickle', 'rb') as handle:
                            in_situ_obs = pickle.load(handle)

                #except:
                #    print('Buoy ', buoy, 'File ', fname, ' cannot be normalized for size = ', size) # Check if the image exists and if the crop area is within the image
                #    count_not_available = count_not_available - 1
            #else:
            #    print('Buoy ', buoy, 'File ', fname, ' is already normalized for size = ', size)
    
    print('Number of images that were not cropped: ', count_not_available)

#with open(data_dir + 'in_situ_obs_with_sar_params.pickle', 'wb') as handle: 
#    pickle.dump(in_situ_obs, handle, protocol=pickle.HIGHEST_PROTOCOL)
import matplotlib.pyplot as plt
import sys
from nansat import Nansat
import time
