""" SAR module with a function to retrieve radar parameters at a
given location.
"""
import numpy as np

from nansat.nansat import Nansat

def calc_vv(s0hh, inc):
    """ Calculate VV pol NRCS.

    Parameters
    ==========
    s0hh : float
        Real valued NRCS in HH polarisation.
    inc : float
        Radar look incidence angle.
    """
    # PR from Lin Ren, Jingsong Yang, Alexis Mouche, et al. (2017) [remote sensing]
    PR = np.square(1.+2.*np.square(np.tan(inc*np.pi/180.))) / \
            np.square(1.+1.3*np.square(np.tan(inc*np.pi/180.)))
    return s0hh*PR # assuming real values (not dB)...

def symfunc(inc):
    """ Symmetric equation for incidence angle of 30 degrees from
    Topouzelis et al. (2016), eq. (7).

    Parameters
    ==========
    inc : float
        Radar look incidence angle.
    """
    return 0.776*inc - 31.638

def normalize_nrcs(s0, inc):
    """ Normalize the NRCS to 30 degrees incidence angle, following
    Topouzelis et al. (2016), eq. (3). 

    Parameters
    ==========
    s0 : float
        NRCS in dB.
    inc : float
        Radar look incidence angle.
    """
    return (s0 + symfunc(inc))/2.

def find_nearest_value(arr, val):
    """ Element in nd array `arr` closest to the scalar value `val`

    Parameters
    ==========
    arr : nd array
    val : scalar value
    """
    idx = np.abs(arr - val).argmin()
    return arr.flat[idx]

def find_nearest_index(arr, val):
    """ Index of element in nd array `arr` closest to the scalar value `val`

    Parameters
    ==========
    arr : nd array
    val : scalar value
    """
    idx = np.abs(arr - val).argmin()
    return idx

def crop_sar_data(n, station_lon, station_lat, epsilon):
    """ Crop Nansat object to fit into given longitude/latitude limit
    
    Parameters
    ==========
    n : Nansat object 
    epsilon : float
        width/height of the new image (measured from the center)
    station_lon : float
        if provided, longitude of the station around which the image will be cropped.
    station_lat : float
        if provided, latitue of the station around which the image will be cropped.
        
    """
    lonlim=[station_lon - epsilon, station_lon + epsilon]
    latlim=[station_lat - epsilon, station_lat + epsilon]
    
    n.crop_lonlat(lonlim=lonlim, latlim=latlim)
    

def sar_params(sar_fn, station_lon=None, station_lat=None, normalize=True, vv=True, epsilon=0.0005):
    """ Estimate SAR parameters at given location.

    Parameters
    ==========
    sar_fn : string
        Full path to SAR dataset.
    station_lon : float, optional
        if provided, longitude of the station around which the image will be cropped.
    station_lat : float, optional
        if provided, latitue of the station around which the image will be cropped.    
    normalize : bool, optional
        True (default) if the NRCS should be normalized to 30 degrees
        incidence angle, currently following Topouzelis et al. (2016),
        eqs. (3) and (7).
    vv : bool, optional
        True (default) if HH polarized NRCS should be converted to VV
        polarization.

    Returns
    =======
    s0 : float
        NRCS [dB] of the cropped object.
    inc : float
        Radar look incidence angle of the cropped object.
    az : float
        Radar look azimuth of the cropped object.
    grid_lons : array of floats
        Geographical longitudes in degrees of the cropped object.
    grid_lats : array of floats
        Geographical latitudes in degrees of the cropped object.
    pol : string
        Radar polarization.

    """
    s0, inc, az, pol = None, None, None, None

    n = Nansat(sar_fn)
    
    if station_lon and station_lat:
        crop_sar_data(n, station_lon, station_lat, epsilon)

    # Find band number of real valued HH or VV polarization NRCS
    try:
        band_no = n.get_band_number({
            'standard_name': 'surface_backwards_scattering_coefficient_of_radar_wave',
            'polarization': 'HH',
            'dataType': '6',})
    except ValueError:
        band_no = n.get_band_number({
            'standard_name': 'surface_backwards_scattering_coefficient_of_radar_wave',
            'polarization': 'VV',
            'dataType': '6',})

    pol = n.get_metadata(key='polarization', band_id=band_no)

    # Get NRCS, incidence angle, and sensor azimuth angle
    s0 = n[band_no]
    inc = n['incidence_angle']
    az = n['look_direction']

    # Calculate VV polarization
    if pol=='HH' and vv:
        s0 = calc_vv(s0, inc)

    # NRCS in decibel
    s0 = 10.*np.log10(s0)

    if normalize:
        # Normalize NRCS
        s0 = normalize_nrcs(s0, inc)

    grid_lons, grid_lats = n.get_geolocation_grids()

    return s0, inc, az, grid_lons, grid_lats, pol
