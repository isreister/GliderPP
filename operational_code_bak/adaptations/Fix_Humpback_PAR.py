#!/usr/bin/env python

import argparse, os, sys, shutil, datetime, logging
from netCDF4 import Dataset
import numpy as np
from scipy.interpolate import interp1d

#-main--------------------------------------------------------------------------
if __name__ == "__main__":
    data_file = "/home/ben/shared/Linux_desktop/data/datasets/Projects/AlterEco/Glider_data/BODC_data/humpback_UEA/AE3_sg579_timeseries_flag_UEA.nc.bak"

    output_file=data_file.replace('.bak','')
    if os.path.exists(output_file):
        os.remove(output_file)

    shutil.copy(data_file,output_file)

    nc_file  = Dataset(output_file,'r+')

    TIME = nc_file.variables['time'][:].data
    PAR = nc_file.variables['PAR'][:].data
    CHLA = nc_file.variables['Chlorophyll'][:].data

    # re-baseline CHLA
    print(np.nanmin(CHLA))
    CHLA = CHLA - np.nanmin(CHLA)
    print(np.nanmin(CHLA))

    # correct for wrong units
    PAR = PAR/1000

    # filter out the spikes
    PAR[PAR>500]=np.nan

    #interp for missing data
    ii = np.where(np.isfinite(PAR) & np.isfinite(TIME))
    jj = np.where(np.isnan(PAR))
    PAR = interp1d(TIME[ii],PAR[ii],fill_value='extrapolate')(TIME)

    # smooth the signal with a running mean
    window = 21
    par = np.convolve(PAR, np.ones((window,))/window, mode='valid')
    PAR[int((window-1)/2):int(-(window-1)/2)]=par
    PAR[PAR<0] = np.nan

    #define variables
    nc_file.variables['PAR'][:] = PAR
    nc_file.variables['Chlorophyll'][:] = CHLA
    # Close the file.
    nc_file.close()
