#! /usr/bin/env python
'''
 Create multi-panel plot of CHLA/DEFF
'''
# --- import modules -----------------------------------------------------------
from netCDF4 import Dataset
import numpy as np
import glob
import datetime
import warnings

# --- main ---------------------------------------------------------------------
if __name__ == '__main__':
    files = glob.glob('*.nc')
    for file in files:
        print('--------------')
        print('Extents for {}'.format(file))
        nc_fid = Dataset(file)
        TIME = nc_fid.variables['TIME'][:].data
        date1=(datetime.datetime(1970,1,1,0,0,0) + datetime.timedelta(seconds=TIME[0])).strftime('%d/%m/%Y')
        date2=(datetime.datetime(1970,1,1,0,0,0) + datetime.timedelta(seconds=np.nanmax(TIME))).strftime('%d/%m/%Y')
        print('{} - {}'.format(date1,date2))
        nc_fid.close()