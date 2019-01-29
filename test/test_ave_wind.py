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

uv10[0:3,0,0] = [15,16,17]
uv10[0:3,0,1] = [16,17,18]
uv10[0:3,1,0] = [1,2,3]
uv10[0:3,1,1] = [2,3,4]
def test_average_wind_multi():
    ave_w = mc.average_wind(5,180,uv10[0:3,:,:],True)
    assert(ave_w[0,0].values == 16)
    assert(ave_w[1,1].values == 3)

def test_average_wind_nomulti():
    print(XTIME.values)
    ave_w = mc.average_wind(5,180,uv10[0:3,:,:],False)
    ave1 = (uv10[0,0,0]+uv10[1,0,0]+2/3*uv10[2,0,0])/3
    np.testing.assert_almost_equal(ave_w[0,0].values, ave1)

def test_time_extra_0():
    trem = mc.time_remainder(uv10[0:4,:,:],9)
    assert(trem == 0)

def test_time_extra_x():
    '''Need some time from the last timestep'''
    trem = mc.time_extra(uv10[0:4,:,:],8)
    assert(trem == 60.0)