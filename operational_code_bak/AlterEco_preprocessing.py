#!/usr/bin/env python
'''
Purpose:	Preprocesses glider data. Performs the following operations
                1) concatenation of all files into single file
                2) fluorescence quneching; differing methods for DT/NRT

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
from scipy.interpolate import interp2d, interp1d
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import cm
import random
import string

# add paths/tools
sys.path.append(os.path.dirname(os.path.realpath(__file__))+'/tools/')
import db_tools as db
import glider_tools as gt
import fluor_correction as fcorr
import common_tools as ct

#-messages----------------------------------------------------------------------
print('RUNNING: WARNINGS ARE SUPPRESSED')
warnings.filterwarnings('ignore')

#-default parameters------------------------------------------------------------
OUT_ROOT = '/home/ben/shared/Linux_desktop/data/datasets/Projects/AlterEco/'
DEFAULT_LOG_PATH = OUT_ROOT+'/Glider_data/logs/'
DEFAULT_PLT_DIR = OUT_ROOT+'/Glider_data/plots/'
DEFAULT_CFG_DIR = os.path.dirname(os.path.realpath(__file__))+'/cfg/'
DEFAULT_CFG_FILE = DEFAULT_CFG_DIR+'config_main.py'

#-ARGS--------------------------------------------------------------------------

PARSER = argparse.ArgumentParser()
PARSER.add_argument('-cfg', '--config_file', type=str,\
                    default=DEFAULT_CFG_FILE,\
                    help='Config file')
PARSER.add_argument('-gcfg', '--glider_config_file', type=str,\
                    default=DEFAULT_CFG_DIR+'config_EGO.py',\
                    help='Glider config file')
PARSER.add_argument('-p', '--plot_dir', type=str,\
                    default=DEFAULT_PLT_DIR,\
                    help='Plot plotting directory')
PARSER.add_argument('-v', '--verbose',\
                    action='store_true')
PARSER.add_argument('-l', '--log_path', type=str,\
                    default=DEFAULT_LOG_PATH,\
                    help='log file output path')
PARSER.add_argument("-pc", "--proc_chain",\
                    type=str,\
                    default="NRT",\
                    help="processing chain type (NRT or DT)")
PARSER.add_argument('-ag', '--allowed_gliders', type=str,\
                    default=[],\
                    help='allowed gliders')
ARGS = PARSER.parse_args()

#-main--------------------------------------------------------------------------
if __name__ == "__main__":
  
    debug = False
    reprocess = True
    allowed_gliders = ["EGO_441_Cook","EGO_454_Cabot","EGO_477_Dolomite",\
                       "EGO_478_Eltanin","EGO_481_Kelvin","EGO_494_Stella",\
                       "EGO_499_Dolomite","EGO_500_Coprolite","EGO_517_Cabot",\
                       "UEA_579_humpback"]

    if ARGS.allowed_gliders:
        allowed_gliders = [ARGS.allowed_gliders]
        print(allowed_gliders)

    verbose = ARGS.verbose

    # need this is launching lots of jobs!
    RAND_STRING = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))

    # preliminary stuff
    LOGFILE = ARGS.log_path+"AlterEco_preprocessing_"+RAND_STRING+'_'+\
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

    # read processing config file
    MODULE_DICT = {}
    try:
        logging.info("Reading configuration file...")
        with open(ARGS.config_file) as myfile:
            for line in myfile:
                if '#' in line:
                    continue
                else:
                    name, var = line.partition("=")[::2]
                    MODULE_DICT[name.strip()] = str(var.replace('\n', ''))
    except:
        logging.error("Failed to read configuration file")
        sys.exit()

    master_database = MODULE_DICT['database_NRT'] # primary
    all_databases = [MODULE_DICT['database_NRT'], MODULE_DICT['database_DT']]

    # get database statuses
    glider_type, glider_prefix, glider_number, glider_name, file_names, \
        is_staged, stage_dir, is_EO, is_preproc, is_spectral, is_corrected, \
        is_pp, is_postproc = db.get_status(master_database,\
        MODULE_DICT['table_name'],\
        MODULE_DICT['glider_type_column'],\
        MODULE_DICT['glider_prefix_column'],\
        MODULE_DICT['glider_number_column'],\
        MODULE_DICT['glider_name_column'],\
        MODULE_DICT['file_name_column'],\
        MODULE_DICT['stage_column'],\
        MODULE_DICT['stage_dir_column'],\
        MODULE_DICT['EO_column'],\
        MODULE_DICT['preproc_column'],\
        MODULE_DICT['spectral_column'],\
        MODULE_DICT['corrected_column'],\
        MODULE_DICT['pp_column'],\
        MODULE_DICT['postproc_column'],\
        logging=logging, verbose=verbose)

    # convert database keys to integer arrays
    is_EO_int = np.asarray(is_EO).astype(int)
    is_preproc_int = np.asarray(is_preproc).astype(int)

    glider_tags = [str(m[0])+'_'+str(n[0])+'_'+str(p[0]) \
                   for m,n,p in zip(glider_prefix,glider_number,glider_name)]

    for count in np.arange(len(is_EO_int)):

        glider_tag = glider_tags[count]
        print(glider_tag)
        if glider_tag not in allowed_gliders:
            continue

        if reprocess:
            pass
        else:
            if is_EO_int[count] == 1 and is_preproc_int[count] == 0:
                print('Preprocessing: '+ stage_dir[count][0])
            else:
                continue
 
        # determine glider type:
        if glider_tag.split('_')[0] == 'sg':
            GLIDER_CONFIG = DEFAULT_CFG_DIR+'config_seaglider.py'
            match_tag = '*'+glider_tag.split('_')[0]+glider_tag.split('_')[1]+'*.nc'            
        elif glider_tag.split('_')[0] == 'EGO':
            GLIDER_CONFIG = DEFAULT_CFG_DIR+'config_EGO.py'
            match_tag = '*'+glider_tag.split('_')[2]+'_'+glider_tag.split('_')[1]+'*.nc'
        elif glider_tag.split('_')[0] == 'UEA':
            GLIDER_CONFIG = DEFAULT_CFG_DIR+'config_UEA.py'
            match_tag = '*_sg'+glider_tag.split('_')[1]+'*.nc'
        else:
            GLIDER_CONFIG = DEFAULT_CFG_DIR+'config_slocum.py'
            continue

        if 'ELTANIN' in glider_tag.upper() and 'EGO' in stage_dir[count][0]:
            GLIDER_CONFIG = DEFAULT_CFG_DIR+'config_EGO_ELTANIN.py'
            print('Swapping config to Eltanin....')

        if ARGS.glider_config_file:
            GLIDER_CONFIG = ARGS.glider_config_file

        print('------------------------------------------')
        print('Using: '+GLIDER_CONFIG)
        print('------------------------------------------')

        # create pre-proc directory structure
        preproc_dir = stage_dir[count][0].replace(MODULE_DICT['staged_dir'], \
                                         MODULE_DICT['preproc_dir'])

        os.chmod(os.path.dirname(preproc_dir), 0o777)
        if not os.path.exists(preproc_dir):
            os.makedirs(preproc_dir)
            os.chmod(preproc_dir, 0o777)

        # find matching files in staged dir
        preprocessing_files = glob.glob(os.path.join(stage_dir[count][0],match_tag))
        
        # get EO trajectory data files
        EO_dir = os.path.join(MODULE_DICT['EO_dir'],glider_tag,ARGS.proc_chain)
        EO_trajectory_files = glob.glob(os.path.join(EO_dir,'*traj.nc'))      
        
        # init EO trajectory data
        PAR_traj = np.ones(len(preprocessing_files))*np.nan
        KD490_traj = np.ones(len(preprocessing_files))*np.nan
        CHLA_traj = np.ones(len(preprocessing_files))*np.nan
        WSPD_traj = np.ones(len(preprocessing_files))*np.nan
        RH_traj = np.ones(len(preprocessing_files))*np.nan
        TCWV_traj = np.ones(len(preprocessing_files))*np.nan
        O3_traj = np.ones(len(preprocessing_files))*np.nan
        MSLP_traj = np.ones(len(preprocessing_files))*np.nan
        CLOUD_traj = np.ones(len(preprocessing_files))*np.nan
        ZEU_traj = np.ones(len(preprocessing_files))*np.nan

        # dealing with the Hemsley case....
        # read processing config file
        CONFIG_DICT = gt.read_config_file(GLIDER_CONFIG,logging=logging)

        correct_time = True
        if CONFIG_DICT['t_base'] == 'matlab':
            print('Correcting from Matlab timebase')
            correct_time = False
        tref = CONFIG_DICT['t_ref']

        for EO_trajectory_file in EO_trajectory_files:
            print(EO_trajectory_file)
            if 'PAR' in EO_trajectory_file:
                nc_fid   = Dataset(EO_trajectory_file, 'r')
                PAR_traj = nc_fid.variables['PAR'][:]
                LON_traj = nc_fid.variables[CONFIG_DICT['lon_var']][:]
                LAT_traj = nc_fid.variables[CONFIG_DICT['lat_var']][:]
                nc_fid.close()
            if 'KD490' in EO_trajectory_file:
                nc_fid   = Dataset(EO_trajectory_file, 'r')
                KD490_traj = nc_fid.variables['KD490'][:]
                LON_traj = nc_fid.variables[CONFIG_DICT['lon_var']][:]
                LAT_traj = nc_fid.variables[CONFIG_DICT['lat_var']][:]
                nc_fid.close()
            if 'CHL' in EO_trajectory_file:
                nc_fid   = Dataset(EO_trajectory_file, 'r')
                CHLA_traj = nc_fid.variables['CHL'][:]
                ZEU_traj = nc_fid.variables['ZEU'][:]
                LON_traj = nc_fid.variables[CONFIG_DICT['lon_var']][:]
                LAT_traj = nc_fid.variables[CONFIG_DICT['lat_var']][:]
                nc_fid.close()
            if 'SST' in EO_trajectory_file:
                nc_fid   = Dataset(EO_trajectory_file, 'r')
                SST_traj = nc_fid.variables['SST'][:]
                SSS_traj = nc_fid.variables['SSS'][:]
                MLD_traj = nc_fid.variables['MLD'][:]
                LON_traj = nc_fid.variables[CONFIG_DICT['lon_var']][:]
                LAT_traj = nc_fid.variables[CONFIG_DICT['lat_var']][:]
                nc_fid.close()
            if 'ALTIM' in EO_trajectory_file:
                nc_fid   = Dataset(EO_trajectory_file, 'r')
                UGOS_traj = nc_fid.variables['UGOS'][:]
                VGOS_traj = nc_fid.variables['VGOS'][:]
                UGOSA_traj = nc_fid.variables['UGOSA'][:]
                VGOSA_traj = nc_fid.variables['VGOSA'][:]
                SLA_traj = nc_fid.variables['SLA'][:]
                ADT_traj = nc_fid.variables['ADT'][:]
                EKE_traj = nc_fid.variables['EKE'][:]
                MKE_traj = nc_fid.variables['MKE'][:]
                TKE_traj = nc_fid.variables['TKE'][:]
                LON_traj = nc_fid.variables[CONFIG_DICT['lon_var']][:]
                LAT_traj = nc_fid.variables[CONFIG_DICT['lat_var']][:]
                nc_fid.close()
            if 'ATMOS' in EO_trajectory_file:
                nc_fid   = Dataset(EO_trajectory_file, 'r')
                WSPD_traj = nc_fid.variables['WSPD'][:]
                CLOUD_traj = nc_fid.variables['CLOUD'][:]
                MSLP_traj = nc_fid.variables['MSLP'][:]
                O3_traj = nc_fid.variables['O3'][:]
                TCWV_traj = nc_fid.variables['TCWV'][:]
                RH_traj = nc_fid.variables['RH'][:]                
                LON_traj = nc_fid.variables[CONFIG_DICT['lon_var']][:]
                LAT_traj = nc_fid.variables[CONFIG_DICT['lat_var']][:]
                nc_fid.close()

        # get GEBCO bathy
        bathy_file = '/home/ben/shared/Linux_desktop/home/Tools/DATA_SETS/GEBCO_2014_2D.nc'
        nc_fid = Dataset(bathy_file, 'r')
        blon = nc_fid.variables['lon'][:]
        blat = nc_fid.variables['lat'][:]
        xx = np.where((blon > np.nanmin(LON_traj)) & (blon < np.nanmax(LON_traj)))[0]
        yy = np.where((blat > np.nanmin(LAT_traj)) & (blat < np.nanmax(LAT_traj)))[0]
        BATHY = nc_fid.variables['elevation'][yy,xx]
        nc_fid.close()

        f = interp2d(blon[xx],blat[yy], BATHY, kind='cubic')
        glider_bathy = np.ones(np.shape(LON_traj))*np.nan
        for ii in np.arange(0,len(glider_bathy)):
            glider_bathy[ii] = f(LON_traj[ii],LAT_traj[ii])*-1

        # init Hemsley variables
        all_night = np.zeros(len(preprocessing_files))
        all_day = np.zeros(len(preprocessing_files))
        all_good = np.zeros(len(preprocessing_files))
        all_bad = np.zeros(len(preprocessing_files))
        all_no_DCM = np.zeros(len(preprocessing_files))
        all_day_PAR = np.zeros(len(preprocessing_files))
        E_0_plus = np.zeros(len(preprocessing_files))

        CHLA_surf1 = np.zeros(len(preprocessing_files))
        CHLA_surf2 = np.zeros(len(preprocessing_files))
        CHLA_surf3 = np.zeros(len(preprocessing_files))
        glider_HOUR = np.zeros(len(preprocessing_files))

        # loop through and perform corrections / derive variables
        traj_index = -1
        preprocessing_files = sorted(preprocessing_files)
        output_files = []
        all_quench_methods_used = []
        last_MLD = np.nan
        last_ZEU = np.nan

        for preprocessing_file in preprocessing_files:
            print(preprocessing_file)
            # most quenching methods are done on a profile by profile basis
            # Hemsley, however, is not. We need to preprocess the entire 
            # glider mission. In the first run, we need to know if profiles are
            # i) good, ii) nighttime, and iii) don't have a DCM.

            traj_index = traj_index + 1
            #if traj_index >= 10:
            #    continue
            
            # we do not work on the staged files....
            output_file = preprocessing_file.replace(MODULE_DICT['staged_dir'], \
                                         MODULE_DICT['preproc_dir'])

            output_file = output_file.replace('.nc',CONFIG_DICT['nc_tag'])            
 
            if os.path.exists(output_file):
                os.chmod(output_file, 0o777)
                os.remove(output_file)

            shutil.copy(preprocessing_file, output_file)
            output_files.append(output_file)

            success, all_night[traj_index], all_day[traj_index], \
              all_bad[traj_index], all_good[traj_index], \
              all_no_DCM[traj_index], all_day_PAR[traj_index],\
              E_0_plus[traj_index], quench_method_used, last_MLD, last_ZEU = \
              gt.preprocess_dive(output_file, GLIDER_CONFIG, \
                                 PAR_traj[traj_index], KD490_traj[traj_index], \
                                 CHLA_traj[traj_index],\
                                 glider_bathy[traj_index],WSPD_traj[traj_index], last_MLD, last_ZEU, \
                                 logging=logging, verbose=verbose, correct_time=correct_time)
            
            all_quench_methods_used.append(quench_method_used)

        if 'Hemsley' in all_quench_methods_used:
            print('Performing Hemsley correction: part 2')
            regress_profiles = np.where((all_good == 1) & (all_night == 1) & (all_no_DCM == 1))[0]
            correct_profiles = np.where((all_good == 1) & (all_day ==1))[0]

            hem_regress_profiles = []
            for regress_profile in regress_profiles:
                hem_regress_profiles.append(output_files[regress_profile])         

            hem_correct_profiles = []
            for correct_profile in correct_profiles:
                hem_correct_profiles.append(output_files[correct_profile])

            fcorr.fluor_correction_Hem(GLIDER_CONFIG,hem_regress_profiles,\
               hem_correct_profiles,glider_tag,logging=logging, verbose=verbose)

        # now we write out the required text files
        count = -1
        for output_file in sorted(output_files):
            print('Writing: ' + output_file)
            count = count + 1
            OUT_DIR = os.path.dirname(output_file).replace('preprocessed','pp')
            OUT_DIR = os.path.join(OUT_DIR,glider_tag)

            os.chmod(os.path.dirname(OUT_DIR), 0o777)
            if not os.path.exists(OUT_DIR):
                os.makedirs(OUT_DIR)
                os.chmod(OUT_DIR, 0o777)

            # read in the required variables
            nc_fid     = Dataset(output_file, 'r')
            PROFILE_NUMBERS = nc_fid.variables['PROFILE_NUMBER'][:]
            try:
                TIME = nc_fid.variables['TIME'][:]
            except:
                TIME = nc_fid.variables['time'][:]
            
            DEPTH = nc_fid.variables['DEPTH_CORRECTED'][:]
            LAT = nc_fid.variables['LATITUDE_CORRECTED'][:]
            LON = nc_fid.variables['LONGITUDE_CORRECTED'][:]
            CHLA = nc_fid.variables['CHLA_CORRECTED'][:]
            PAR = nc_fid.variables['DOWNWELLING_PAR_CORRECTED'][:]
            ZEU = nc_fid.variables['EUPHOTIC_DEPTH'][:]
            MLD = nc_fid.variables['MIXED_LAYER_DEPTH'][:]
            TEMP = nc_fid.variables['CONSERVATIVE_TEMPERATURE'][:]
            nc_fid.close()

            if 'Masked' in str(type(CHLA)):
                CHLA = np.ma.filled(CHLA, np.nan)

            if 'Masked' in str(type(PAR)):
                PAR = np.ma.filled(PAR, np.nan)
            
            ct.output_text(np.nanmean(PROFILE_NUMBERS),TIME,tref,DEPTH,CHLA,PAR,\
                  WSPD_traj[count],\
                  RH_traj[count],\
                  TCWV_traj[count],\
                  O3_traj[count],\
                  MSLP_traj[count],\
                  CLOUD_traj[count],\
                  CHLA_traj[count],\
                  ZEU_traj[count],\
                  E_0_plus[count],\
                  np.nanmean(MLD),\
                  np.nanmean(ZEU),\
                  LON,LAT,TEMP,OUT_DIR,'chl_profile','par_profile',all_day[count],\
                  verbose=verbose,logging=logging,correct_time=correct_time,\
                  outfile_suffix=CONFIG_DICT['correction_file_suffix']) 

#--EOF
