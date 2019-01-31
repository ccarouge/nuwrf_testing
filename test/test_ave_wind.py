import xarray as xr
import pandas as pd 
import numpy as np
import CCRC_diags_calc.CCRC_diags_calc as mc

# Create test data
XTIME = xr.DataArray(pd.date_range(start='2000-01-01 00:00:00', \
                                   end='2000-01-01 00:30:00',   \
                                   freq="3min"),dims='Time')
XLONG = xr.DataArray([60,61],dims='west_east')
XLAT  = xr.DataArray([20,21],dims='south_north')
uv10 = xr.DataArray(np.zeros((XTIME.size,2,2)), \
                    dims=('Time','south_north','west_east'),     \
                    coords={'XTIME':XTIME,'XLONG':XLONG,'XLAT':XLAT})

uv10[0:11,0,0] = range(15,26)
uv10[0:11,0,1] = range(16,27)
uv10[0:11,1,0] = range(1,12)
uv10[0:11,1,1] = range(2,13)
uv10 = uv10*3*60
def test_average_wind_multi():
    within_period = 3
    ave_w = mc.average_wind(uv10,6,3*60,within_period)
    np.testing.assert_almost_equal(ave_w[within_period-2,0,0].values, 15.5)
    np.testing.assert_almost_equal(ave_w[within_period-2,1,0].values, 1.5)

def test_average_wind_nomulti():
    within_period = 3    
    ave_w = mc.average_wind(uv10,5,3*60,within_period)
    ave1 = (uv10[0,0,0]+uv10[1,0,0]*2/3)/(5*60)
    np.testing.assert_almost_equal(ave_w[within_period-2,0,0].values, ave1)

def test_time_extra_0():
    trem = mc.time_extra(uv10[0:3,:,:],3*60.,6)
    assert(trem == 0)

def test_time_extra_x():
    '''Need some time from the last timestep'''
    trem = mc.time_extra(uv10[0:3,:,:],3*60.,5)
    assert(trem == 60.0)

def test_ntimestep():
    ds = uv10.to_dataset(name="Fake")
    wp = mc.ntimestep_in_diag(ds,5)
    assert(wp == 3)

def test_ntimestep_0():
    ds = uv10.to_dataset(name="Fake")
    wp = mc.ntimestep_in_diag(ds,9)
    assert(wp == 4)