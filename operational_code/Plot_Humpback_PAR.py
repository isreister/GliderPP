#!/usr/bin/env python


import sys,os,shutil
import netCDF4 as nc
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
import datetime

def process_PAR(input_file, tvar, var, window, tref, ttype='seconds'):
    nc_fid = nc.Dataset(input_file, 'r')
    TIME = nc_fid.variables[tvar][:]
    PAR = nc_fid.variables[var][:]
    nc_fid.close()

    if 'Masked' in str(type(PAR)):
        PAR = PAR.data
        PAR[PAR == 99999.0] = np.nan

    if ttype == 'seconds':
        TIME = TIME + (tref - datetime.datetime(1900,1,1)).total_seconds()
    elif ttype == 'days':
        TIME = TIME*86400. + (tref - datetime.datetime(1900,1,1)).total_seconds()

    PAR[PAR>4e5]=np.nan

    #interp for missing data
    ii = np.where(np.isfinite(PAR) & np.isfinite(TIME))
    PAR = interp1d(TIME[ii],PAR[ii],fill_value='extrapolate')(TIME)

    # running mean
    if window != 1:
        par = np.convolve(PAR, np.ones((window,))/window, mode='valid')
        PAR[(window-1)/2:-(window-1)/2]=par

    PAR[PAR<0] = np.nan
    TIME = TIME/86400
    
    if np.nanmean(PAR) > 100:
        PAR = PAR/1e8
    #PAR = (PAR - np.nanmin(PAR)) / (np.nanmax(PAR) - np.nanmin(PAR))

    return TIME, PAR

if __name__ == "__main__":
    window = 3
    input_file1 = "/data/datasets/Projects/AlterEco/Glider_data/BODC_data/humpback_UEA/AE3_sg579_timeseries_flag_UEA.nc"
    time1, par1 = process_PAR(input_file1, 'time', 'PAR', window, datetime.datetime(1,1,1), ttype='days')

    input_file2 = "/data/datasets/Projects/AlterEco/Glider_data/BODC_data/EGO/Cabot_20190312/Cabot_517_R.nc"
    time2, par2 = process_PAR(input_file2, 'TIME', 'DOWNWELLING_PAR', window, datetime.datetime(1970,1,1))

    input_file3 = "/data/datasets/Projects/AlterEco/Glider_data/BODC_data/EGO/GL_20180508_Cabot_454_R.nc"
    time3, par3 = process_PAR(input_file3, 'TIME', 'DOWNWELLING_PAR', window, datetime.datetime(1970,1,1))

    # plotting
    output_file = "/users/rsg/utils/web_visible_public_share/blo/private/HUMPBACK_PAR.png"
    
    fig1 = plt.figure(figsize=(20,10), dpi=300)
    plt.scatter(time1, par1, s=10, c='b', edgecolor='b', alpha=0.5)
    plt.scatter(time2, par2, s=10, c='r', edgecolor='r', alpha=0.5)
    plt.scatter(time3, par3, s=10, c='g', edgecolor='g', alpha=0.5)

    #plt.xlim([43525, 43660])
    #plt.ylim([0, 1e5])
    plt.xlabel('TIME')
    plt.ylabel('PAR')
    plt.savefig(output_file)

#-EOF--
