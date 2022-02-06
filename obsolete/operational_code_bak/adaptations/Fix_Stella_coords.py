#!/usr/bin/env python

import argparse, os, sys, shutil, datetime, logging
from netCDF4 import Dataset
import numpy as np
from scipy.interpolate import interp1d

#-main--------------------------------------------------------------------------
if __name__ == "__main__":
    data_file = "/data/datasets/Projects/AlterEco/Glider_data/BODC_data/EGO/Stella_20180207/Stella_494_R.nc"
    nc_file  = Dataset(data_file,'r+')

    TIME_GPS = nc_file.variables['TIME_GPS'][:]
    TIME = nc_file.variables['TIME'][:]
    LONGITUDE_GPS = nc_file.variables['LONGITUDE_GPS'][:]

    fn = interp1d(TIME_GPS,\
                  LONGITUDE_GPS, fill_value="extrapolate")

    LONGITUDE = fn(TIME)

    #define variables
    ncV1   = nc_file.createVariable('LONGITUDE',np.float32,'TIME',\
                 fill_value=99999.)

    # Write data to variable
    ncV1[:]   = LONGITUDE

    # Close the file.
    nc_file.close()
