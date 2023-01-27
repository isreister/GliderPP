#!/usr/bin/env python
'''
Purpose:	Adds corrected chlorophyll and par to EGO files

Version: 	v2.0 05/2019

Ver. hist:	Current version support Seaglider netCDF data and EGO format
		gliders

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
import numpy as np
import fnmatch
import glob
import warnings
from netCDF4 import Dataset
import subprocess

#-messages----------------------------------------------------------------------
print('RUNNING: WARNINGS ARE SUPPRESSED')
warnings.filterwarnings('ignore')

#DEFAULT_EGO_FILE='/data/datasets/Projects/AlterEco/Glider_data/BODC_data/EGO/GL_20180508_Cabot_454_R.nc'
DEFAULT_EGO_FILE='/data/datasets/Projects/AlterEco/Glider_data/BODC_data/EGO/Cabot_20190312/Cabot_517_R.nc'
DEFAULT_OUT_DIR='/data/datasets/Projects/AlterEco/Glider_data/BODC_EGO_CAMPUS'

#-ARGS--------------------------------------------------------------------------

PARSER = argparse.ArgumentParser()
PARSER.add_argument('-e', '--EGO_file', type=str,\
                    help='EGO file',\
                    default=DEFAULT_EGO_FILE)
PARSER.add_argument('-o', '--output_dir', type=str,\
                    help='Output directory',\
                    default=DEFAULT_OUT_DIR)
ARGS = PARSER.parse_args()

#-main--------------------------------------------------------------------------
if __name__ == "__main__":

    glider_tags = os.path.basename(ARGS.EGO_file).split('_')
    glider_tag='EGO_'+glider_tags[-2]+'_'+glider_tags[-3]
    print('Glider tag: '+glider_tag)

    if os.path.exists(ARGS.EGO_file):
        target_file = os.path.join(ARGS.output_dir,os.path.basename(ARGS.EGO_file))
        print('Copying to: '+target_file)
        shutil.copy(ARGS.EGO_file,target_file)
        print('Done')
    else:
        print('No such file; exiting')
        sys.exit()

    # get time dimension length
    nc_fid = Dataset(target_file,'r')
    TIME = nc_fid.variables['TIME'][:]
    nc_fid.close()

    # add new variables to file
    new_variables = ['PROFILE_NUMBER',\
                     'LATITUDE_CORRECTED',\
                     'LONGITUDE_CORRECTED',\
                     'PRES_CORRECTED',\
                     'DEPTH_CORRECTED',\
                     'DOWNELLING_PAR_CORRECTED',\
                     'BACKSCATTER_CORRECTED',\
                     'CHLA_CORRECTED']

    aux_variables = ['DOWNWELLING_PAR_CORRECTED_SCALED',\
                     'CHLA_CORRECTED_SCALED']

    nc_fid = Dataset(target_file,'r+')
    for aux_variable in aux_variables:
        print('Creating space for aux variable, ' + aux_variable )
        nc_fid.createVariable(aux_variable, np.float32,('TIME'))
        # create required variables
        exec("%s=np.ones(len(TIME))*np.nan" % (aux_variable))
    nc_fid.close()
    print('Done')

    # find corrected variables from preprocessing
    print('Find necessary files....')
    corrected_files = []
    for root, _, filenames in os.walk('/data/datasets/Projects/AlterEco/Glider_data/BODC_preprocessed_data/EGO/Cabot_20190312/'):
        for filename in fnmatch.filter(filenames,os.path.basename(target_file).replace('.nc','*')):
            corrected_files.append(os.path.join(root, filename))

    # find corrected/scales variables from pp files
    corrected_chl_files = []
    corrected_ed_files = []
    for root, _, filenames in os.walk('/data/datasets/Projects/AlterEco/Glider_data/BODC_pp_data/EGO/Cabot_20190312/'+glider_tag+'/'):
        for filename in fnmatch.filter(filenames,'chl_profile*.corr'):
            corrected_chl_files.append(os.path.join(root, filename))
            corrected_ed_files.append(os.path.join(root, filename.replace('chl','ed')))           
    print('Done')

    print('Sort')
    corrected_files = sorted(corrected_files)
    corrected_chl_files = sorted(corrected_chl_files)
    corrected_ed_files = sorted(corrected_ed_files)
    print('Done')

    # concat all the netcdf variables together
    print('Concat netCDF variables')
    command='ncrcat -h -H -v '+','.join(new_variables)+' '+os.path.join(os.path.dirname(corrected_files[0]),'*fin.nc')+' '+target_file.replace('.nc','_CORRECTED.nc')
    print('Running: '+command)
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, \
              stderr=subprocess.STDOUT)
    process.wait()

    #print('Copy netCDF variables across')
    #command='ncks -A '+os.path.join(ARGS.output_dir,'tmp_corr.nc')+' '+target_file
    #print('Running: '+command)
    #process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, \
    #          stderr=subprocess.STDOUT)
    #process.wait()
