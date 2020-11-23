#!/usr/bin/env python
'''
Purpose:	Gets ECMWF monthly mean values for NRT climatology

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
import numpy as np
import fnmatch
import glob
import warnings
import subprocess

# add paths/tools
sys.path.append(os.path.dirname(os.path.realpath(__file__))+'/tools/')
sys.path.append(os.path.dirname(os.path.realpath(__file__))+'/cfg/')
import db_tools as db
import glider_tools as gt
from config_EO_trajectory import TRA_CONFIG
import download_tools as dlt

#-functions---------------------------------------------------------------------
def execute(command,logger=logging):
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, \
              stderr=subprocess.STDOUT)

    # Poll process for new output until finished
    while True:
        nextline = process.stdout.readline()
        if nextline == '' and process.poll() is not None:
            break
        logging.info(nextline)
        sys.stdout.flush()

    output = process.communicate()[0]
    exitCode = process.returncode

    if (exitCode == 0):
        return output
    else:
        raise ProcessException(command, exitCode, output)

#-default parameters------------------------------------------------------------
OUT_ROOT = '/data/datasets/Projects/AlterEco/'
DEFAULT_LOG_PATH = OUT_ROOT+'/Glider_data/logs/'

#-ARGS--------------------------------------------------------------------------

PARSER = argparse.ArgumentParser()
PARSER.add_argument('-v', '--verbose',\
                    action='store_true')
PARSER.add_argument('-l', '--log_path', type=str,\
                    default=DEFAULT_LOG_PATH,\
                    help='log file output path')
ARGS = PARSER.parse_args()

#-main--------------------------------------------------------------------------
if __name__ == "__main__":
    get_new_data = False
    verbose = ARGS.verbose
    # preliminary stuff
    LOGFILE = ARGS.log_path+"AlterEco_ECMWF_monthly_"+\
              datetime.datetime.now().strftime('%Y%m%d_%H%M')+".log"

    # set file logger
    try:
        if os.path.exists(LOGFILE):
            os.remove(LOGFILE)
        print("logging to: "+LOGFILE)
        logging.basicConfig(filename=LOGFILE, level=logging.DEBUG)
    except:
        print("Failed to set logger")
        sys.exit()

    # get all monthly ERAI means
    if get_new_data:
        for year in np.arange(1988,2018):
            var_file = 'ERAI_'+str(year)+'.nc'
            COORDS_LIST = ["-180","180","-90","90",str(year)+"-01-01 00:00:00",\
                           str(year)+"-12-31 23:59:59"]
            D0 = datetime.datetime.strptime(COORDS_LIST[4],'%Y-%m-%d %H:%M:%S')
            D1 = datetime.datetime.strptime(COORDS_LIST[5],'%Y-%m-%d %H:%M:%S')
            dlt.get_ecmwf(COORDS_LIST, D0, D1, var_file,clim=True, \
                                  logging=logging, verbose=verbose)

    # construct climatology
    for ii in np.arange(0,12):
        bashCommand = "ncra -O -d time,"+str(ii)+",,12 ERAI_????.nc ERAI_"+\
                      str(ii+1).zfill(2)+"_climatology.nc"
        print("running: "+bashCommand)
        try:
            execute(bashCommand,logging)
            if verbose:
                print('Process succeeded')
            logging.info('Process succeeded')
        except:
            if verbose:
                print('Process failed')
            logging.error('Process failed')

    bashCommand = "ncrcat ERAI_12_climatology* ERAI_??_climatology* ERAI_01_climatology* ERAI_monthly_climatology2.nc"
    try:
        execute(bashCommand,logging)
        if verbose:
            print('Process succeeded')
        logging.info('Process succeeded')
    except:
        if verbose:
            print('Process failed')
        logging.error('Process failed') 
