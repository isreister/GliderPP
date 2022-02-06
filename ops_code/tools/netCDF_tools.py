#!/usr/bin/env python
'''
Purpose:	Unspecified

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
from netCDF4 import Dataset
import numpy as np
import os

def ncdump(nc_fid, verb=True):
   '''
   ncdump outputs dimensions, variables and their attribute information.
   The information is similar to that of NCAR's ncdump utility.
   ncdump requires a valid instance of Dataset.

   Parameters
   ----------
   nc_fid : netCDF4.Dataset
       A netCDF4 dateset object
   verb : Boolean
       whether or not nc_attrs, nc_dims, and nc_vars are printed

   Returns
   -------
   nc_attrs : list
       A Python list of the NetCDF file global attributes
   nc_dims : list
       A Python list of the NetCDF file dimensions
   nc_vars : list
       A Python list of the NetCDF file variables
   '''
   def print_ncattr(key):
      """
      Prints the NetCDF file attributes for a given key

      Parameters
      ----------
      key : unicode
            a valid netCDF4.Dataset.variables key
      """
      try:
         print('\t\ttype:', repr(nc_fid.variables[key].dtype))
         for ncattr in nc_fid.variables[key].ncattrs():
            print('\t\t%s:' % ncattr, repr(nc_fid.variables[key].getncattr(ncattr)))
      except KeyError:
         print('\t\tWARNING: %s does not contain variable attributes' % key)

   # NetCDF global attributes
   nc_attrs = nc_fid.ncattrs()
   if verb:
      print('NetCDF Global Attributes:')
      for nc_attr in nc_attrs:
         print('\t%s:' % nc_attr, repr(nc_fid.getncattr(nc_attr)))
   nc_dims = [dim for dim in nc_fid.dimensions]  # list of nc dimensions
   # Dimension shape information.
   if verb:
      print('NetCDF dimension information:')
      for dim in nc_dims:
         print('\tName:', dim)
         print('\t\tsize:', len(nc_fid.dimensions[dim]))
         print_ncattr(dim)


   # Variable information; now supports groups
   nc_groups  = [group for group in nc_fid.groups]  # list of nc groups

   nc_vars_all=[]
   if nc_groups:
      for group in nc_fid.groups:
         nc_vars     = [var for var in nc_fid.groups[group].variables]  # list of nc variables
         nc_vars_all.append(nc_vars)
         if verb:
            print('NetCDF variable information:')
            for var in nc_vars:
               if var not in nc_dims:
                  print('\tName:', var)
                  print('\t\tdimensions:', nc_fid.groups[group].variables[var].dimensions)
                  print('\t\tsize:', nc_fid.groups[group].variables[var].size)
                  print_ncattr(var)
   else:
      nc_vars = [var for var in nc_fid.variables]  # list of nc variables
      nc_vars_all.append(nc_vars)
      if verb:
         print('NetCDF variable information:')
         for var in nc_vars:
            if var not in nc_dims:
               print('\tName:', var)
               print('\t\tdimensions:', nc_fid.groups[group].variables[var].dimensions)
               print('\t\tsize:', nc_fid.groups[group].variables[var].size)
               print_ncattr(var)

   return nc_attrs, nc_dims, nc_vars_all, nc_groups

def get_variables(nc_fid, nc_groups, nc_vars, thisvar, time_slice=0, depth_slice=0, subset=0,logging = None):
   #-get coords and data--------------------------------------------------------------------
   lon           = []
   lon_test      = []
   lat           = []
   time          = []
   DATA          = []
   units         = []
   meridian_flag = False
   datvarname    = 'blank'
   group_count   = 0

   if subset:
      if logging:
         logging.info('  >>> extracting subset')
      else:
         print('  >>> extracting subset')

   if not nc_groups:
      nc_groups='0'

   # for longitude to check for stupid grids
   for group in nc_groups:     
      for var in nc_vars[group_count]:           
         if var=='lon' or var=='longitude' or var=='lon_rho' or var=='NbLongitudes' or var=='X' or var=='x' or var=='lon_out' or var=='LONGITUDE' or var=='nav_lon':
            if logging:
               logging.info('Checking longitude variable = '+str(var))
            else:
               print('Checking longitude variable =',var)
            lonvarname = var[:]

            if nc_groups=='0':
               lon_test = nc_fid.variables[lonvarname][:]
            else:
               lon_test = nc_fid.groups[group].variables[lonvarname][:]

   if np.nanmax(lon_test) > 180:
      meridian_flag = True
      if logging:
         logging.info('Warning; longitude extends from '+str(np.nanmin(lon_test))+' to '+str(np.nanmax(lon_test)))
      else:
         print('Warning; longitude extends from '+str(np.nanmin(lon_test))+' to '+str(np.nanmax(lon_test)))

   # for coordinate variables
   for group in nc_groups:     
      for var in nc_vars[group_count]:
         if var=='lat' or var=='latitude'  or var=='lat_rho' or var=='NbLatitudes' or var=='Y' or var=='y' or var=='lat_out' or var=='LATITUDE' or var=='nav_lat':
            if logging:
               logging.info('Latitude variable  = '+str(var))
            else:
               print('Latitude variable  =',var)
            latvarname = var[:]

            if nc_groups=='0':
               lat        = nc_fid.variables[latvarname][:]
            else:
               lat        = nc_fid.groups[group].variables[latvarname][:]

            if subset:
               jj  = np.where((lat>=subset[2]) & (lat<= subset[3]))
               lat = lat[jj]               

            # catch all for the case where no variable name is passed, make nan array of same size of latitude
            data          = np.copy(lat)*np.nan
            
         if var=='lon' or var=='longitude' or var=='lon_rho' or var=='NbLongitudes' or var=='X' or var=='x' or var=='lon_out' or var=='LONGITUDE' or var=='nav_lon':
            if logging:
               logging.info('Longitude variable = '+str(var))
            else:
               print('Longitude variable =',var)
            lonvarname = var[:]

            if nc_groups=='0':
               lon    = nc_fid.variables[lonvarname][:]
            else:
               lon    = nc_fid.groups[group].variables[lonvarname][:]

            if subset:
               if meridian_flag:
                  if subset[0] < 0 and subset[1] < 0:
                     ii  = np.where((lon>=(subset[0]+360)) & (lon<=(subset[1]+360)))
                     lon = lon[ii]-360
                  else:
                     print('Fail! >> WRITE ME!')
               else:
                  ii  = np.where((lon>=subset[0]) & (lon<= subset[1]))
                  lon = lon[ii] 

         if var=='time':
            if logging:
               logging.info('Time variable      = '+str(var))
            else:
               print('Time variable      =',var)
            tvarname   = var[:]

            if nc_groups=='0':
               tsize    = nc_fid.variables[tvarname].shape
               time     = nc_fid.variables[tvarname][:]
            else:
               tsize    = nc_fid.groups[group].variables[tvarname].shape
               time     = nc_fid.groups[group].variables[tvarname][:]

   # for data variables
   if thisvar == []:
      if logging:
         logging.info('Data variable      = dummy (leaving function)' )
      else:
         print('Data variable      = dummy (leaving function)') 
      return lon,lat,time,[],[],[]   

   for group in nc_groups:     
      for var in nc_vars[group_count]:
         if thisvar and var==thisvar:
            if logging:
               logging.info('Data variable      = '+str(var))
            else:
               print('Data variable      =',var)     
            datvarname = var[:]
            plotname   = datvarname.replace(' ','')

            if nc_groups=='0':
               datsize    = nc_fid.variables[datvarname].shape
               if np.size(datsize) == 2:
                  if subset:
                     data       = nc_fid.variables[datvarname][jj[0],ii[0]]
                  else:
                     data       = nc_fid.variables[datvarname][:]
               elif np.size(datsize) == 3:
                  if subset:
                     data       = np.squeeze(nc_fid.variables[datvarname][time_slice,jj[0],ii[0]])
                  else:
                     data       = np.squeeze(nc_fid.variables[datvarname][time_slice,:,:])
               elif np.size(datsize) == 4:
                  if logging:
                     logging.info('Choosing depth-determined value: '+str(depth_slice))
                  else:
                     print('Choosing depth-determined value: '+str(depth_slice))
                  if subset:
                     data       = np.squeeze(nc_fid.variables[datvarname][time_slice,depth_slice,jj[0],ii[0]])
                  else:
                     data       = np.squeeze(nc_fid.variables[datvarname][time_slice,depth_slice,:,:])
            else:
               datsize    = nc_fid.groups[group].variables[datvarname].shape
               if np.size(datsize) == 2:
                  if subset:
                     data       = nc_fid.groups[group].variables[datvarname][jj[0],ii[0]]
                  else:
                     data       = nc_fid.groups[group].variables[datvarname][:]
               elif np.size(datsize) == 3:
                  if subset:
                     data       = np.squeeze(nc_fid.groups[group].variables[datvarname][time_slice,jj[0],ii[0]])
                  else:
                     data       = np.squeeze(nc_fid.groups[group].variables[datvarname][time_slice,:,:])
               elif np.size(datsize) == 4:
                  if logging:
                     logging.info('Choosing depth-determined value: '+str(depth_slice))
                  else:
                     print('Choosing depth-determined value: '+str(depth_slice))
                  if subset:
                     data       = np.squeeze(nc_fid.groups[group].variables[datvarname][time_slice,depth_slice,jj[0],ii[0]])
                  else:
                     data       = np.squeeze(nc_fid.groups[group].variables[datvarname][time_slice,depth_slice,:,:])

            data=data.astype(float)

            try:
               mask = data.mask

               # ditch the automatic mask
               data = data.data
            except:
               masked = False

            #-masking-- 
            try:
               fill = nc_fid.variables[datvarname]._FillValue
               data[np.where(data==fill)]=np.nan
               if logging:
                  logging.info('Applying fill value:    '+str(fill))
               else:
                  print('Applying fill value:    '+str(fill))
            except:
               data[np.isnan(data)]=np.nan

            try:      
               miss = nc_fid.variables[datvarname].missing_value
               data[np.where(data==miss)]=np.nan
               if logging:
                  logging.info('Applying missing value: '+str(miss))
               else:
                  print('Applying missing value: '+str(miss))
            except:
               data[np.isnan(data)]=np.nan

            #-units--
            try:
               units    = nc_fid.variables[datvarname].units
            except:
               units    = []

      #iterate group
      group_count=group_count +1

   return lon,lat,time,data,datvarname,units

def read_var(fname,vname):
   nc_fid  = Dataset(fname, 'r')
   fvar    = nc_fid.variables[vname][:]
   return fvar

def write_corrected_to_file(nc_file,var,var_name,dim,define_var=True):

    write_var = var.copy()
    os.chmod(nc_file,0o777)
    nc_fid = Dataset(nc_file,'r+')

    #define variables & write
    fill_value = 1e36

    if 'Masked' in str(type(write_var)):
        write_var = np.ma.filled(write_var, fill_value)

    succeed = False
    if define_var:
        try:
            ncV1 = nc_fid.createVariable(var_name,np.float32,(dim),\
                       fill_value=fill_value)
            ncV1[:] = write_var
            succeed = True
        except:
            pass

        try:
            ncV1 = nc_fid.createVariable(var_name,np.float32,(dim.lower()),\
                       fill_value=fill_value)
            ncV1[:] = write_var
            succeed = True
        except:
            pass

    if not define_var or succeed == False:
        write_var[np.isnan(write_var)] = fill_value
        nc_fid.variables[var_name][:] = write_var      

    # Close the file.
    nc_fid.close()
