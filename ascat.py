"""
TODO:

From files in '/lustre/storeB/project/IT/geout/machine-ocean/data_raw/metop', after collocating the data:

- extract sigma0_trip_fore for the three beams (fore, mid, aft) from the pixel overlaying the buoy.
- extract also lat, long, azi_angle_trip_fore, 'inc_angle_trip_fore'
"""

import xarray as xr
import numpy as np


def ascat_params(ascat_fn, station_lon, station_lat):
    """ Estimate SAR parameters at given location.

    Parameters
    ==========
    ascat_fn : string
        Full path to ASCAT dataset.
    station_lon : float
        Longitude (in degrees) of the station where ASCAT parameters are retrieved.
    station_lat : float
        Latitue (in degrees) of the station where ASCAT parameters are retrieved.            
        

    Returns
    =======
    ascat_params_dict : dictionary with ASCAT data.
        The dictionary contains the following keys:
        sigma0_trip_fore : float
            NRCS [dB] over the buoy from the fore beam.
        sigma0_trip_mid : float
            NRCS [dB] over the buoy from the mid beam.
        sigma0_trip_aft : float
            NRCS [dB] over the buoy from the aft beam.    
        inc_angle_trip_fore : float
            Satellite look incidence angle over the buoy from the fore beam.
        inc_angle_trip_mid : float
            Satellite look incidence angle over the buoy from the mid beam.
        inc_angle_aft_fore : float
            Satellite look incidence angle over the buoy from the aft beam.    
        azi_angle_trip_fore : float
            Satellite look azimuth angle over the buoy from the fore beam.
        azi_angle_trip_mid : float
            Satellite look azimuth angle over the buoy from the mid beam.
        azi_angle_aft_fore : float
            Satellite look azimuth angle over the buoy from the aft beam.
        grid_lons_orig : array of floats
            Geographical longitudes in degrees of the original image.
        grid_lats_orig : array of floats
            Geographical latitudes in degrees of the original image.
    """
    
    # Load the image data
    data = xr.open_dataset(ascat_fn)
    
    # Fill in dict with parameters from the image
    ascat_params_dict = {}
    ascat_params_dict['grid_lats_orig'] = data.lat.values
    ascat_params_dict['grid_lons_orig'] = data.lon.values
    
    list_of_params = [
        'sigma0_trip_fore', 'sigma0_trip_mid', 'sigma0_trip_aft',
        'azi_angle_trip_fore', 'azi_angle_trip_mid', 'azi_angle_trip_aft',
        'inc_angle_trip_fore', 'inc_angle_trip_mid', 'inc_angle_trip_aft',
        'start_sensing_time',
        'stop_sensing_time'
    ]
    
    data_station = data.sel(lat=station_lat, lon=station_lon,  method='nearest')
    
    for param in list_of_params:
        if param == 'start_sensing_time':
            ascat_params_dict[param] = data_station.start_sensing_time  # Attr
        elif param == 'stop_sensing_time':
            ascat_params_dict[param] = data_station.stop_sensing_time  # Attr
        else:    
            ascat_params_dict[param] = data_station[param].values.item()  # Var

    return ascat_params_dict


def ascat_params_cnn(ascat_fn, station_lon:float, station_lat:float, nx:int=17, ny:int=17):
    """ Estimate SAR parameters at given location.

    Parameters
    ==========
    ascat_fn : string
        Full path to SAR dataset.
    station_lon : float
        Longitude (in degrees) of the station around which the image will be cropped.
    station_lat : float
        Latitue (in degrees) of the station around which the image will be cropped. 
    nx : float
        Number of pixel in the longitude dimension of the cropped image.
    ny : float
        Number of pixel in the latitude dimension of the cropped image.

    Returns
    =======
    ascat_params_dict : dictionary with ASCAT data.
        The dictionary contains the following keys:
        sigma0_trip_fore : float
            NRCS [dB] over the buoy from the fore beam.
        sigma0_trip_mid : float
            NRCS [dB] over the buoy from the mid beam.
        sigma0_trip_aft : float
            NRCS [dB] over the buoy from the aft beam.    
        inc_angle_trip_fore : float
            Satellite look incidence angle over the buoy from the fore beam.
        inc_angle_trip_mid : float
            Satellite look incidence angle over the buoy from the mid beam.
        inc_angle_aft_fore : float
            Satellite look incidence angle over the buoy from the aft beam.    
        azi_angle_trip_fore : float
            Satellite look azimuth angle over the buoy from the fore beam.
        azi_angle_trip_mid : float
            Satellite look azimuth angle over the buoy from the mid beam.
        azi_angle_aft_fore : float
            Satellite look azimuth angle over the buoy from the aft beam.
        grid_lons_orig : array of floats
            Geographical longitudes in degrees of the original image.
        grid_lats_orig : array of floats
            Geographical latitudes in degrees of the original image.
        lons_cropped_image : array of floats
            Geographical longitudes in degrees of the cropeed image.
        lats_cropped_image : array of floats
            Geographical latitudes in degrees of the cropeed image.
    """
    
    # Load the image data
    ascat = xr.open_dataset(ascat_fn)
    
    # Fill in dict with parameters from the image
    ascat_params_dict = {}
    ascat_params_dict['grid_lats_orig'] = ascat.lat.values
    ascat_params_dict['grid_lons_orig'] = ascat.lon.values
    
    list_of_params = [
        'sigma0_trip_fore', 'sigma0_trip_mid', 'sigma0_trip_aft',
        'azi_angle_trip_fore', 'azi_angle_trip_mid', 'azi_angle_trip_aft',
        'inc_angle_trip_fore', 'inc_angle_trip_mid', 'inc_angle_trip_aft',
        'start_sensing_time',
        'stop_sensing_time'
    ]
    
    
    # Get the latitude and the logitude of the nearest grid box in ASCAT to the station
    ascat_station = ascat.sel(lat=station_lat, lon=station_lon, method='nearest')
    
    # Get the indices of the nearest grid box in ASCAT to the station
    lon_i, lat_i = np.nonzero(
        xr.where(
            (ascat.lon==ascat_station.lon.values) & (ascat.lat==ascat_station.lat.values), 1, 0
        ).data
    )
    
    # How many grid boxes on each side of the nearest station grid box
    if divmod(nx, 2)==0:
        nx2 = nx/2
    else:
        nx2 = (nx - 1)/2
        
    if divmod(ny, 2)==0:
        ny2 = ny/2
    else:
        ny2 = (ny - 1)/2

    cropped_image = ascat.isel(lat=slice(lat_i[0] - ny2, lat_i[0] + ny2 + 1), lon=slice(lon_i[0] - nx2, lon_i[0] + nx2 + 1))
    
    ascat_params_dict['lats_cropped_image'] = cropped_image['lat'].values
    ascat_params_dict['lons_cropped_image'] = cropped_image['lon'].values
    
    for param in list_of_params:
        if param == 'start_sensing_time':
            ascat_params_dict[param] = cropped_image.start_sensing_time  # Attr
        elif param == 'stop_sensing_time':
            ascat_params_dict[param] = cropped_image.stop_sensing_time  # Attr
        else:    
            ascat_params_dict[param] = cropped_image[param].values  # Var

    return ascat_params_dict


def ascat_params_mean_nxn(ascat_fn, station_lon:float, station_lat:float, nx:int=17, ny:int=17):
    """ Estimate SAR parameters at given location.

    Parameters
    ==========
    ascat_fn : string
        Full path to SAR dataset.
    station_lon : float
        Longitude (in degrees) of the station around which the image will be cropped.
    station_lat : float
        Latitue (in degrees) of the station around which the image will be cropped. 
    nx : float
        Number of pixel in the longitude dimension of the cropped image.
    ny : float
        Number of pixel in the latitude dimension of the cropped image.

    Returns
    =======
    ascat_params_dict : dictionary with ASCAT data.
        The dictionary contains the following keys:
        sigma0_trip_fore : float
            NRCS [dB] over the buoy from the fore beam.
        sigma0_trip_mid : float
            NRCS [dB] over the buoy from the mid beam.
        sigma0_trip_aft : float
            NRCS [dB] over the buoy from the aft beam.    
        inc_angle_trip_fore : float
            Satellite look incidence angle over the buoy from the fore beam.
        inc_angle_trip_mid : float
            Satellite look incidence angle over the buoy from the mid beam.
        inc_angle_aft_fore : float
            Satellite look incidence angle over the buoy from the aft beam.    
        azi_angle_trip_fore : float
            Satellite look azimuth angle over the buoy from the fore beam.
        azi_angle_trip_mid : float
            Satellite look azimuth angle over the buoy from the mid beam.
        azi_angle_aft_fore : float
            Satellite look azimuth angle over the buoy from the aft beam.
        grid_lons_orig : array of floats
            Geographical longitudes in degrees of the original image.
        grid_lats_orig : array of floats
            Geographical latitudes in degrees of the original image.
        lons_cropped_image : array of floats
            Geographical longitudes in degrees of the cropeed image.
        lats_cropped_image : array of floats
            Geographical latitudes in degrees of the cropeed image.
    """
    
    # Load the image data
    ascat = xr.open_dataset(ascat_fn)
    
    # Fill in dict with parameters from the image
    ascat_params_dict = {}
    ascat_params_dict['grid_lats_orig'] = ascat.lat.values
    ascat_params_dict['grid_lons_orig'] = ascat.lon.values
    
    list_of_params = [
        'sigma0_trip_fore', 'sigma0_trip_mid', 'sigma0_trip_aft',
        'azi_angle_trip_fore', 'azi_angle_trip_mid', 'azi_angle_trip_aft',
        'inc_angle_trip_fore', 'inc_angle_trip_mid', 'inc_angle_trip_aft',
        'start_sensing_time',
        'stop_sensing_time'
    ]
    
    
    # Get the latitude and the logitude of the nearest grid box in ASCAT to the station
    ascat_station = ascat.sel(lat=station_lat, lon=station_lon, method='nearest')
    
    # Get the indices of the nearest grid box in ASCAT to the station
    lon_i, lat_i = np.nonzero(
        xr.where(
            (ascat.lon==ascat_station.lon.values) & (ascat.lat==ascat_station.lat.values), 1, 0
        ).data
    )
    
    # How many grid boxes on each side of the nearest station grid box
    if divmod(nx, 2)==0:
        nx2 = nx/2
    else:
        nx2 = (nx - 1)/2
        
    if divmod(ny, 2)==0:
        ny2 = ny/2
    else:
        ny2 = (ny - 1)/2

    cropped_image = ascat.isel(
        lat=slice(int(lat_i[0] - ny2), int(lat_i[0] + ny2 + 1)), 
        lon=slice(int(lon_i[0] - nx2), int(lon_i[0] + nx2 + 1))
    )
    
    ascat_params_dict['lats_cropped_image'] = cropped_image['lat'].values
    ascat_params_dict['lons_cropped_image'] = cropped_image['lon'].values
    
    for param in list_of_params:
        if param == 'start_sensing_time':
            ascat_params_dict[param] = cropped_image.start_sensing_time  # Attr
        elif param == 'stop_sensing_time':
            ascat_params_dict[param] = cropped_image.stop_sensing_time  # Attr
        else:    
            ascat_params_dict[param] = np.nanmean(cropped_image[param].values)  # Var

    return ascat_params_dict


def ascat_params_gradient_nxn(ascat_fn, station_lon:float, station_lat:float, nx:int=17, ny:int=17):
    """ Estimate SAR parameters at given location.

    Parameters
    ==========
    ascat_fn : string
        Full path to SAR dataset.
    station_lon : float
        Longitude (in degrees) of the station around which the image will be cropped.
    station_lat : float
        Latitue (in degrees) of the station around which the image will be cropped. 
    nx : float
        Number of pixel in the longitude dimension of the cropped image.
    ny : float
        Number of pixel in the latitude dimension of the cropped image.

    Returns
    =======
    ascat_params_dict : dictionary with ASCAT data.
        The dictionary contains the following keys:
        sigma0_trip_fore : float
            NRCS [dB] over the buoy from the fore beam.
        sigma0_trip_mid : float
            NRCS [dB] over the buoy from the mid beam.
        sigma0_trip_aft : float
            NRCS [dB] over the buoy from the aft beam.    
        inc_angle_trip_fore : float
            Satellite look incidence angle over the buoy from the fore beam.
        inc_angle_trip_mid : float
            Satellite look incidence angle over the buoy from the mid beam.
        inc_angle_aft_fore : float
            Satellite look incidence angle over the buoy from the aft beam.    
        azi_angle_trip_fore : float
            Satellite look azimuth angle over the buoy from the fore beam.
        azi_angle_trip_mid : float
            Satellite look azimuth angle over the buoy from the mid beam.
        azi_angle_aft_fore : float
            Satellite look azimuth angle over the buoy from the aft beam.
        grid_lons_orig : array of floats
            Geographical longitudes in degrees of the original image.
        grid_lats_orig : array of floats
            Geographical latitudes in degrees of the original image.
        lons_cropped_image : array of floats
            Geographical longitudes in degrees of the cropeed image.
        lats_cropped_image : array of floats
            Geographical latitudes in degrees of the cropeed image.
    """
    
    # Load the image data
    ascat = xr.open_dataset(ascat_fn)
    
    # Fill in dict with parameters from the image
    ascat_params_dict = {}
    ascat_params_dict['grid_lats_orig'] = ascat.lat.values
    ascat_params_dict['grid_lons_orig'] = ascat.lon.values
    
    list_of_params = [
        'sigma0_trip_fore', 'sigma0_trip_mid', 'sigma0_trip_aft',
        'azi_angle_trip_fore', 'azi_angle_trip_mid', 'azi_angle_trip_aft',
        'inc_angle_trip_fore', 'inc_angle_trip_mid', 'inc_angle_trip_aft',
        'start_sensing_time',
        'stop_sensing_time'
    ]
    
    
    # Get the latitude and the logitude of the nearest grid box in ASCAT to the station
    ascat_station = ascat.sel(lat=station_lat, lon=station_lon, method='nearest')
    
    # Get the indices of the nearest grid box in ASCAT to the station
    lon_i, lat_i = np.nonzero(
        xr.where(
            (ascat.lon==ascat_station.lon.values) & (ascat.lat==ascat_station.lat.values), 1, 0
        ).data
    )
    
    # How many grid boxes on each side of the nearest station grid box
    if divmod(nx, 2)==0:
        nx2 = nx/2
    else:
        nx2 = (nx - 1)/2
        
    if divmod(ny, 2)==0:
        ny2 = ny/2
    else:
        ny2 = (ny - 1)/2

    cropped_image = ascat.isel(
        lat=slice(int(lat_i[0] - ny2), int(lat_i[0] + ny2 + 1)), 
        lon=slice(int(lon_i[0] - nx2), int(lon_i[0] + nx2 + 1))
    )
    
    ascat_params_dict['lats_cropped_image'] = cropped_image['lat'].values
    ascat_params_dict['lons_cropped_image'] = cropped_image['lon'].values
    
    for param in list_of_params:
        if param == 'start_sensing_time':
            ascat_params_dict[param] = cropped_image.start_sensing_time  # Attr
        elif param == 'stop_sensing_time':
            ascat_params_dict[param] = cropped_image.stop_sensing_time  # Attr
        elif (param == 'sigma0_trip_fore') or (param == 'sigma0_trip_mid') or (param == 'sigma0_trip_aft'):
            ascat_params_dict[param + '_x'] = (cropped_image[param][int(ny2), -1] - cropped_image[param][int(ny2), 0])
            ascat_params_dict[param + '_y'] = (cropped_image[param][-1, int(nx2)] - cropped_image[param][0, int(nx2)])
        else:    
            ascat_params_dict[param] = ascat_station[param].values  # Var

    return ascat_params_dict

