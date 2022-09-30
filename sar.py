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

def sar_params(sar_fn, longitude, latitude, normalize=True, vv=True):
    """ Estimate SAR parameters at given location.

    Parameters
    ==========
    sar_fn : string
        Full path to SAR dataset.
    longitude : float
        Geographical longitude in degrees.
    latitude : float
        Geographical latitude in degrees.
    normalize : bool
        True (default) if the NRCS should be normalized to 30 degrees
        incidence angle, currently following Topouzelis et al. (2016),
        eqs. (3) and (7).
    vv : bool
        True (default) if HH polarized NRCS should be converted to VV
        polarization.

    Returns
    =======
    s0 : float
        NRCS [dB] at given location.
    inc : float
        Radar look incidence angle at given location.
    az : float
        Radar look azimuth angle at given location.
    pol : string
        Radar polarization.

    """
    s0, inc, az, pol = None, None, None, None

    n = Nansat(sar_fn)

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

    lon, lat = n.get_geolocation_grids()

    # Find pixels at desired location (input longitude and latitude variables)

    return s0, inc, az, pol
