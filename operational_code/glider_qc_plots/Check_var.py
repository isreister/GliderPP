#!/usr/bin/env python

import os
from netCDF4 import Dataset
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import glob

#-main--------------------------------------------------------------------------
if __name__ == "__main__":

    nc_dir = '/data/datasets/Projects/AlterEco/Glider_data/BODC_preprocessed_data/EGO/'

    nc_pattern1 = '*_477_*'
    nc_pattern2 = '*_478_*'

    files = glob.glob(os.path.join(nc_dir,nc_pattern1))
    VAR1 = []
    TIME1 = []
    for nc_file in files:
        print(nc_file)
        nc_fid = Dataset(nc_file,'r')
        VAR1.append(nc_fid.variables['CHLA_CORRECTED'][:])
        TIME1.append(nc_fid.variables['TIME'][:])
        nc_fid.close()

    files = glob.glob(os.path.join(nc_dir,nc_pattern2))
    VAR2 = []
    TIME2 = []
    for nc_file in files:
        print(nc_file)
        nc_fid = Dataset(nc_file,'r')
        VAR2.append(nc_fid.variables['CHLA_CORRECTED'][:])
        TIME2.append(nc_fid.variables['TIME'][:])
        nc_fid.close()

    VAR1 = np.asarray([item for sublist in VAR1 for item in sublist])
    VAR2 = np.asarray([item for sublist in VAR2 for item in sublist])

    TIME1 = np.asarray([item for sublist in TIME1 for item in sublist])
    TIME2 = np.asarray([item for sublist in TIME2 for item in sublist])

    #filtering
    VAR1[VAR1 > 1e4] = np.nan
    VAR2[VAR2 > 1e4] = np.nan

    plt.scatter(TIME1, VAR1, s=5, edgecolor='g', facecolor='g', linewidth=None)
    plt.scatter(TIME2, VAR2, s=5, edgecolor='k', facecolor='k', linewidth=None)

    plt.xlabel('time')
    plt.ylabel('CHLA')
    plt.savefig('/users/rsg/utils/web_visible_public_share/blo/files/AlterEco/test_var')

