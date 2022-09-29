import pytest

from sar import sar_params

sar_fn = (
    '/lustre/storeB/project/IT/geout/machine-ocean/data_raw/sentinel/'
    'S1A_IW_GRDH_1SDV_20220925T171246_20220925T171311_045164_0565E1_358E.SAFE')

@pytest.mark.sar
def test_sar():
    """ Test that method sar_params returns the correct data.
    """
    location = [5.0, 65.0]

    s0norm, s0, inc, az = sar_params(sar_fn, location[0], location[1])
