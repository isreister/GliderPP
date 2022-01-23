#!/usr/bin/env python

import os, sys, shutil
import numpy as np
import matplotlib.pyplot as plt
import netCDF4 as nc

if __name__ == "__main__":
   dcut = 5
   print('Starting....')
   glider_file='/Volumes/PML_BACKUP/Linux_desktop/data/datasets/Projects/AlterEco/Glider_data/BODC_data/humpback_UEA/AE3_sg579_timeseries_flag_UEA.nc.bak'
   #glider_file = '/Volumes/PML_BACKUP/Linux_desktop/data/datasets/Projects/AlterEco/Glider_data/BODC_data/EGO/GL_20180508_Cabot_454_R.nc'
   nc_fid = nc.Dataset(glider_file,'r')
   try:
       CHL = nc_fid.variables['Chlorophyll'][:]
       TIME = nc_fid.variables['time'][:]
       DEPTH = nc_fid.variables['depth'][:]
       PAR = nc_fid.variables['PAR'][:]
   except:
       CHL = nc_fid.variables['CHLA'][:]
       TIME = nc_fid.variables['TIME'][:].data
       DEPTH = abs(nc_fid.variables['PRES'][:])
       PAR = nc_fid.variables['DOWNWELLING_PAR'][:]*1000000/4.6
   nc_fid.close()

   CHL[CHL<0.0]=0.0
   print('------CHL-------')
   print(np.nanmax(CHL))
   print(np.nanmin(CHL))
   print(np.nanstd(CHL))

   PAR[PAR<0.0]=0.0
   print('------PAR-------')
   print(np.nanmax(PAR))
   print(np.nanmin(PAR))
   print(np.nanstd(PAR))

   ii = np.where((np.isfinite(TIME)) & (np.isfinite(CHL)) & (DEPTH < dcut))
   plt.plot(TIME[ii], CHL[ii], 'r')
   plt.plot(TIME[ii], PAR[ii], 'b')
   plt.savefig('test.png')

