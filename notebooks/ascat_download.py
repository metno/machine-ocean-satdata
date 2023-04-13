#!/usr/bin/env python
"""
This script downloads ASCAT data. See ascat_sandbox notebook for details.

TODO:
1 use more (EUMETSAT) users and do parallel dl (DO NOT OVERWRITE pickle)
2 find limits for parallell customisations and dl's? <- 20 GB max limit for customisations
3 -> MT code
"""

import eumdac
import time
import requests
import fnmatch
import shutil
import pickle
import sys

####

productname = "Pioneer_5"
data_dir = "/lustre/storeB/project/IT/geout/machine-ocean/data_raw/metop/"

####

# Insert your personal key and secret into the single quotes
consumer_key = 'KEY'
consumer_secret = 'SECRET'

credentials = (consumer_key, consumer_secret)

token = eumdac.AccessToken(credentials)
try:
    print(f"This token '{token}' expires {token.expiration}")
except requests.exceptions.HTTPError as error:
    print(f"Error when trying the request to the server: '{error}'")
    sys.exit(-1)

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

if "nc_files" not in in_situ_obs[productname].keys():
    in_situ_obs[productname]["nc_files"] = {}

print("Running customisations and downloading nc-files")

for product in in_situ_obs[productname]["products"]:
    # do not process products that are already downloaded
    if str(product) in in_situ_obs[productname]["nc_files"].keys():
        print(f"Product already processed and downloaded...skipping!")
        continue        
    
    try:
        customisation = datatailor.new_customisation(product, chain)
        print(f"Customisation {customisation._id} started.")
    except eumdac.datatailor.DataTailorError as error:
        print(f"Error related to the Data Tailor: '{error.msg}'")
        break
    except eumdac.EumdacError as error:
        print("Unexpected eumdac error:", error)
        break
    except requests.exceptions.HTTPError as error:
        print(f"HTTP error: '{error.msg}'")
        break
    except requests.exceptions.RequestException as error:
        print(f"Unexpected error: {error}")
        break

    status = "QUEUED"
    sleep_time = 10 # seconds

    # Customisation Loop
    while status:
        # Get the status of the ongoing customisation
        try:
            jobID = customisation._id
            status = customisation.status
        except eumdac.customisation.CustomisationError as error:
            print(f"Data Tailor Error", error)
            break
        except eumdac.EumdacError as error:
            print("Unexpected eumdac error:", error)
            break
        except requests.exceptions.HTTPError as error:
            print(f"HTTP error: '{error.msg}'")
            break
        except requests.exceptions.RequestException as error:
            print(f"Unexpected error: {error}")
            break

        if "DONE" in status:
            print(f"Customisation {jobID} is successfully completed.")
            break
        elif status in ["ERROR","FAILED","DELETED","KILLED","INACTIVE"]:
            print(f"Customisation {jobID} was unsuccessful. Customisation log is printed.\n")
            print(customisation.logfile)
            break
        elif "QUEUED" in status:
            print(f"Customisation {jobID} is queued.")
        elif "RUNNING" in status:
            print(f"Customisation {jobID} is running.")
        time.sleep(sleep_time)
    
    try:
        if len(customisation.outputs) < 1:
            print("...NO FILES AVAILABLE FOR DOWNLOADING...", flush=True)
            continue

        jobID = customisation._id
        print(f"\tStarting to download the NetCDF output of the customisation {jobID}")

        nc, = fnmatch.filter(customisation.outputs, '*.nc')

        with customisation.stream_output(nc,) as stream, \
                open(data_dir + stream.name, mode='wb') as fdst:
            shutil.copyfileobj(stream, fdst)
            in_situ_obs[productname]["nc_files"][str(product)] = stream.name
    except eumdac.customisation.CustomisationError as error:
        print(f"Data Tailor Error", error)
        break
    except eumdac.EumdacError as error:
        print("Unexpected eumdac error:", error)
        break
    except requests.exceptions.HTTPError as error:
        print(f"HTTP error: '{error.msg}'")
        break
    except requests.exceptions.RequestException as error:
        print(f"Unexpected error: {error}")
        break

    print(f"\tDeleting the customisation {jobID}")

    try:
        customisation.delete()
    except eumdac.customisation.CustomisationError as error:
        print("Customisation Error:", error)
        break
    except eumdac.EumdacError as error:
        print("Unexpected eumdac error:", error)
        break
    except requests.exceptions.HTTPError as error:
        print(f"HTTP error: '{error.msg}'")
        break
    except requests.exceptions.RequestException as error:
        print("Unexpected error:", error)
        break

    print(f"\tFinished dowloading the NetCDF output and deleted the customisation {jobID}", flush=True)

print("All customisations done and nc-files downloaded")

# pickle dict with file names
with open('in_situ_obs_ascat_with_customisations.pickle', 'wb') as handle:
        print("Saving dict!")
        pickle.dump(in_situ_obs, handle, protocol=pickle.HIGHEST_PROTOCOL)
