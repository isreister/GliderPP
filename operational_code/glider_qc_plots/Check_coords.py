#!/usr/bin/env python

from netCDF4 import Dataset
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

#-main--------------------------------------------------------------------------
if __name__ == "__main__":
#    nc_fid = Dataset('/data/datasets/Projects/AlterEco/Glider_data/BODC_data/EGO/GL_20180928_Kelvin_481_R.nc')
    nc_fid = Dataset('/data/datasets/Projects/AlterEco/Glider_data/EO_data/EGO_481_Kelvin/NRT/EGO_481_Kelvin_trajectory.nc')
    LAT = nc_fid.variables['LATITUDE'][:]
    LON = nc_fid.variables['LONGITUDE'][:]
    PROF = nc_fid.variables['PROFILE_NUMBER'][:]
    TIME = nc_fid.variables['TIME'][:]
    nc_fid.close()

    #sanity checks
    LAT[LAT>90.]=np.nan
    LAT[LAT<-90.]=np.nan
    LON[LON>360.]=np.nan
    LON[LON<-180.]=np.nan

    print(len(LAT[np.isfinite(LAT)]))
    print(len(LON[np.isfinite(LON)]))

    ii = np.where((np.isfinite(LAT)) & (np.isfinite(LON)))

    LAT = LAT[ii]
    LON = LON[ii]

    print(len(LON))
    print(len(LAT))

    plt.scatter(LON,LAT)
    plt.savefig('test')

    print('--------------')
    print(np.nanmin(LON))
    print(np.nanmax(LON))
    print(np.nanmin(LAT))
    print(np.nanmax(LAT))
    print('--------------')
