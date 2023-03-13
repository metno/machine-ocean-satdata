#!/usr/bin/env python
"""
This script downloads ASCAT data. See ascat_sandbox notebook for details.

TODO:
1 use more (EUMETSAT) users and do parallel dl (DO NOT OVERWRITE pickle)
2 find limits for parallell customisations and dl's?
3 -> MT code
"""

import eumdac
import time
import fnmatch
import shutil
import pickle

####

productname = "Pioneer_6"
data_dir = "/lustre/storeB/project/IT/geout/machine-ocean/data_raw/metop/"

####

# Insert your personal key and secret into the single quotes
consumer_key = 'vnGFm2AvkAxC7RpbNrY5UP50uj8a'
consumer_secret = 'bLfPiNANHxfGbi3_5NI9CG4014Ua'

credentials = (consumer_key, consumer_secret)

token = eumdac.AccessToken(credentials)
print(f"This token '{token}' expires {token.expiration}")

####

with open('in_situ_obs_ascat_with_customisations.pickle', 'rb') as handle:
    in_situ_obs = pickle.load(handle)

####

datatailor = eumdac.DataTailor(token)

chain = eumdac.tailor_models.Chain(
     product='ASCATL1SZR',
     format='netcdf4',
     projection='geographic'
)

####

in_situ_obs[productname]["customisations"] = []
in_situ_obs[productname]["nc_files"] = []

print("Running customisations and downloading nc-files")

for product in in_situ_obs[productname]["products"]:
    customisation = datatailor.new_customisation(product, chain)
    customisation # By calling the newly created customisation we will start the customisation process
    
    jobID= customisation._id
    print(f"Started customisation process {jobID}", end="")
    
    in_situ_obs[productname]["customisations"].append(customisation)
    
    status = "QUEUED"
    sleep_time = 60 # seconds

    # Customisation Loop
    while status == "QUEUED" or status == "RUNNING":
        # Get the status of the ongoing customisation
        status = customisation.status

        if "DONE" in status:
            #print(f"SUCCESS")
            print(".", end="")
            break
        elif "ERROR" in status or 'KILLED' in status:
            #print(f"UNSUCCESS, exiting")
            print("...UNSUCCESS...", end="")
            break
        elif "QUEUED" in status:
            #print(f"QUEUED")
            print(".", end="")
        elif "RUNNING" in status:
            #print(f"RUNNING")
            print(".", end="")
        elif "INACTIVE" in status:
            sleep_time = max(60*10, sleep_time*2)
            print(f"INACTIVE, doubling status polling time to {sleep_time} (max 10 mins)")
        time.sleep(sleep_time)
    
    print(f"...finished")
    
    if len(customisation.outputs) < 1:
        print("...NO FILES AVAILABLE FOR DOWNLOADING...", end="")
    else:
        nc, = fnmatch.filter(customisation.outputs, '*.nc')

        jobID= customisation._id
        print(f"\tStarting to download the NetCDF output of the customisation {jobID}", end="")

        with customisation.stream_output(nc,) as stream, \
                open(data_dir + stream.name, mode='wb') as fdst:
            in_situ_obs[productname]["nc_files"].append(stream.name)
            shutil.copyfileobj(stream, fdst)

    print(f"...finished")
    print(f'\tDeleting completed customisation {customisation} from {customisation.creation_time} UTC.')
    customisation.delete()

print("All customisations completed and nc-files downloaded!")

# pickle dict with customisations
with open('in_situ_obs_ascat_with_customisations.pickle', 'wb') as handle:
        pickle.dump(in_situ_obs, handle, protocol=pickle.HIGHEST_PROTOCOL)
