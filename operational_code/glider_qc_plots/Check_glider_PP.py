#!/usr/bin/env python

import glob
import os, shutil
import netCDF4 as nc
import numpy as np
import datetime
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
from matplotlib import gridspec
import argparse
from matplotlib.colors import LinearSegmentedColormap
from mpl_toolkits.basemap import Basemap
import warnings
warnings.filterwarnings("ignore")
        
#-main--------------------------------------------------------------------------
if __name__ == "__main__":

    nc_file1 = '/data/datasets/Projects/AlterEco/Glider_data/UEA/AE3_sg579_timeseries_flag.nc'
    nc_file2 = '/data/datasets/Projects/AlterEco/Glider_data/BODC_data/EGO/GL_20180508_Cabot_454_R.nc'

    nc_fid = nc.Dataset(nc_file1, 'r')
    PP1 = nc_fid.variables['PAR'][:]
    CHL1 = nc_fid.variables['Chlorophyll'][:]
    TIME1 = nc_fid.variables['time'][:]
    PP1[PP1 > 2000] = np.nan
    plt.scatter(TIME1, PP1/5.97, color='k', alpha=0.5)
    nc_fid.close()

    nc_fid = nc.Dataset(nc_file2, 'r')
    PP2 = nc_fid.variables['DOWNWELLING_PAR'][:].data
    CHL2 = nc_fid.variables['CHLA'][:]
    PP2[PP2 > 1000] = np.nan
    TIME2 = (nc_fid.variables['TIME'][:] + (datetime.datetime(1970,1,1) - datetime.datetime(1,1,1)).total_seconds() + 365.*86400.)/86400.

    PP2 = PP2[np.isfinite(TIME2)]
    TIME2 = TIME2[np.isfinite(TIME2)]
    plt.scatter(TIME2, PP2*86400.0, color='r', alpha=0.5)
    nc_fid.close()

    plt.savefig('/users/rsg/utils/web_visible_public_share/blo/files/AlterEco/test.png')
    print(np.nanmean(PP1), np.nanmean(PP2*86400))
    print(np.nanmean(CHL1),np.nanmean(CHL2))




#-EOF--
