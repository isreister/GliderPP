#!/usr/bin/env python
'''
Description:    Glider data manipulation functions

Version: 	v1.0 11/2017

Ver. hist:

Author:		Ben Loveday, Plymouth Marine Laboratory

License:        MIT Licence -- Copyright 2017 Plymouth Marine Laboratory

		Permission is hereby granted, free of charge, to any person
                obtaining a copy of this software and associated documentation 
                files (the "Software"), to deal in the Software without 
                restriction, including without limitation the rights to use, 
                copy, modify, merge, publish, distribute, sublicense, and/or 
                sell copies of the Software, and to permit persons to whom the 
                Software is furnished to do so, subject to the following 
                conditions:

                The above copyright notice and this permission notice shall be 
                included in all copies or substantial portions of the Software.

                THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, 
                EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES 
                OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND 
                NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT 
                HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
                WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING 
                FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR 
                OTHER DEALINGS IN THE SOFTWARE.
'''
#-imports-----------------------------------------------------------------------
from __future__ import print_function
import argparse, os, sys, shutil, datetime, logging
from netCDF4 import Dataset
import numpy as np
import subprocess
from scipy.interpolate import interp1d
from scipy import stats
import glob
import fnmatch
from scipy.interpolate import RegularGridInterpolator
from dateutil.relativedelta import relativedelta
from scipy.signal import savgol_filter
import matplotlib
matplotlib.use('Agg')
import time
import matplotlib.pyplot as plt
import ephem
from scipy.integrate import simps
import gsw
from matplotlib import gridspec

# add paths/tools
import netCDF_tools as nct
import db_tools as db
import mld_utils as mu
import common_tools as ct
import fluor_correction as fcorr
import par_correction as parcorr

#-functions---------------------------------------------------------------------
def write_trajectory_file(GLIDER_CONFIG, input_files, output_file,logging=None):
    GLIDER_DICT = read_config_file(GLIDER_CONFIG, logging=None)
    bashCommand='ncrcat -O -H -v ' + GLIDER_DICT['lon_var'] + ',' \
                                 + GLIDER_DICT['lat_var'] + ',' \
                                 + GLIDER_DICT['record_var'] + ',' \
                                 + GLIDER_DICT['profile_var'] + ' ' \
                                 + ' '.join(input_files) + ' '\
                                 + output_file

    execute(bashCommand,logging=logging)
    permit(output_file)

def get_coords(open_file, GLIDER_DICT, logging=None, verbose=False, use_backups=False):
    '''
     Finds spatio-temporal limits of glider profile
    '''
    nc_fid = Dataset(open_file,'r')

    good_lon = True
    good_lat = True
    good_prof = True

    debug = False

    # lon var
    try:
        lon = nc_fid.variables[GLIDER_DICT['lon_var']][:]
        # terrible catch-all for bad netcdf
        if 'MaskedArray' in str(type(lon)):
            lon = lon.data
            lon[lon>1000]=np.nan
            lon[lon<-1000]=np.nan
    except:
        good_lon = False

    if not good_lon or use_backups:
        try:
            print('Bad lon')
            lon = nc_fid.variables[GLIDER_DICT['lon_var_backup']][:]
            # terrible catch-all for bad netcdf
            if 'MaskedArray' in str(type(lon)):
                lon = lon.data
                lon[lon>1000]=np.nan
                lon[lon<-1000]=np.nan
            good_lon = True
        except:
            lon = np.nan

    # lat vars
    try:
        lat = nc_fid.variables[GLIDER_DICT['lat_var']][:]
        # terrible catch-all for bad netcdf
        if 'MaskedArray' in str(type(lat)):
            lat = lat.data
            lat[lat>1000]=np.nan
            lat[lat<-1000]=np.nan
    except:
        good_lat = False

    if not good_lat or use_backups:
        try:
            print('Bad lat')
            lat = nc_fid.variables[GLIDER_DICT['lat_var_backup']][:]
            # terrible catch-all for bad netcdf
            if 'MaskedArray' in str(type(lat)):
                lat = lat.data
                lat[lat>1000]=np.nan
                lat[lat<-1000]=np.nan
            good_lat = True
        except:
            lat = np.nan

    #sanity checks
    lat[lat>90.]=np.nan
    lat[lat<-90.]=np.nan
    lon[lon>360.]=np.nan
    lon[lon<-180.]=np.nan

    #trim to good values only
    if len(lat[np.isfinite(lat)]) != len(lon[np.isfinite(lon)]):
        print('Warning! Coordinates are corrupted')
        ii = np.where((np.isfinite(lat)) & (np.isfinite(lon)))
        lat_check = lat[ii]
        lon_check = lon[ii]
    else:
        lat_check = lat.copy()
        lon_check = lon.copy()

    # profile vars
    profile_numbers = nc_fid.variables[GLIDER_DICT['profile_var']][:]

    if debug:
        print(np.nanmin(lon_check))
        print(np.nanmax(lon_check))
        print(np.nanmin(lat_check))
        print(np.nanmax(lat_check))

    # time vars
    try:
        time = np.copy(nc_fid.variables[GLIDER_DICT['t_var']][:])
        time[time > 1e32] = np.nan
        mean_times = []
        mean_lat = []
        mean_lon = []
        for profile_number in np.unique(profile_numbers):
            
            mean_times.append(np.nanmean(time[profile_number == profile_numbers]))
            mean_lat.append(np.nanmean(lat[profile_number == profile_numbers]))
            mean_lon.append(np.nanmean(lon[profile_number == profile_numbers]))

        if GLIDER_DICT['t_base'] == 'seconds':
            min_time = datetime.datetime.strptime(GLIDER_DICT['t_ref'],\
                       '%Y-%m-%d %H:%M:%S')+\
                       datetime.timedelta(seconds=int(np.nanmin(time)))
            max_time = datetime.datetime.strptime(GLIDER_DICT['t_ref'],\
                       '%Y-%m-%d %H:%M:%S')+\
                       datetime.timedelta(seconds=int(np.nanmax(time)+1))
        elif GLIDER_DICT['t_base'] == 'days':
            min_time = datetime.datetime.strptime(GLIDER_DICT['t_ref'],\
                       '%Y-%m-%d %H:%M:%S')+\
                       datetime.timedelta(days=int(np.nanmin(time)))
            max_time = datetime.datetime.strptime(GLIDER_DICT['t_ref'],\
                       '%Y-%m-%d %H:%M:%S')+\
                       datetime.timedelta(days=int(np.nanmax(time)+1))
        elif GLIDER_DICT['t_base'] == 'matlab':
            # as in days but need to remove a year a and a day as python cannot
            # cope with 0000-00-00 as a reference date
            min_time = datetime.datetime.strptime(GLIDER_DICT['t_ref'],\
                       '%Y-%m-%d %H:%M:%S')+\
                       datetime.timedelta(days=int(np.nanmin(time)-367))
            max_time = datetime.datetime.strptime(GLIDER_DICT['t_ref'],\
                       '%Y-%m-%d %H:%M:%S')+\
                       datetime.timedelta(days=int(np.nanmax(time)+1-367))
        else:
            db.shout('Bad time base', logging=logging, verbose=verbose)
            min_time = np.nan
            max_time = np.nan
    except:
        min_time = np.nan
        max_time = np.nan

    if debug:
        print(min_time)
        print(max_time)

    # get average glider time
    ave_time = np.ones(len(mean_times))*np.nan
    for ii in np.arange(0,len(ave_time)):
        if GLIDER_DICT['t_base'] == 'seconds':        
            this_time = datetime.datetime.strptime(GLIDER_DICT['t_ref'],\
                     '%Y-%m-%d %H:%M:%S')+\
                     datetime.timedelta(seconds=int(mean_times[ii]))
            ave_time[ii] = (this_time - \
                           datetime.datetime(1,1,1)).total_seconds()/86400
        elif GLIDER_DICT['t_base'] == 'days':
            this_time = datetime.datetime.strptime(GLIDER_DICT['t_ref'],\
                     '%Y-%m-%d %H:%M:%S')+\
                     datetime.timedelta(days=int(mean_times[ii]))
            ave_time[ii] = (this_time - \
                           datetime.datetime(1,1,1)).total_seconds()/86400
        elif GLIDER_DICT['t_base'] == 'matlab':
            this_time = datetime.datetime.strptime(GLIDER_DICT['t_ref'],\
                     '%Y-%m-%d %H:%M:%S')+\
                     datetime.timedelta(days=int(mean_times[ii]-367))
            ave_time[ii] = (this_time - \
			   datetime.datetime(1,1,1)).total_seconds()/86400 \
                           -int(mean_times[ii])+mean_times[ii]
    nc_fid.close()

    # check latitude per profile against checked coordinates
    mean_lon = np.asarray(mean_lon).astype(float)
    mean_lat = np.asarray(mean_lat).astype(float)

    mean_lon[mean_lon<np.nanmin(lon_check)] = np.nan
    mean_lon[mean_lon>np.nanmax(lon_check)] = np.nan
    mean_lat[mean_lat<np.nanmin(lat_check)] = np.nan
    mean_lat[mean_lat>np.nanmax(lat_check)] = np.nan

    return np.nanmin(lon_check), np.nanmax(lon_check), mean_lon, \
           np.nanmin(lat_check), np.nanmax(lat_check), mean_lat, \
           min_time, max_time, ave_time, np.unique(profile_numbers) 

def nan_vals(x):
   '''
    QC data does not survive this process...
   '''
   x = x.astype(float)
   val = np.nanmean(x)
   return val

def concatenate_files(input_dir, CONFIG, logging = None):
    '''
     Concatenates glider profiles into single file
    '''
    good_flag = True    
    concat_dir = input_dir.replace(CONFIG['output_dir'],CONFIG['concat_dir'])

    if not os.path.exists(concat_dir):
        os.makedirs(concat_dir)
        os.chmod(concat_dir, 0o777)
    
    concat_file = concat_dir + '/' + CONFIG['gprefix'] +\
                  str(CONFIG['gnumber']) + '_binned.nc'

    nc_files = glob.glob(input_dir+'/*.nc')

    for nc_file in nc_files:
        output_file = nc_file.replace('_fin','_rec')
        output_file = output_file.replace('_bad','_rec')
        bashCommand='ncks -O --mk_rec_dim profile_number ' + nc_file + ' '\
                     + output_file
        execute(bashCommand,logging=logging)
        permit(output_file)

    bashCommand='ncrcat -O ' + ' '.join(nc_files) + ' '\
                  + concat_file
                 
    execute(bashCommand,logging=logging)
    permit(concat_file)
    return good_flag

def create_interpolated_netcdf_file(input_file, output_file, old_dim, \
                                    interp_dim, dim_name, prof_number):
    '''
     Create a netCDF file ready to ingest interpolated variables. All variables
     that have a different dimension length to the interpolation variables
     are copied across untouched.
    '''
    dsin = Dataset(input_file,'r')

    # create a new netCDF file for writing
    dsout = Dataset(output_file,'w',format='NETCDF4_CLASSIC')

    #Copy dimensions
    for dname, the_dim in dsin.dimensions.iteritems():
        if len(the_dim) == len(old_dim):
            dsout.createDimension(dname, len(interp_dim) \
                  if not the_dim.isunlimited() else None)
        else:
            dsout.createDimension(dname, len(the_dim) \
                  if not the_dim.isunlimited() else None)

    # Copy variables
    for v_name, varin in dsin.variables.iteritems():
        if '_qc' in v_name:
            continue
        # copies across all vars, but leaves interp variables space undefined.
        if varin.dimensions and \
                 len(dsin.dimensions[varin.dimensions[0]]) == len(old_dim):
            outVar = dsout.createVariable(v_name, varin.datatype, dim_name)
        else:
            outVar = dsout.createVariable(v_name, varin.datatype,\
                                          varin.dimensions)
            outVar[:] = varin[:]

        # Copy variable attributes
        outVar.setncatts({k: varin.getncattr(k) for k in varin.ncattrs()})

    # close the output file    
    dsout.close()
    dsin.close()

def get_profile_number(data_file):
    parse_name=os.path.basename(data_file).split('.')[0]
    prof_number = int(parse_name.split('_')[-1])
    return prof_number

def read_config_file(GLIDER_CONFIG, logging=None, verbose=False):
    GLIDER_DICT = {}
    try:
        db.shout("Reading configuration file...", logging=logging,\
                 verbose=verbose)
        with open(GLIDER_CONFIG) as myfile:
            for line in myfile:
                if '#' in line:
                    continue
                else:
                    name, var = line.partition("=")[::2]
                    GLIDER_DICT[name.strip()] = str(var.replace('\n', ''))
    except:
        db.shout("Failed to read configuration file", logging=logging,\
                 verbose=verbose)
        sys.exit()

    return GLIDER_DICT

def execute(command, logging=None):
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, \
                               stderr=subprocess.STDOUT)

    output = process.communicate()[0]
    exitCode = process.returncode
    
    if (exitCode == 0):
        return output
    else:
        raise ConnectionError(command, exitCode, output)
    process.wait()

def permit(myfile):
    os.chmod(myfile, 0o777)

def turning_points(array):
    # https://stackoverflow.com/questions/19936033/finding-turning-points-of-an-array-in-python
    ''' turning_points(array) -> min_indices, max_indices
    Finds the turning points within an 1D array and returns the indices of the minimum and 
    maximum turning points in two separate lists.
    '''
    idx_max, idx_min = [], []
    if (len(array) < 3): 
        return idx_min, idx_max

    NEUTRAL, RISING, FALLING = range(3)
    def get_state(a, b):
        if a < b: return RISING
        if a > b: return FALLING
        return NEUTRAL

    ps = get_state(array[0], array[1])
    begin = 1
    for i in range(2, len(array)):
        s = get_state(array[i - 1], array[i])
        if s != NEUTRAL:
            if ps != NEUTRAL and ps != s:
                if s == FALLING: 
                    idx_max.append((begin + i - 1) // 2)
                else:
                    idx_min.append((begin + i - 1) // 2)
            begin = i
            ps = s
    return idx_min, idx_max

def split_dive_index(data_file, output_file, GLIDER_CONFIG, logging=None, \
                     profiles_nums_exist=False):
    '''
     Splits ingested file into dives and adds new profile number to record. 
     Should support both EGO and SG formats.
    '''
    debug = False

    # read processing config file
    CONFIG_DICT = read_config_file(GLIDER_CONFIG,logging=logging)

    if profiles_nums_exist:
        print('Profile numbers exist....')
        nc_fid = Dataset(data_file)
        profile_num = nc_fid.variables[CONFIG_DICT['profile_var_read']][:]
        rec_len = len(profile_num)
        nc_fid.close()
    else:
        nc_fid = Dataset(data_file)
        nominal_depth_var = nc_fid.variables[CONFIG_DICT['depth_var']][:]
        nominal_depth_var = np.ma.filled(nominal_depth_var.astype(float), np.nan)

        try:
            x_var = nc_fid.variables[CONFIG_DICT['record_var']][:]
            if 'numpy.ma.core.MaskedArray' in str(type(x_var)):
                x_var = x_var.data
                x_var = np.ma.filled(x_var.astype(float), np.nan)
        except:
            x_var = np.arange(len(nominal_depth_var))

        nc_fid.close()

        if CONFIG_DICT['depth_pol'] == 'positive':
            nominal_depth_var[nominal_depth_var < 0.0] = 0.0
        else:
            nominal_depth_var[nominal_depth_var > 0.0] = 0.0

        # fill gaps
        print('Interpolating....')
        fn = interp1d(x_var[np.isfinite(nominal_depth_var)],\
                  nominal_depth_var[np.isfinite(nominal_depth_var)], fill_value="extrapolate")
        ndv = fn(x_var)

        # iterate through file to find inversion points
        rec_len = len(ndv)
        xlocs = np.arange(rec_len)

        # smooth depth field
        print('Smoothing....')
        ndv_smooth = savgol_filter(ndv,\
                               int(CONFIG_DICT['sgolay_win']),\
                               int(CONFIG_DICT['sgolay_smooth']))
        # find inversion points
        print('Finding turning points....')
        idx_min,idx_max = turning_points(ndv_smooth)
        idx_max = np.asarray(idx_max)
        idx_min = np.asarray(idx_min)

        # reverse polarity if depth values are negative
        if np.nanmean(idx_max) < np.nanmean(idx_min):
            tmp = idx_max[:]
            idx_max = idx_min[:]
            idx_min = tmp[:]

        profile_num = np.zeros(rec_len).astype(int)

        # first profile
        print('Assigning profile numbers....')
        idx = np.sort(np.concatenate((idx_max,idx_min)))

        count = 0
        if idx[0] != 0:
            profile_num[0:idx[0]-1] = 0
            count = count + 1

        for ii in range(len(idx)-1):
            profile_num[idx[ii]:idx[ii+1]] = count
            count = count + 1
   
        profile_num[idx[-1]:] = count

        if debug:
            print('Making debug plots...')
            partition = 2000
            for ii in range(0,len(xlocs),partition):
                plt.plot(xlocs[ii:ii+partition-1],ndv[ii:ii+partition-1],'0.5')
                plt.plot(xlocs[ii:ii+partition-1],ndv_smooth[ii:ii+partition-1],\
                         'b--')
                plt.scatter(xlocs[idx_max],ndv_smooth[idx_max],color='g')
                plt.scatter(xlocs[idx_min],ndv_smooth[idx_min],color='r')
                plt.xlim([xlocs[ii], xlocs[ii+partition-1]])
                plt.savefig('depth_profile'+str(ii))

    # now split
    print('Splitting....')
    split_files = []
    profile_num = np.asarray(profile_num).astype(int)
    recs = np.arange(rec_len).astype(int)
    for ii in np.unique(profile_num):
        this_rec = recs[profile_num == ii]
        split_file = output_file.replace('.nc','_'+str(ii).zfill(6)+'.nc')
        split_files.append(split_file)
        bashCommand='ncks -O -d '+CONFIG_DICT['record_var']+','+str(this_rec[0])+','+str(this_rec[-1])\
                    +' '+data_file+' '+ split_file

        db.shout(bashCommand, logging=logging, verbose=False)
        execute(bashCommand, logging=logging)
        permit(split_file)

    return split_files

def interpolate_dive(data_file, output_file, GLIDER_CONFIG, CONFIG,\
                     interp_flag=False, logging=None):
    '''
     Finds minimum/maximum depth in glide profile to enable it to be split     
    '''
    good_flag = True

    if os.path.exists(output_file):
        os.remove(output_file)

    bad_file = output_file.replace('_int','_bad')
    if os.path.exists(bad_file):
        os.remove(bad_file)

    # read processing config file
    CONFIG_DICT = read_config_file(GLIDER_CONFIG,logging=logging)

    data_fid = Dataset(data_file,'r')
    nc_attrs, nc_dims, nc_vars, nc_groups = nct.ncdump(data_fid, verb=False)
    depth = data_fid.variables[CONFIG_DICT['depth_var']][:]
    prof_number = get_profile_number(data_file)
    
    if interp_flag:
        interp_bins = np.arange(float(CONFIG_DICT['depth_min']),\
                                float(CONFIG_DICT['depth_max'])+\
                                float(CONFIG_DICT['depth_bin']),\
                                float(CONFIG_DICT['depth_bin']))
        interp_depth = interp_bins[0:-1]

        # create a netCDF ready for population with interpolated variables
        create_interpolated_netcdf_file(data_file, output_file,\
                                    depth, interp_depth,\
                                    CONFIG_DICT['record_var'],prof_number)

        # reopen and add profile number
        nc_fid = Dataset(output_file,'r+')
        rec_var = nc_fid.variables[CONFIG_DICT['record_var']][:]
        ncprof_num = nc_fid.createVariable(CONFIG_DICT['profile_var'],np.float64,\
                       (CONFIG_DICT['record_var']))
        ncprof_num[:] = np.ones(len(rec_var))*prof_number
        allowed_vars = list(CONFIG_DICT['allowed'].split(','))

        for nc_var in nc_vars[0]:
            # only process allowed variables          
            var_matches = set([nc_var]).intersection(set(allowed_vars))

            if not var_matches:
                continue

            # special conditions: depth variable
            if nc_var == CONFIG_DICT['depth_var']:
                nc_fid.variables[nc_var][:] = interp_depth
                continue

            dims = nc_fid.variables[nc_var].dimensions
            if dims and dims[0] == CONFIG_DICT['record_var']:
                # binning approach
                data = data_fid.variables[nc_var][:]

                try:
                    bin_data, bin_edges, bin_number = \
                                            stats.binned_statistic(depth,\
                                            data, statistic=nan_vals,\
                                            bins=interp_bins,\
                                            range=[np.nanmin(interp_bins),\
                                            np.nanmax(interp_bins)])
                    nc_fid.variables[nc_var][:] = bin_data
                except:
                    good_flag = False
                    nc_fid.variables[nc_var][:] = interp_depth*np.nan
        nc_fid.close()
        data_fid.close()
    else:
        data_fid.close()
        shutil.copy(data_file, output_file)
        # reopen and add profile number
        nc_fid = Dataset(output_file,'r+')
        try:
            rec_var = nc_fid.variables[CONFIG_DICT['record_var']][:]
            ncprof_num = nc_fid.createVariable(CONFIG_DICT['profile_var'],np.float64,\
                       (CONFIG_DICT['record_var']))
        except:
            rec_var = nc_fid.variables[CONFIG_DICT['alt_record_var']][:]
            ncprof_num = nc_fid.createVariable(CONFIG_DICT['profile_var'],np.float64,\
                       (CONFIG_DICT['record_var']))
        ncprof_num[:] = np.ones(len(rec_var))*prof_number
        nc_fid.close()

    # rename files based on level of success
    if good_flag:
        output_file_final = output_file.replace('.nc','_fin.nc')
    else:
        output_file_final = output_file.replace('.nc','_bad.nc')

    bashCommand='ncks -O --mk_rec_dim '+CONFIG_DICT['record_var']+' '+ \
                output_file + ' ' + output_file_final

    execute(bashCommand, logging=logging)
    permit(output_file_final)

    # remove intermediate data files
    os.remove(data_file)
    os.remove(output_file)

def glider_average_values(concat_file, GLIDER_CONFIG, COORDS_LIST,\
                          logging=None, verbose=False, use_backups=False):
    '''
     Defines file with lon/lat/time boundaries for glider series
    '''

    # read processing config file
    GLIDER_DICT = read_config_file(GLIDER_CONFIG,logging=logging)

    LON_MIN, LON_MAX, lon_average, \
      LAT_MIN, LAT_MAX, lat_average, \
      T_MIN, T_MAX, time_average, \
      profile_average = get_coords(concat_file, GLIDER_DICT, \
                                      logging=logging,\
                                      verbose=verbose,\
                                      use_backups=use_backups)

    return lon_average, lat_average, time_average, \
           profile_average

def define_boundary_file(concat_file, GLIDER_CONFIG, COORDS_LIST, boundary_file,\
                         pad, logging=None, verbose=False, use_backups=False):
    '''
     Defines file with lon/lat/time boundaries for glider series
    '''
    geo_update = False
    time_update = False

    # read processing config file
    GLIDER_DICT = read_config_file(GLIDER_CONFIG,logging=logging)
   
    LON_MIN, LON_MAX, lon_average, \
      LAT_MIN, LAT_MAX, lat_average, \
      T_MIN, T_MAX, time_average, \
      profile_average = get_coords(concat_file, GLIDER_DICT, \
                                      logging=logging,\
                                      verbose=verbose,\
                                      use_backups=use_backups)

    T_MIN = T_MIN - datetime.timedelta(days=pad)
    T_MAX = T_MAX + datetime.timedelta(days=pad)
    
    # check what coords need to be updated
    if str(T_MIN) != str(COORDS_LIST[4]) or \
       str(T_MAX) != str(COORDS_LIST[5]):
        time_update = True

    if float(LON_MIN) < float(COORDS_LIST[0]) or \
       float(LON_MAX) > float(COORDS_LIST[1]) or \
       float(LAT_MIN) < float(COORDS_LIST[2]) or \
       float(LAT_MAX) > float(COORDS_LIST[3]):
        geo_update = True 
        LON_MIN = LON_MIN - pad
        LON_MAX = LON_MAX + pad 
        LAT_MIN = LAT_MIN - pad
        LAT_MAX = LAT_MAX + pad

    if geo_update or time_update:
        with open(boundary_file, 'w') as the_file:
            the_file.write(str(LON_MIN)+','+\
                           str(LON_MAX)+','+\
                           str(LAT_MIN)+','+\
                           str(LAT_MAX)+','+\
                           str(T_MIN)+','+\
                           str(T_MAX))

        db.shout('Written: '+boundary_file, logging=logging, verbose=verbose)
    else:
        db.shout('Using old: '+boundary_file, logging=logging, verbose=verbose)

    return geo_update, time_update, lon_average, lat_average, time_average, \
           profile_average

def convert_time(surf_time,T0,tstep):
    '''
      Convert glider timebase to EO timebase for interpolation
    '''
    adapted_time = np.ones(np.shape(surf_time))*np.nan
    for ii in np.arange(0,len(adapted_time)):
        if np.isnan(surf_time[ii]):
            adapted_time[ii] = np.nan
        else:
            glider_date = datetime.datetime.fromordinal(int(surf_time[ii]))\
                           +datetime.timedelta(days=surf_time[ii]%1)
            adapted_time[ii] = (glider_date - datetime.datetime.\
                               strptime(T0,'%Y-%m-%d %H:%M:%S')).total_seconds()
            if tstep =='days':
                adapted_time[ii] = adapted_time[ii]/86400
            if tstep =='hours':
                adapted_time[ii] = adapted_time[ii]/3600
    return adapted_time

def fly_cube(variable, TRA_CONFIG, GLIDER_CONFIG, MODULE_DICT, nc_concat_file,\
             nc_outfile, adapted_time, t_ave, lon_ave, lat_ave, prof_ave, \
             clim=False, logging=None, verbose=False):

    lon_ave = np.asarray(lon_ave).astype(float)
    lat_ave = np.asarray(lat_ave).astype(float)

    success = True
    GLIDER_DICT = read_config_file(GLIDER_CONFIG,logging=logging)

    nc_fid = Dataset(nc_concat_file, 'r')
    lon_EO = nc_fid.variables[TRA_CONFIG[variable]['lon_var']][:]
    lat_EO = nc_fid.variables[TRA_CONFIG[variable]['lat_var']][:]

    if clim:
        # assume monthly with wrap-around
        # e.g. Dec/Jan/Feb......Nov/Dec/Jan
        time_EO = np.arange(0,14)
    else:
        time_EO = nc_fid.variables[TRA_CONFIG[variable]['t_var']][:]

    if 'numpy.ma.core.MaskedArray' in str(type(time_EO)):
        time_EO = time_EO.data
        time_EO = np.ma.filled(time_EO.astype(float), np.nan)

    if 'numpy.ma.core.MaskedArray' in str(type(lon_EO)):
        lon_EO = lon_EO.data
        lon_EO = np.ma.filled(lon_EO.astype(float), np.nan)

    if 'numpy.ma.core.MaskedArray' in str(type(lat_EO)):
        lat_EO = lat_EO.data
        lat_EO = np.ma.filled(lat_EO.astype(float), np.nan)

    nc_fid.close()

    if not TRA_CONFIG[variable]['calc_vars']:
       success = True
       return success

    PREP_VARS = np.ones((np.shape(time_EO)[0],\
                         np.shape(lat_EO)[0],\
                         np.shape(lon_EO)[0],\
                         len(TRA_CONFIG[variable]['calc_vars'])))*np.nan
    try:
        if 'ATMOS' in variable:
            PREP_VARS[:,:,:,0],\
            PREP_VARS[:,:,:,1],\
            PREP_VARS[:,:,:,2],\
            PREP_VARS[:,:,:,3],\
            PREP_VARS[:,:,:,4],\
            PREP_VARS[:,:,:,5],\
            rlat_EO = derive_atmos_vars(MODULE_DICT,nc_concat_file,\
                 variable, TRA_CONFIG, lat_EO, logging=logging, verbose=verbose)

        elif 'ALTIM' in variable:
            PREP_VARS[:,:,:,0],\
            PREP_VARS[:,:,:,1],\
            PREP_VARS[:,:,:,2],\
            PREP_VARS[:,:,:,3],\
            PREP_VARS[:,:,:,4],\
            PREP_VARS[:,:,:,5],\
            PREP_VARS[:,:,:,6],\
            PREP_VARS[:,:,:,7],\
            PREP_VARS[:,:,:,8],\
            rlat_EO = derive_altim_vars(nc_concat_file, \
                 variable, TRA_CONFIG, lat_EO, logging=logging, verbose=verbose)

        elif 'SST' in variable:
            PREP_VARS[:,:,:,0],\
            PREP_VARS[:,:,:,1],\
            PREP_VARS[:,:,:,2],\
            rlat_EO = derive_sst_vars(nc_concat_file, variable,\
                         TRA_CONFIG, lat_EO, logging=logging, verbose=verbose)

        elif 'CHL' in variable:
            PREP_VARS[:,:,:,0],\
            PREP_VARS[:,:,:,1],\
            rlat_EO = derive_chl_vars(nc_concat_file, variable,\
                         TRA_CONFIG, lat_EO, logging=logging, verbose=verbose)

        else:
            PREP_VARS[:,:,:,0],\
            rlat_EO = derive_par_vars(nc_concat_file, variable,\
                         TRA_CONFIG, lat_EO, logging=logging, verbose=verbose)

        create_netcdf_traj(t_ave,GLIDER_DICT['t_var'],\
                       lat_ave,GLIDER_DICT['lat_var'],\
                       lon_ave,GLIDER_DICT['lon_var'],\
                       prof_ave,GLIDER_DICT['profile_var'],\
                       nc_outfile, logging=logging, verbose=verbose)

        # now interpolate
        for ii in np.arange(0,len(TRA_CONFIG[variable]['calc_vars'])):
            db.shout('Interpolating: '+TRA_CONFIG[variable]['calc_vars'][ii],\
                     logging=logging, verbose=verbose)
            if clim:
                # interp year-by-year
                interp_var = []
                if TRA_CONFIG[variable]['t_base'] == 'seconds':
                    min_time = datetime.datetime.strptime(\
                               TRA_CONFIG[variable]['t_ref'],\
                               '%Y-%m-%d %H:%M:%S')+\
                               datetime.timedelta(seconds=\
                               int(np.nanmin(adapted_time)))
                    max_time = datetime.datetime.strptime(\
                               TRA_CONFIG[variable]['t_ref'],\
                               '%Y-%m-%d %H:%M:%S')+\
                               datetime.timedelta(seconds=\
                               int(np.nanmax(adapted_time)+1))
                elif TRA_CONFIG[variable]['t_base'] == 'hours':
                    min_time = datetime.datetime.strptime(\
                               TRA_CONFIG[variable]['t_ref'],\
                               '%Y-%m-%d %H:%M:%S')+\
                               datetime.timedelta(seconds=\
                               int(np.nanmin(adapted_time*3600)))
                    max_time = datetime.datetime.strptime(\
                               TRA_CONFIG[variable]['t_ref'],\
                               '%Y-%m-%d %H:%M:%S')+\
                               datetime.timedelta(seconds=\
                               int(np.nanmax(adapted_time*3600)+1))
                elif TRA_CONFIG[variable]['t_base'] == 'days':
                    min_time = datetime.datetime.strptime(\
                               TRA_CONFIG[variable]['t_ref'],\
                               '%Y-%m-%d %H:%M:%S')+\
                               datetime.timedelta(days=\
                               int(np.nanmin(adapted_time)))
                    max_time = datetime.datetime.strptime(\
                               TRA_CONFIG[variable]['t_ref'],\
                               '%Y-%m-%d %H:%M:%S')+\
                               datetime.timedelta(days=\
                               int(np.nanmax(adapted_time)+1))

                min_Year = min_time.year
                max_Year = max_time.year

                for YEAR in np.arange(min_Year, max_Year+1):
                    logging.info('Interpolating climatology for: '+str(YEAR))
                    # reconstruct time base for this year in format consistent
                    # with source timing
                    time_EO = []
                    for mm in np.arange(-1,13):
                       this_date = datetime.datetime(YEAR,1,15)+\
                                   relativedelta(months=mm)
                       this_time = (this_date - datetime.datetime.strptime(\
                                    TRA_CONFIG[variable]['t_ref'],\
                                    '%Y-%m-%d %H:%M:%S')).total_seconds()
                       if TRA_CONFIG[variable]['t_base'] =='days':
                           this_time = this_time/86400
                       if TRA_CONFIG[variable]['t_base'] =='hours':
                           this_time = this_time/3600

                       time_EO.append(this_time)

                    t_start = (datetime.datetime(YEAR,1,1,0,0,0) - \
                              datetime.datetime.strptime(\
                              TRA_CONFIG[variable]['t_ref'],\
                              '%Y-%m-%d %H:%M:%S')).total_seconds()

                    t_end   = (datetime.datetime(YEAR,12,31,23,59,59) - \
                              datetime.datetime.strptime(\
                              TRA_CONFIG[variable]['t_ref'],\
                              '%Y-%m-%d %H:%M:%S')).total_seconds()

                    if TRA_CONFIG[variable]['t_base'] =='days':
                        t_start = t_start/86400.
                        t_end   = t_end/86400.
                    elif TRA_CONFIG[variable]['t_base'] =='hours':
                        t_start = t_start/3600.
                        t_end   = t_end/3600.

                    # subset adapted_time: remember clim boundary wrapping
                    kk = np.where((adapted_time >= t_start) &\
                                  (adapted_time <= t_end))[0]

                    adapted_time_year = adapted_time[kk]
                    lon_year = lon_ave[kk]
                    lat_year = lat_ave[kk]

                    fn  = RegularGridInterpolator((time_EO,rlat_EO,lon_EO),\
                                           np.squeeze(PREP_VARS[:,:,:,ii]))

                    interp_var_year = np.ones(np.shape(adapted_time_year))\
                                      *np.nan
              
                    for tt in np.arange(0,len(adapted_time_year)):
                        if np.isfinite(adapted_time_year[tt]) &\
                          np.isfinite(lat_year[tt]) &\
                          np.isfinite(lon_year[tt]):
                            interp_var_year[tt] = fn([adapted_time_year[tt],\
                                                  lat_year[tt],lon_year[tt]])

                    interp_var_year[np.isnan(interp_var_year)]=float(-9999)
                    interp_var.append(interp_var_year)

                # finally convert list to array
                flat_list = [item for sublist in interp_var for item in sublist]
                interp_var = np.asarray(flat_list)
            else:
                fn  = RegularGridInterpolator((time_EO,rlat_EO,lon_EO),\
                                           np.squeeze(PREP_VARS[:,:,:,ii]))

                interp_var = np.ones(np.shape(adapted_time))*np.nan
                if 'PAR' in variable:
                    daytime_var = np.zeros(len(interp_var))
                
                for tt in range(len(adapted_time)):
                    if np.isfinite(adapted_time[tt]) & \
                      np.isfinite(lat_ave[tt]) & \
                      np.isfinite(lon_ave[tt]):
                        interp_var[tt] = fn([adapted_time[tt],\
                                         lat_ave[tt],lon_ave[tt]])

                        if 'PAR' in variable:
                            # special condition to derive PAR from daily average
                            # value based on latitude and time of day.
                            is_night, is_day, last_sunrise, next_sunset,  = \
                                     ct.glider_times(lat_ave[tt],lon_ave[tt],
                                     TRA_CONFIG[variable]['t_ref'],
                                     adapted_time[tt])

                            if is_day:
                                # model a sin curve for this latitude and get
                                # interpolated value
                                tstart = 0 
                                tend = (next_sunset - last_sunrise).total_seconds()
                                daylight_ratio = 86400/tend
                                tglid = datetime.datetime.strptime(TRA_CONFIG[variable]['t_ref'],'%Y-%m-%d %H:%M:%S') \
                                        + datetime.timedelta(seconds=int(adapted_time[tt]))
                                tglider = (tglid - last_sunrise).total_seconds()
                                tglider = tglider/tend * np.pi
                                npts = int(tend/60)
                                tend = np.pi
                                x = np.linspace(0,tend,npts)
                                y = np.sin(x)*interp_var[tt]*daylight_ratio
                                fn2 = interp1d(x,y)
                                # convert from mol/m2/day to W/m2
                                interp_var[tt] = fn2(tglider)*1e6/86400/4.6
                                daytime_var[tt] = 1
                            else:
                                interp_var[tt] = 0.0
                
                interp_var[np.isnan(interp_var)]=float(-9999)

            # now write into netcdf file
            write_netcdf_traj(interp_var,\
                              TRA_CONFIG[variable]['calc_vars'][ii],\
                              GLIDER_DICT['profile_var'],
                              nc_outfile, logging=logging,\
                              verbose=verbose)

            if 'PAR' in variable:
                write_netcdf_traj(daytime_var,\
                              'daytime',\
                              GLIDER_DICT['profile_var'],
                              nc_outfile, logging=logging,\
                              verbose=verbose)
    except:
        db.shout('Interpolation failed', logging=logging, verbose=verbose)
        success = False

    return success

def preprocess_dive(nc_file, GLIDER_CONFIG, traj_PAR, traj_KD490, traj_CHLA, glider_bathy, traj_WSPD,\
                    last_MLD, last_ZEU, logging=logging, verbose=False, correct_time=True):

    print('Preprocessing')

    try:
        if '_eo' in nc_file and np.mod(int(nc_file.split('_')[-5]), 10) == 0:
            debug = True
        elif np.mod(int(nc_file.split('_')[-4]), 10) == 0:
            debug = True
    except:
        pass
    debug = False

    MLD_min = 5.0

    success = True
    is_night = 0
    is_day = 0
    is_bad = 0
    is_good = 0
    is_no_DCM_night = 0
    is_day_good_PAR = 0
    E_0_plus = 0
    
    # read processing config file
    CONFIG_DICT = read_config_file(GLIDER_CONFIG,logging=logging)
   
    quench_method_used = 'None'
    use_Xing = False
    use_Biermann = False
    use_Swart = False
    use_Hemsley = False

    if 'Xing' in CONFIG_DICT['quench_methods'].split(','):
        use_Xing = True
    if 'Biermann' in CONFIG_DICT['quench_methods'].split(','):
        use_Biermann = True
    if 'Swart' in CONFIG_DICT['quench_methods'].split(','):
        use_Swart = True
    if 'Hemsley' in CONFIG_DICT['quench_methods'].split(','):
        use_Hemsley = True

    # -get the variable names for comparison to config list
    nc_fid     = Dataset(nc_file, 'r')
    nc_attrs, nc_dims, nc_vars, nc_groups = nct.ncdump(nc_fid, verb=False)

    # -get the vars-----------------------------------------------------------
    var_dict = {}
    for varname in nc_vars[0]:
        # Dolomite has empty PAR record, but variable is there...
        if 'Dolomite_499_' in nc_file and '_PAR' in varname:
            print('PAR variable is empty....skipping')
            continue
        # not all variables, esp scatterings, present in each file
        for ii in np.arange(len(CONFIG_DICT['allowed_vars'].split(','))):
            if int(CONFIG_DICT['allowed_exact'].split(',')[ii]) == 0:
                if CONFIG_DICT['allowed_vars'].split(',')[ii] in varname:
                    if verbose:
                        print('Found: '+varname)
                    # re-write using library...
                    storename = CONFIG_DICT['allowed_heads'].split(',')[ii]
                    var_dict[storename] = nc_fid.variables[varname][:]
            else:
                if CONFIG_DICT['allowed_vars'].split(',')[ii] == varname:
                    if verbose:
                        print('Found: '+varname)
                    # re-write using library...
                    storename = CONFIG_DICT['allowed_heads'].split(',')[ii]
                    var_dict[storename] = nc_fid.variables[varname][:]
    nc_fid.close()

    if 'TIME' not in var_dict.keys() and 'time' in var_dict.keys():
        var_dict['TIME'] = var_dict['time']

    tref = CONFIG_DICT['t_ref']

    # check for missing vars
    miss_vars = np.ones(len(CONFIG_DICT['allowed_heads'].split(',')))
    for ii in np.arange(len(CONFIG_DICT['allowed_heads'].split(','))):
        if CONFIG_DICT['allowed_heads'].split(',')[ii] not in var_dict.keys():          
            print('Missing: ' + CONFIG_DICT['allowed_heads'].split(',')[ii])
            miss_vars[ii] = 0.0

    if sum(miss_vars) == len(miss_vars):
        if verbose:
            print('All required variables present')

    # -autoselect temp/sal variables------------------------------------------
    if 'TIME' in var_dict.keys():
        TIME = var_dict['TIME']
        TIME[TIME > 1e20] = np.nan
        if 'numpy.ma.core.MaskedArray' in str(type(TIME)):
            TIME = TIME.data
            TIME = np.ma.filled(TIME.astype(float), np.nan)
    if 'TEMP' in var_dict.keys():
        TEMP = ct.check_remask_var(var_dict['TEMP'],0.0,1e5)
    if 'CTEMP' in var_dict.keys():
        CTEMP = ct.check_remask_var(var_dict['CTEMP'],0.0,1e5)
    if 'SAL' in var_dict.keys():
        SAL = ct.check_remask_var(var_dict['SAL'],0.0,1e5)
    if 'PRES' in var_dict.keys():
        PRES = ct.check_remask_var(var_dict['PRES'],-1e5,1e5)
    if 'CNDC' in var_dict.keys():
        CNDC = ct.check_remask_var(var_dict['CNDC'],0.0,1e5)  
    if 'PAR' in var_dict.keys():
        PAR = ct.check_remask_var(var_dict['PAR'],0.0,1e5) 
    if 'CHLA' in var_dict.keys():
        CHLA = ct.check_remask_var(var_dict['CHLA'],0.0,1e5) 
    if 'CDOM' in var_dict.keys():
        CDOM = ct.check_remask_var(var_dict['CDOM'],0.0,1e5) 
    if 'SCATTER' in var_dict.keys():
        SCATTER = ct.check_remask_var(var_dict['SCATTER'],0.0,1e5)
    if 'LATITUDE' in var_dict.keys():
        LATITUDE = ct.check_remask_var(var_dict['LATITUDE'],-90,90)
    if 'LONGITUDE' in var_dict.keys():
        LONGITUDE = ct.check_remask_var(var_dict['LONGITUDE'],-360,360)

    # correct LAT:
    if 'LATITUDE' in var_dict.keys():
        CORR_LATITUDE = LATITUDE.copy()
        CORR_BLANK = np.ones(np.shape(LATITUDE))*np.nan
        try:
            print('Interpolating latitude')
            fn = interp1d(TIME[np.isfinite(LATITUDE)],LATITUDE[np.isfinite(LATITUDE)],\
                 fill_value="extrapolate")
            CORR_LATITUDE = fn(TIME)
        except:
            pass

    # correct LON:
    if 'LONGITUDE' in var_dict.keys():
        CORR_BLANK = np.ones(np.shape(LONGITUDE))*np.nan
        CORR_LONGITUDE = LONGITUDE.copy()
        try:
            print('Interpolating longitude')
            fn = interp1d(TIME[np.isfinite(LONGITUDE)],LONGITUDE[np.isfinite(LONGITUDE)],\
                 fill_value="extrapolate")
            CORR_LONGITUDE = fn(TIME)
        except:
            pass
    
    # correct PRES & DEPTH:
    if 'PRES' in var_dict.keys():
        CORR_PRES = PRES.copy()
        CORR_DEPTH = PRES.copy()
        try:
            print('Interpolating pressure & depth')
            fn = interp1d(TIME[np.isfinite(PRES)],PRES[np.isfinite(PRES)],\
                 fill_value="extrapolate")
            PRES_int = fn(TIME)
            if np.nanmax(PRES) < 10:
                print('Correcting pressure')
                CORR_PRES = PRES_int*10 # BODC mess up with bar -> decibar
            else:
                CORR_PRES = PRES_int.copy()
            DEPTH = gsw.z_from_p(CORR_PRES,np.nanmean(CORR_LATITUDE))       
            CORR_DEPTH = DEPTH*-1
        except:
            pass

    CORR_DEPTH[CORR_DEPTH<0] = 0.0

    glider_HOUR = (datetime.datetime.strptime(CONFIG_DICT['t_ref'],'%Y-%m-%d %H:%M:%S') \
                      + datetime.timedelta(seconds=int(np.nanmean(TIME)))).hour

    # calculate absolute salinity

    if 'CNDC' in locals() and 'TEMP' in locals() and 'CORR_PRES' in locals():
        ASAL = CNDC.copy()
        try:
            # convert from mhos/m to mS/cm
            CNDC = CNDC * 1000 / 100
            PSAL = gsw.SP_from_C(CNDC,TEMP,CORR_PRES)
            ASAL = gsw.SA_from_SP(PSAL,CORR_PRES,np.nanmean(CORR_LONGITUDE),np.nanmean(CORR_LATITUDE))
            print('Calculated ASAL')
        except:
            pass

    elif 'SAL' in locals() and 'CORR_PRES' in locals():
        ASAL = SAL.copy()
        try:
            ASAL = gsw.SA_from_SP(SAL,CORR_PRES,np.nanmean(CORR_LONGITUDE),np.nanmean(CORR_LATITUDE))
            print('Calculated ASAL')
        except:
            pass

    # calculate conservative temperature
    if 'CTEMP' in locals():
        pass
    elif 'TEMP' in locals() and 'CORR_PRES' in locals() and 'ASAL' in locals():
        CTEMP = TEMP.copy()
        try:
            CTEMP = gsw.CT_from_t(ASAL,TEMP,CORR_PRES)
            print('Calculated CTEMP')
        except:
            pass

    # calculate MLD
    MLD = np.nan
    if 'ASAL' in locals() and 'CTEMP' in locals() and 'CORR_PRES' in locals():
        print('Calculating MLD')
        try:
            ii = np.where(np.isfinite(CORR_PRES) & np.isfinite(CTEMP) & np.isfinite(ASAL))
            mld_dict = mu.findmld(CORR_PRES[ii], CTEMP[ii], ASAL[ii], 0, rec_cut=10, pmax=20, \
                              logging=logging, verbose=verbose)
            MLD = mld_dict['mixeddp']
        except:
            print('MLD calculation failed')
            pass

    print('MLD: '+str(MLD))

    # take previous dive value    
    if np.isfinite(MLD):
        last_MLD = MLD
    else:
        print('Taking previous MLD dive value: '+str(last_MLD))
        MLD = last_MLD

    if MLD < MLD_min:
        print('MLD too shallow; dropping to '+str(MLD_min))
        MLD = MLD_min
 
    # PAR corrections and fitting
    PAR_FLAG = 0
    if 'CORR_DEPTH' in locals():
        use_insitu_par = False
        if 'PAR' in locals():
            use_insitu_par = True
            # convert to W/m2
            PAR = PAR*float(CONFIG_DICT['PAR_conversion'])

            dd = np.where((CORR_DEPTH> 50.0))
            try:
                PAR = PAR - np.nanmin(PAR[dd])
            except:
                pass

        if int(CONFIG_DICT['force_use_EO_par'])==1:
            print('Forcing to use EO PAR')
            use_insitu_par = False

        if use_insitu_par:
            print('Using glider PAR')

            CORR_PAR = PAR.copy()
            CORR_PAR[CORR_PAR<0]=0.0
            CORR_PAR[CORR_PAR>1e3]=np.nan
            E_0_plus = E_0_minus = np.nanmax(CORR_PAR)
            PAR_FLAG = 1
            
            print('Default (max par) E_0_minus:'+str(E_0_minus))
            try:
                ii = np.where(np.isfinite(CORR_DEPTH) & np.isfinite(np.log10(CORR_PAR)))
                if sum(CORR_PAR[ii]) != 0:
                    weights = np.sqrt(CORR_PAR[ii])
                    KDPAR, SURF_PAR = np.polyfit(CORR_DEPTH[ii], np.log(CORR_PAR[ii]), 1, w=weights)
                    if KDPAR >= -0.01:
                        CORR_PAR = CORR_PAR*0.0
                    else:
                        CORR_PAR = np.exp(SURF_PAR)*np.exp(KDPAR*CORR_DEPTH)
                    # fit to surface
                    E_0_minus = np.exp(SURF_PAR)
                else:
                    KDPAR = np.nan
                print('Extrapolated PAR across depth record')
            except:
                KDPAR = np.nan
                print('Failed to extrapolate PAR across depth record')
                pass

            is_night, is_day, is_bad, is_good, \
              is_no_DCM_night, is_day_good_PAR = \
              ct.profile_specifics(np.nanmean(TIME),CONFIG_DICT['t_ref'],\
                                       np.nanmean(CORR_LATITUDE),np.nanmean(CORR_LONGITUDE),\
                                       CORR_DEPTH,glider_bathy,[],CORR_PAR,\
                                       correct_time=correct_time,to_UTC=0,skip_chl=True)
            if is_night:
                print('Nighttime')
                E_0_minus = E_0_plus = 0.0
                CORR_PAR = CORR_PAR * 0.0

            # get Fresnel reflectances: Hemsley et al., 2015
            try:
                ii = np.where((np.isfinite(CTEMP)) & (np.isfinite(CORR_DEPTH)))[0]
                subset_depth = CORR_DEPTH[ii]
                subset_ctemp = CTEMP[ii]
                subset_asal = ASAL[ii]
                SST = subset_ctemp[subset_depth == np.nanmin(subset_depth)]
                SSS = subset_asal[subset_depth == np.nanmin(subset_depth)]
            except:
                # assume minimal dependency here and use mean global values
                SST = 16.1
                SSS = 35.0

            r_tot,solzen = ct.fresnel_refl(np.nanmean(CORR_LATITUDE),\
                                           np.nanmean(CORR_LONGITUDE),\
                                           np.nanmean(TIME),tref,\
                                           np.nanmin(CORR_DEPTH),\
                                           CORR_PAR,is_day_good_PAR,\
                                           traj_WSPD,\
                                           SST,SSS,correct_time=correct_time)

            # get above surface (E0) irradiance: Hemsley et al., 2015
            E_0_plus = E_0_minus
            try:
                E_0_plus = ct.get_E0(E_0_minus,r_tot)[0]
            except:
                pass

        else:
            # make the exponential decay. Correct KD490 to KDPAR (though 1:1 not end of world)
            # https://www.sciencedirect.com/science/article/abs/pii/S0034425712003847
            # http://www.obs-vlfr.fr/Boussole/html/publications/pubs/Saulquin_etal_RSE_2013.pdf
            print('Using PAR from trajectory file')
            
            # create the attentuation array
            if np.isfinite(traj_KD490):
                print('Using KD490 from trajectory file')
                KD490 = traj_KD490
                if KD490 <= 0.115:
                    KDPAR = 4.6051*KD490 / (6.07*KD490 + 3.2)
                else:
                    KDPAR = 0.81*KD490**0.8256
                PAR_FLAG = 2
            else:
                # KDPAR = (ln(PAR(0)) - ln(par(ZEU)))/ZEU
                KDPAR = 4.60517/derive_Lee_ZEU(np.nanmax(CHLA))
                PAR_FLAG = 3

            CORR_PAR = traj_PAR * np.exp(-1 * KDPAR * CORR_DEPTH)

            is_night, is_day, is_bad, is_good, \
              is_no_DCM_night, is_day_good_PAR = \
              ct.profile_specifics(np.nanmean(TIME),CONFIG_DICT['t_ref'],\
                                       np.nanmean(CORR_LATITUDE),np.nanmean(CORR_LONGITUDE),\
                                       CORR_DEPTH,glider_bathy,[],CORR_PAR,\
                                       correct_time=correct_time,to_UTC=0,skip_chl=True)

            E_0_plus = E_0_minus = traj_PAR
      
        print('KDPAR:                     '+str(KDPAR)) 
        print('Traj PAR:                  '+str(traj_PAR)) 
        print('Corrected (Z=0) E_0_minus: '+str(E_0_minus))
        
        # sanity corrections:
        if E_0_plus < 0: E_0_plus = 0
        if E_0_plus > 5*E_0_minus: E_0_plus = E_0_minus
        if E_0_plus > 250: E_0_plus = E_0_minus
        print('Corrected E_0_plus:        '+str(E_0_plus))
    else:
        print('No depth record.....cannot calculate PAR')
 
    # apply CHLA calibration: this is for Eltanin, Orca, Melonhead: re-write to remove manual coeffs
    if 'FLUORESCENCE_CHLA' in CONFIG_DICT['allowed_vars']:
        print('Calibrating CHLA....')
        
        if 'Melonhead' in nc_file:
            # Melonhead: have cal cert
            CHLA = 0.0121*(CHLA-43)
        elif 'Eltanin' in nc_file:
            # Eltanin: have cal cert
            CHLA = 0.0118*(CHLA-48)
        elif 'Orca' in nc_file: 
            # Orca: have cal cert
            CHLA = 0.0133*(CHLA-51)
        else:
            print('Unknown glider!')
            print('Please provide calibration coeffs as none are being applied and you are working with raw counts!')

        CHLA[CHLA > 1e5] = np.nan

    # fill CHLA gaps if they exist
    ii = np.where((np.isfinite(CORR_DEPTH)) & (np.isfinite(CHLA)))
    try:
        fn = interp1d(CORR_DEPTH[ii], CHLA[ii], fill_value="extrapolate")
        CHLA = fn(CORR_DEPTH)
    except:
        pass

    # calculate ZEU
    ZEU = np.nan
    ZEU_FLAG = 0
    if 'CORR_DEPTH' in locals() and 'CORR_PAR' in locals():
        print('Calculating ZEU')
        try:
            if 'PAR' in var_dict.keys():
                zz = np.where((PAR >= (E_0_minus/100.0)))
                ZEU_FLAG = 1
            else:
                zz = np.where((CORR_PAR >= (E_0_minus/100.0)))
                ZEU_Flag = 2

            ZEU = np.nanmax(CORR_DEPTH[zz])
            good_ZEU=True
        except:
            print('ZEU calculation failed, using Lee at el.')
            good_ZEU=False

        if not good_ZEU:
            try:
                if 'CHLA' in var_dict.keys():
                    ZEU = derive_Lee_ZEU(np.nanmax(CHLA[abs(CORR_DEPTH) < abs(mld_min)]))
                    ZEU_FLAG = 3
                else:
                    ZEU = derive_Lee_ZEU(traj_CHLA)
                    ZEU_FLAG = 4
            except:
                print('No ZEU calculation possible')
                pass

    # take previous dive value
    if np.isfinite(ZEU):
        last_ZEU = ZEU
    else:
        print('Taking previous ZEU dive value: '+str(last_MLD))
        ZEU = last_ZEU

    if np.isfinite(np.nanmean(CORR_LATITUDE)) and np.isfinite(np.nanmean(CORR_LONGITUDE)):
        is_night, is_day, last_sunrise, next_sunset = \
                  ct.glider_times(np.nanmean(CORR_LATITUDE), np.nanmean(CORR_LONGITUDE),\
                  CONFIG_DICT['t_ref'], np.nanmean(TIME), to_UTC=0, correct_time=correct_time)
    else:
        is_day = True
    
    if is_day:
        print('Zeu: '+str(ZEU)+ ' (flag: '+str(ZEU_FLAG)+')')
    else:
        ZEU = 0.0
        ZEU_FLAG = 5
        print('Night-time')
        print('Zeu: '+str(ZEU)+ ' (flag: '+str(ZEU_FLAG)+')')

    if 'SCATTER' in var_dict.keys():
        print('Correcting scatter')
        CORR_SCATTER = SCATTER.copy()
    else:
        CORR_SCATTER = CORR_BLANK.copy()

    # set up new CHL variables
    CORR_CHLA = CHLA.copy()
  
    # ditch bad data
    CORR_CHLA[CORR_CHLA <= 0.0] = 0.0
    CORR_SCATTER[CORR_SCATTER <= 0.0] = 0.0

    PROFILE_NUMBER = var_dict["PROFILE_NUMBER"]
    
    if use_Xing:
        if 'CHLA' in var_dict.keys() and 'CORR_DEPTH' in var_dict.keys():
            print('Correcting CHLA with Xing quenching')
            #  Xing et al., 2012:
            if is_day:
                print('Daytime correcting...')
                CORR_CHLA, method_success = fcorr.fluor_correction_Xin(PROFILE_NUMBER,TIME,\
                                    CORR_CHLA,MLD,CORR_DEPTH,verbose=True,\
                                    logging=logging,debug=debug)
            else:
                print('Nighttime; no correction')
                method_success = True  
            quench_method_used = 'Xing'

    if use_Biermann:
        if 'CHLA' in var_dict.keys() and 'CORR_DEPTH' in var_dict.keys():
            print('Correcting CHLA with Biermann quenching')
            #  Biermann et al., 2015:
            if is_day:
                print('Daytime correcting...')
                CORR_CHLA, method_success = fcorr.fluor_correction_Bie(PROFILE_NUMBER,TIME,\
                                    CORR_CHLA,ZEU,CORR_DEPTH,verbose=True,\
                                    logging=logging,debug=debug)
            else:
                print('Nighttime; no correction')
                method_success = True
            quench_method_used = 'Biermann'

    if use_Swart:
        if 'CHLA' in var_dict.keys() and 'SCATTER' in var_dict.keys():
            print('Correcting CHLA with Swart quenching')        
            #  Swart et al., 2015:
            if is_day:
                 print('Daytime correcting...')
                 CORR_CHLA, method_success = fcorr.fluor_correction_Swa(PROFILE_NUMBER,TIME,\
                                      CORR_CHLA,ZEU,CORR_DEPTH,CORR_SCATTER,verbose=True,\
                                      logging=logging)
            else:
                print('Nighttime; no correction')
                method_success = True
            quench_method_used = 'Swart'

    if use_Hemsley:
        if 'CHLA' in var_dict.keys() and 'SCATTER' in var_dict.keys() \
          and 'DEPTH' in var_dict.keys() and 'PAR' in var_dict.keys():
            print('Correcting CHLA with Hemsley quenching: part 1')
            is_night, is_day, is_bad, is_good, \
              is_no_DCM_night, is_day_good_PAR = \
              ct.profile_specifics(np.nanmean(TIME),CONFIG_DICT['t_ref'],\
              np.nanmean(CORR_LATITUDE),np.nanmean(CORR_LONGITUDE),\
              CORR_DEPTH,glider_bathy,CORR_CHLA,CORR_PAR,\
              correct_time=correct_time,to_UTC=0)
            quench_method_used = 'Hemsley'

    print('Writing out corrected data to: ' + nc_file)
    nct.write_corrected_to_file(nc_file,CORR_LATITUDE,'LATITUDE_CORRECTED','TIME')
    nct.write_corrected_to_file(nc_file,CORR_LONGITUDE,'LONGITUDE_CORRECTED','TIME')
    nct.write_corrected_to_file(nc_file,CORR_PRES,'PRES_CORRECTED','TIME')
    nct.write_corrected_to_file(nc_file,CORR_DEPTH,'DEPTH_CORRECTED','TIME')
    nct.write_corrected_to_file(nc_file,ASAL,'ABSOLUTE_SALINITY','TIME')
    nct.write_corrected_to_file(nc_file,CTEMP,'CONSERVATIVE_TEMPERATURE','TIME')
    try:
        nct.write_corrected_to_file(nc_file,CORR_PAR,'DOWNWELLING_PAR_CORRECTED','TIME')
    except:
        nct.write_corrected_to_file(nc_file,CORR_BLANK,'DOWNWELLING_PAR_CORRECTED','TIME')
    nct.write_corrected_to_file(nc_file,CORR_SCATTER,'BACKSCATTER_CORRECTED','TIME')
    nct.write_corrected_to_file(nc_file,np.ones(len(TIME))*MLD,'MIXED_LAYER_DEPTH','TIME')
    nct.write_corrected_to_file(nc_file,np.ones(len(TIME))*ZEU,'EUPHOTIC_DEPTH','TIME')
    nct.write_corrected_to_file(nc_file,np.ones(len(TIME))*ZEU_FLAG,'EUPHOTIC_DEPTH_FLAG','TIME')
    nct.write_corrected_to_file(nc_file,np.ones(len(TIME))*PAR_FLAG,'DOWNWELLING_PAR_CORRECTED_FLAG','TIME')
    nct.write_corrected_to_file(nc_file,CORR_CHLA,'CHLA_CORRECTED','TIME')

    if debug:
        fig = plt.figure()
        plt.rcParams.update({'font.size': 10})
        gs = gridspec.GridSpec(1,3)
        ax = plt.subplot(gs[0, 0])
        try:
            plt.scatter(CHLA,CORR_DEPTH*-1,130,color='k',zorder=1)
            plt.scatter(CORR_CHLA,CORR_DEPTH*-1,50,color='g',zorder=2)
            plt.plot(CORR_DEPTH*0,CORR_DEPTH*-1,'k--')
            plt.ylim([np.nanmin(CORR_DEPTH*-1),0.0])
            minval = np.nanmin(CHLA)
            maxval = np.nanmax(CORR_CHLA)*1.1
            plt.xticks([maxval/2,maxval])

            plt.plot([minval, maxval],[ZEU*-1, ZEU*-1],'g--')
            plt.plot([minval, maxval],[MLD*-1, MLD*-1],'k--')

            if is_night:
                plt.title('Nighttime profile')
            else:
                plt.title('Daytime profile')
        except:
            pass

        ax = plt.subplot(gs[0, 1])
        try:
            plt.scatter(CORR_SCATTER,PRES*-1,color='r')
            plt.ylim([np.nanmin(PRES*-1),0.0])
            minval = np.nanmin(CORR_SCATTER)/1.1
            maxval = np.nanmax(CORR_SCATTER)*1.1
            plt.xticks([maxval/2,maxval])
            plt.xlim([minval,maxval])

            plt.plot([minval, maxval],[ZEU*-1, ZEU*-1],'g--')
            plt.plot([minval, maxval],[MLD*-1, MLD*-1],'k--')

        except:
            pass

        ax = plt.subplot(gs[0, 2])
        try:
            ii = np.where(np.isfinite(CORR_PAR) & np.isfinite(CORR_PRES) & (CORR_PAR>0.0))[0]
            x = CORR_PRES[ii]
            y = CORR_PAR[ii]
            # y = Ae^Bx so fit x against Log(Y)
            a,b = np.polyfit(x, np.log(y), 1, w=np.sqrt(y))
            xvals = np.linspace(0,np.nanmax(PRES),100) 
            plt.plot(np.exp(b)*np.exp(a*xvals),xvals*-1,'b--')
            if 'PAR' in var_dict.keys():
                plt.scatter(PAR, PRES*-1,130,color='k',zorder=1)
            plt.scatter(CORR_PAR,CORR_PRES*-1,50,color='b',zorder=2)
            plt.ylim([np.nanmin(CORR_PRES*-1),0.0])
            maxval = max([np.nanmax(CORR_PAR)*1.1, E_0_plus*1.1])

            plt.plot([0, maxval],[ZEU*-1, ZEU*-1],'g--')
            plt.plot([0, maxval],[MLD*-1, MLD*-1],'k--')

            if 'PAR' in var_dict.keys():
                plt.plot(np.ones(len(PRES[ii]))*np.nanmax(PAR)/100.0, PRES[ii]*-1, color='0.5', linewidth=5, zorder=3)
            plt.plot(np.ones(len(PRES[ii]))*np.nanmax(CORR_PAR)/100.0, PRES[ii]*-1, 'b--', linewidth=1, zorder=4)

            plt.xlim([maxval*-0.1, maxval])
            plt.xticks([0.0, maxval*0.5,maxval])
            plt.title('PAR_FLAG: '+str(PAR_FLAG) + ' ZEU_FLAG: '+str(ZEU_FLAG))
        except:
            pass

        fname_plt = os.path.basename(nc_file.replace('.nc','.png'))
        try:
            plt.savefig(fname_plt)
        except:
            pass
        plt.close()

    return success, is_night, is_day, is_bad, is_good, is_no_DCM_night,\
           is_day_good_PAR,E_0_plus, quench_method_used, last_MLD, last_ZEU

############################# CALCULATING VARIABLES ############################

def derive_altim_vars(nc_file, variable, TRA_CONFIG, lat_EO, logging=None,\
                      verbose=False):

    nc_fid = Dataset(nc_file, 'r')
    for ALTIM_var in TRA_CONFIG[variable]['vars']:
        db.shout('Getting: '+ALTIM_var, logging=logging, 
                  verbose=verbose)
            
        VAR,rlat_EO = get_var(nc_fid,ALTIM_var,lat_EO)
        if ALTIM_var == 'ugos':
            UGOS = VAR.copy()
        elif ALTIM_var == 'vgos':
            VGOS = VAR.copy()
        elif ALTIM_var == 'ugosa':
            UGOSA = VAR.copy()
        elif ALTIM_var == 'vgosa':
            VGOSA = VAR.copy()
        elif ALTIM_var == 'sla':
            SLA = VAR.copy()
        elif ALTIM_var == 'adt':
            ADT = VAR.copy()

    EKE=((UGOSA*100)**2+(VGOSA*100)**2)/2
    TKE=((UGOS*100)**2+(VGOS*100)**2)/2
    MKE=TKE-EKE

    nc_fid.close()

    return UGOS, VGOS, UGOSA, VGOSA, SLA, ADT, EKE, MKE, TKE, rlat_EO

def derive_atmos_vars(MODULE_DICT, nc_file, variable, TRA_CONFIG, lat_EO, \
                      logging=None, verbose=False):

    nc_fid = Dataset(nc_file, 'r')
    for ECMWF_var in TRA_CONFIG[variable]['vars']:
        db.shout('Getting: '+ECMWF_var, logging=logging, 
                  verbose=verbose)
            
        VAR,rlat_EO = get_var(nc_fid,ECMWF_var,lat_EO)
        if ECMWF_var == 'u10':
            windU = VAR.copy()
            windV,rlat_EO = get_var(nc_fid,'v10',lat_EO)
            # wspd calculation
            WSPD = (windU**2+windV**2)**0.5
        elif ECMWF_var == 'tcc':
            CLOUD = VAR.copy()
        elif ECMWF_var == 'msl':
            MSLP = VAR/100
        elif ECMWF_var == 'tco3':
            # rough conversion to Dobson (assume STP)
            O3 = VAR * 1000 / float(MODULE_DICT['O3_mol']) \
                 *float(MODULE_DICT['avogadro']) \
                 /float(MODULE_DICT['Dobson_conversion'])
        elif ECMWF_var == 'tcwv':
            # rough conversion to cm.cm-2 (assume STP)
            TCWV = VAR / (100*100)*1000
        elif ECMWF_var == 't2m':
            t2m = VAR.copy()
            d2m,rlat_EO = get_var(nc_fid,'d2m',lat_EO)
            # calc relative humidity
            RH    = 100*d2m/t2m

    nc_fid.close()

    return WSPD, CLOUD, MSLP, O3, TCWV, RH, rlat_EO

def derive_sst_vars(nc_file, variable, TRA_CONFIG, lat_EO, logging=None,\
                      verbose=False):

    nc_fid = Dataset(nc_file, 'r')
    for SST_var in TRA_CONFIG[variable]['vars']:
        db.shout('Getting: '+SST_var, logging=logging, 
                  verbose=verbose)

        VAR,rlat_EO = get_var(nc_fid,SST_var,lat_EO)
        if SST_var == 'thetao':
            if np.nanmean(VAR) > 100:
                SST = VAR - 273.15
            else:
                SST=VAR.copy()
        elif SST_var == 'so':
            SSS = VAR.copy()
        elif SST_var == 'mlotst':
            MLD = VAR.copy()

    nc_fid.close()

    return SST, SSS, MLD, rlat_EO

def derive_par_vars(nc_file, variable, TRA_CONFIG, lat_EO, logging=None,\
                      verbose=False):

    nc_fid = Dataset(nc_file, 'r')
    for PAR_var in TRA_CONFIG[variable]['vars']:
        db.shout('Getting: '+PAR_var, logging=logging, 
                  verbose=verbose)
        PAR,rlat_EO = get_var(nc_fid,PAR_var,lat_EO)

    nc_fid.close()

    return PAR, rlat_EO

def derive_chl_vars(nc_file, variable, TRA_CONFIG, lat_EO, logging=None,\
                      verbose=False):

    nc_fid = Dataset(nc_file, 'r')
    for CHL_var in TRA_CONFIG[variable]['vars']:
        db.shout('Getting: '+CHL_var, logging=logging, 
                  verbose=verbose)
        CHL,rlat_EO = get_var(nc_fid,CHL_var,lat_EO)

    nc_fid.close()

    ZEU = derive_Lee_ZEU(CHL)

    return CHL, ZEU, rlat_EO

def derive_Lee_ZEU(CHL):
    # lee et al., 2007
    ZEU = 34.0 * CHL**-0.39
    return ZEU   

############################# NETCDF READ/WRITE ################################

def get_var(nc_fid,my_var,fLAT_EO):
   
    fVAR = nc_fid.variables[my_var][:]
    if 'Masked' in str(type(fVAR)):
        fVAR     = fVAR.data
        fillval = nc_fid.variables[my_var]._FillValue
        fVAR[fVAR == fillval] = np.nan

    # check for latitude inversion
    if fLAT_EO[-1] < fLAT_EO[0]:
        fLAT_EO = fLAT_EO[::-1]
        fVAR = fVAR[:,::-1,:]

    return np.squeeze(fVAR),fLAT_EO

def create_netcdf_traj(TIME,time_name,LAT,lat_name,LON,lon_name,\
                       PROFILE,profile_name,\
                       out_file,fillval=-9999, logging=None, verbose=False):

    try:
        # create a new netCDF file for writing
        nc_file  = Dataset(out_file,'w',format='NETCDF4_CLASSIC')

        #define dimensions
        nc_file.createDimension(profile_name,len(PROFILE))

        #define variables
        nctime = nc_file.createVariable(time_name,np.float32,(profile_name))
        nclon  = nc_file.createVariable(lon_name,np.float32,(profile_name))
        nclat  = nc_file.createVariable(lat_name,np.float32,(profile_name))

        # Write data to variable
        nctime[:] = TIME
        nclon[:]  = LON
        nclat[:]  = LAT

        # Close the file.
        nc_file.close()
        os.chmod(out_file, 0o777)
      
        db.shout('SUCCESS  writing template netcdf file ' + out_file, \
                 logging=logging, verbose=verbose)
    except:
        db.shout('*** FAILURE writing template netcdf file ' + out_file, \
                 logging=logging, verbose=verbose, level='error')

def write_netcdf_traj(VAR,var_name,profile_name,\
                      out_file,fillval=-9999, logging=None, verbose=False):

    try:
        # create a new netCDF file for writing
        nc_file  = Dataset(out_file,'r+')

        #define variables
        ncV1   = nc_file.createVariable(var_name,np.float32,(profile_name),\
                 fill_value=fillval)

        # Write data to variable
        ncV1[:]   = VAR

        # Close the file.
        nc_file.close()
      
        db.shout('SUCCESS  writing output netcdf file ' + out_file, \
                 logging=logging, verbose=verbose)
    except:
        db.shout('*** FAILURE writing output netcdf file ' + out_file, \
                 logging=logging, verbose=verbose, level='error')

def define_concat_file(concat_file, nfiles, GLIDER_CONFIG,\
                       logging=None, verbose=False):

    success = True
    # read processing config file
    CONFIG_DICT = read_config_file(GLIDER_CONFIG,logging=logging)

    interp_bins = np.arange(float(CONFIG_DICT['depth_min']),\
                            float(CONFIG_DICT['depth_max'])+\
                            float(CONFIG_DICT['depth_bin']),\
                            float(CONFIG_DICT['depth_bin']))

    interp_depth = interp_bins[0:-1]
    profile_name = 'profile'
    depth_name   = 'depth'
    allowed_vars = list(CONFIG_DICT['allowed'].split(','))

    if os.path.exists(concat_file):
        os.remove(concat_file)

    try:
        # create a new netCDF file for writing
        nc_file  = Dataset(concat_file,'w',format='NETCDF4_CLASSIC')

        #define dimensions
        nc_file.createDimension(profile_name,None)
        nc_file.createDimension(depth_name,len(interp_depth))

        #define variables
        for nc_var in allowed_vars:
            cv = nc_file.createVariable(nc_var,\
                                        np.float32,(profile_name,depth_name))

        # make soace for profile number
        cv = nc_file.createVariable('profile_number',\
                 np.float32,(profile_name,depth_name))

        # Close the file
        nc_file.close()
      
        db.shout('SUCCESS  writing template netcdf file ' + concat_file, \
                 logging=logging, verbose=verbose)
    except:
        success= False
        db.shout('*** FAILURE writing template netcdf file ' + concat_file, \
                 logging=logging, verbose=verbose, level='error')

    return success

def fill_concat_file(concat_file, nc_file, count, GLIDER_CONFIG,\
                       logging=None, verbose=False):
    success = True
    # read processing config file
    CONFIG_DICT = read_config_file(GLIDER_CONFIG,logging=logging)
    allowed_vars = list(CONFIG_DICT['allowed'].split(','))

    concat_fid = Dataset(concat_file,'r+')
    nc_fid     = Dataset(nc_file,'r')

    var_len = len(concat_fid.dimensions['depth'])
    concat_fid.variables['profile_number'][count,:] = \
                         np.ones(var_len)*nc_fid.variables['profile_number'][:]

    for variable in allowed_vars:
        try:
            concat_fid.variables[variable][count,:] = \
                                       nc_fid.variables[variable][:]
            db.shout('SUCCESS  writing '+nc_file +':'+variable+\
                     ' profile to netcdf file ' + concat_file, \
                     logging=logging, verbose=verbose)
        except:
            db.shout('*** FAILURE writing '+nc_file +':'+variable+\
                     ' profile to netcdf file ' + concat_file, \
                     logging=logging, verbose=verbose, level='error')

    concat_fid.close()
    nc_fid.close()

def check_for_profile_numbers(input_file,GLIDER_CONFIG):
    profile_num_exists = False
    CONFIG_DICT = read_config_file(GLIDER_CONFIG,logging=logging)

    try:
        nc_fid = Dataset(input_file, 'r')
        profile_nums = nc_fid.variables[CONFIG_DICT['profile_var_read']][:]
        nc_fid.close()
        profile_num_exists = True
    except:
        pass

    return profile_num_exists
#-EOF
