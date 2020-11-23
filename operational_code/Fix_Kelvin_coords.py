#!/usr/bin/env python

import argparse, os, sys, shutil, datetime, logging
from netCDF4 import Dataset
import numpy as np
from scipy.interpolate import interp1d

#-main--------------------------------------------------------------------------
if __name__ == "__main__":
    data_file = "/data/datasets/Projects/AlterEco/Glider_data/BODC_data/EGO/GL_20180928_Kelvin_481_R.nc"
    nc_file  = Dataset(data_file,'r+')

    TIME_GPS = nc_file.variables['TIME_GPS'][:]
    TIME = nc_file.variables['TIME'][:]
    LATITUDE_GPS = nc_file.variables['LATITUDE_GPS'][:]
    LONGITUDE_GPS = nc_file.variables['LONGITUDE_GPS'][:]

    fn1 = interp1d(TIME_GPS,\
                   LATITUDE_GPS, fill_value="extrapolate")

    fn2 = interp1d(TIME_GPS,\
                   LONGITUDE_GPS, fill_value="extrapolate")

    LATITUDE = fn1(TIME)
    LONGITUDE = fn2(TIME)

    #define variables
    ncV1 = nc_file.createVariable('LATITUDE_CORR',np.float32,'TIME',\
           fill_value=99999.)
    ncV2 = nc_file.createVariable('LONGITUDE_CORR',np.float32,'TIME',\
           fill_value=99999.)

    # Write data to variable
    ncV1[:] = LATITUDE
    ncV2[:] = LONGITUDE

    # Close the file.
    nc_file.close()
