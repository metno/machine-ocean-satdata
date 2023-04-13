from sentinelsat import SentinelAPI, geojson_to_wkt

api = SentinelAPI(None, None, "https://scihub.copernicus.eu/dhus", timeout=180)

###########

data_dir = "/lustre/storeB/project/IT/geout/machine-ocean/data_raw/sentinel/oestergarnsholm"

location = [19.053, 57.417]
start_time = "1995-05-22T16:45:00Z"
end_time = "2020-12-31T23:45:00Z"

###########

footprint_json = {
"type": "Feature",
"geometry": {
    "type": "Point",
    "coordinates": location
  }
}
footprint = geojson_to_wkt(footprint_json)

print("Searching {} from {} to {}...".format(footprint, start_time, end_time))

scihub_results = api.query(footprint,
                    date=(start_time, end_time),
                    platformname="Sentinel-1",
                    producttype="GRD")
                    #limit=1,
                    #cloudcoverpercentage=(0, 30))

api.download_all(scihub_results, directory_path=data_dir)
