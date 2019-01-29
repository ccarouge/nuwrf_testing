import xarray as xr
import numpy as np 
import wrf
import netCDF4 as nc
import time
import sys

def time_extra(uv10,diag):
    '''Calculate how much of the last time step is needed to cover the diag period'''
    trem = ((uv10.XTIME[-1]-uv10.XTIME[0])-np.timedelta64(diag,'m'))/np.timedelta64(1,'s')
    trem = conv_to_int(trem)
    return trem

def average_wind(uv10, diag, dt, within_period):
    '''Calculate the wind speed average over the period needed'''
    ''' From Stackoverflow, first answer: https://stackoverflow.com/questions/48510784/xarray-rolling-mean-with-weights'''
    # Time extra:
    trem = time_extra(uv10, diag)
    # Get a weights array
    #weights = xr.DataArray(np.ones(uv10.sizes['Time']), dims=['window'])
    weights = xr.DataArray(np.ones(within_period), dims=['window'])
    print(weights)
    print("======")
    weights[-1] = (dt-trem)/dt

    # Need to change weights array. Need the fraction at the end of all the windows... 
    ave = uv10.rolling(Time=within_period, center=True).construct('window').dot(weights)
    print(ave)
    print("======")

    return ave

def conv_to_int(var):
    '''To convert 0D xarray to int or float'''
    return var.values.tolist()

def calc_timestep(ds):
    '''Calculate the timestep for this dataset. Assumed constant'''
    tt = ds.XTIME

    # Difference between second and first output time in seconds
    dt = (tt[1]-tt[0])/np.timedelta64(1,'s')
    # Convert to int
    dt = conv_to_int(dt)

    return dt

def ntimestep_in_diag(ds,diag):
    '''Calculate how many timesteps are in the diagnostic period'''

    tt = ds.XTIME
    # Get diag in timedelta format
    diag_timedelta = np.timedelta64(diag,'m')

    # Take the date of the first output and add the diag length, then
    # use where() and count() to find how many timesteps are within this period
    end_time = tt[0] + diag_timedelta

    # Use < and +1 to cover both cases when diag is a multiple of the timestep or not
    within_period = tt.where( tt < end_time ).count() + 1
    within_period = conv_to_int(within_period)

    return within_period

def get_windspeed10(ds):
    '''Calculate wind speed from WRF output dataset'''
    return xr.ufuncs.sqrt(ds.U10**2+ds.V10**2)

def getWRF_output(filename):
    '''Read in WRF output file and add wind speed to the dataset'''

    ds = xr.open_dataset(filename,chunks={'Time':20,'south_north':152,'west_east':223})
    ds['uv10'] = get_windspeed10(ds)
 
    return ds

def main():
    # Read in data and calculate wind speed
    filename="/short/w35/ccc561/WRF/run_nu-wrf_v8/tests_CCRC_diag/coupled_run/wrfout_d01_1999-06-01_00:00:00"
    ds = getWRF_output(filename)

    uv10 = ds.uv10
    print(uv10)
    # Loop through the diagnostics: 5min, 10min, 20min, 30min, 60min
    for diag in [5]:#,10,20,30,60]:

        # Calculate how many time steps per window should be used
        # by comparing the output time step and the length of the diagnostic window
        dt = calc_timestep(ds)

        # Number of timesteps to cover the length of the diagnostic window.
        within_period = ntimestep_in_diag(ds, diag)
        print(within_period)


        # Is the diagnositc period a multiple of the time step or not?
        # Convert diag: minutes -> seconds
        print(type(dt))
        multi = (diag*60)%dt == 0
        print(multi)

        # Function that calculates the average wind for this window.
        ave_w = average_wind(uv10,diag=diag,dt=dt,within_period=within_period)
        # Use rolling() to apply the function to the correct data

        # Calculate the daily max of this average (groupby(day))
if __name__ == "__main__":
    main()
#    filename = "/short/w35/ccc561/WRF/run_nu-wrf_v8/tests_CCRC_diag/coupled_run/wrfout_d01_1999-06-01_00:00:00"
#    ds = getWRF_output(filename)
#    uv10 = ds['uv10']
#    ave_w = average_wind(5,180,uv10[0:3,:,:],True)
