import xarray as xr
import numpy as np 
import wrf
import netCDF4 as nc
import time
import sys

def time_extra(uv10,dt,diag):
    '''Calculate how much of the last time step is needed to cover the diag period'''
    trem = ((uv10.XTIME[-1]-uv10.XTIME[0])-np.timedelta64(diag,'m'))/np.timedelta64(1,'s')

    # Check trem < timestep
    if trem > dt:
        print('Problem calculating time fraction of last time step.')
        print('Fraction left: {}'.format(trem.values))
        print('Time step: {}'.format(dt.values))
    trem = conv_to_int(trem)

    return trem

def get_time_weights(uv10, diag, dt, within_period):
    '''Calculate weights in time for the average.'''
    # Time extra:
    trem = time_extra(uv10[0:within_period], dt, diag)

    # Get a weights array
    weights = xr.DataArray(np.ones(within_period-1), dims=['window'])
    weights[-1] = (dt-trem)/dt

    return weights

def average_wind(uv10, diag, dt, within_period):
    '''Calculate the wind speed average over the period needed'''
    ''' From Stackoverflow, first answer: https://stackoverflow.com/questions/48510784/xarray-rolling-mean-with-weights
    uv10: DataArray with time dimension called "Time"
    diag: Length of the diagnostic window in minutes
    dt: time step of uv10 in seconds
    within_period: number of timesteps within the diag window'''

    weights = get_time_weights(uv10, diag, dt, within_period)

    # Need to change weights array. Need the fraction at the end of all the windows... 
    ave = uv10.rolling(Time=within_period-1, center=False).construct('window').dot(weights)/(diag*60.)

    return ave

def conv_to_int(var):
    '''To convert 0D xarray to int or float'''
    return var.values.tolist()

def calc_timestep(ds):
    '''Calculate the timestep for this dataset. Assumed constant. In seconds'''
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

#    ds = xr.open_dataset(filename,chunks={'south_north':1,'west_east':1})
    ds = xr.open_dataset(filename)
    ds['uv10'] = get_windspeed10(ds)
 
    return ds

def main():
    # Read in data and calculate wind speed
    print("Reading in the data from WRF")
    filename="/g/data/w35/ccc561/nuwrf_testing/wrfout_subset.nc"
    ds = getWRF_output(filename)
    uv10 = ds.uv10
    print(uv10)

    # Read in wrfdly
    filename="/g/data/w35/ccc561/nuwrf_testing/wrfdly_d01_1999-06-01_00:00:00"
#    dl = xr.open_dataset(filename, chunks={'south_north':1,'west_east':1})
    dl = xr.open_dataset(filename)

    # Calculate how many time steps per window should be used
    # by comparing the output time step and the length of the diagnostic window
    dt = calc_timestep(ds)

    # Convert wind speed to wind distance: multiply by dt in seconds
    uv10 = uv10 * dt 

    # Loop through the diagnostics: 5min, 10min, 20min, 30min, 60min
#    for diag in [5,10,20,30,60]:
    for diag in [5]:

        print("Calculate the max. daily wind speed for {} min window".format(diag))
        # Number of timesteps to cover the length of the diagnostic window.
        within_period = ntimestep_in_diag(ds, diag)
        print(within_period)


        # Is the diagnositc period a multiple of the time step or not?
        # Convert diag: minutes -> seconds
        multi = (diag*60)%dt == 0

        # Function that calculates the average wind for this window.
        ave_w = average_wind(uv10,diag=diag,dt=dt,within_period=within_period)
        print("What is going on?")
        print(ave_w[:,0,0])

        # Drop the undefined values and Get the daily max.
        ave_w = ave_w.dropna('Time')
        ave_w.coords['XTIME'] = ave_w.coords['XTIME'] - np.timedelta64(int(dt),'s')
        ave_w = ave_w.groupby('XTIME.dayofyear').max(dim='Time')

        # Get coordinate in date
        date_diag=(np.asarray(['1999','1999'], dtype='datetime64[Y]'))+(np.asarray(ave_w['dayofyear'], dtype='timedelta64[D]')-1)

        # Need to specify which dimension to use for the new coordinates as time doesn't
        # exist in the original DataArray
        ave_w.coords['date'] = (['dayofyear'], date_diag)
        ave_w = ave_w.rename({'dayofyear':'time'})
        ave_w['dayofyear'] = ave_w.coords['time']
        ave_w = ave_w.drop('time')
        ave_w.set_index({'time':'date'},inplace=True)

#        # Compare with daily max from WRF
        print("ave_w")
        print(ave_w)

        print("dl.UV10MAX5")
        print(dl.Times)
        # Calculate the daily max of this average (groupby(day))
if __name__ == "__main__":
    main()
#    filename = "/short/w35/ccc561/WRF/run_nu-wrf_v8/tests_CCRC_diag/coupled_run/wrfout_d01_1999-06-01_00:00:00"
#    ds = getWRF_output(filename)
#    uv10 = ds['uv10']
#    ave_w = average_wind(5,180,uv10[0:3,:,:],True)

# array([      nan, 15.236684, 15.162975, ..., 13.162424, 13.215631, 13.269934])
