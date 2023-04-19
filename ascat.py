"""
TODO:

From files in '/lustre/storeB/project/IT/geout/machine-ocean/data_raw/metop', after collocating the data:

- extract sigma0_trip_fore for the three beams (fore, mid, aft) from the pixel overlaying the buoy.
- extract also lat, long, azi_angle_trip_fore, 'inc_angle_trip_fore'
"""

import xarray as xr


def ascat_params(ascat_fn, station_lon=None, station_lat=None):
    """ Estimate SAR parameters at given location.

    Parameters
    ==========
    ascat_fn : string
        Full path to SAR dataset.
    station_lon : float, optional
        If provided, longitude (in degrees) of the station around which the image will be cropped.
    station_lat : float, optional
        If provided, latitue (in degrees) of the station around which the image will be cropped.            
        

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
    ]
    
    data_station = data.sel(lat=station_lat, lon=station_lon,  method='nearest')
    
    for param in list_of_params:
        ascat_params_dict[param] = data_station[param].values.item()    

    return ascat_params_dict