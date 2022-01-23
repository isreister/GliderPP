#!/usr/bin/env python
'''
Purpose:	Stages MARS/NOC/BODC data from download directory to
            preprocessed directory ready for ingestion into the processing chain
            Bins allowed variables if requested.

Version: 	v1.0 10/2021

Author:		Ben Loveday, Plymouth Marine Laboratory
            Time Smyth, Plymouth Marine Laboratory

License:    See LICENCE.txt
'''
#-imports-----------------------------------------------------------------------
from __future__ import print_function
import os
import shutil
import datetime
import logging
import argparse
import numpy as np
import fnmatch
import glob
import warnings

# add paths/tools
sys.path.append(os.path.dirname(os.path.realpath(__file__))+'/tools/')
import db_tools as db
import glider_tools as gt

#-messages----------------------------------------------------------------------
print('RUNNING: WARNINGS ARE SUPPRESSED')
warnings.filterwarnings('ignore')

#-functions---------------------------------------------------------------------
def the_file_date(x):
    date_tag = os.path.basename(os.path.dirname(x))
    the_month_year = '01'+date_tag.split('_')[-1]
    try:
        val = datetime.datetime.strptime(the_month_year,'%d%b%y')
    except:
        val = datetime.datetime.strptime(the_month_year,'%d%B%y')
    return val

def process_file(database, input_file, output_file, GLIDER_CONFIG, \
                 MODULE_DICT, interp_flag=False, logging=None, verbose=False):
    '''
     Performs all necessary pre-processing operations on glider data
    '''

    good_flag = True
    try:
        #check to see if profile numbers exist already
        profiles_nums_exist = \
                          gt.check_for_profile_numbers(input_file,GLIDER_CONFIG)

        # dive splitting
        split_files = gt.split_dive_index(input_file,\
                                     output_file, GLIDER_CONFIG,\
                                     logging=logging, \
                                     profiles_nums_exist=profiles_nums_exist)

        logging.info("Split into: "+str(len(split_files))+" profiles")

        # interpolation onto depth levels (if required) and output
        for split_file in split_files:
            if interp_flag:
                gt.interpolate_dive(split_file, \
                                split_file.replace('.nc','_st_int.nc'),\
                                GLIDER_CONFIG, MODULE_DICT,\
                                interp_flag=interp_flag,\
                                logging=logging)
                logging.info("Created interpolated: "+split_file)
            else:
                gt.interpolate_dive(split_file, \
                                split_file.replace('.nc','_st.nc'),\
                                GLIDER_CONFIG, MODULE_DICT,\
                                interp_flag=interp_flag,\
                                logging=logging)
                logging.info("Created: "+split_file)

    except:
        db.shout("Failed to process profile", logging=logging, verbose=verbose)   
        good_flag = False

    return good_flag

#-default parameters------------------------------------------------------------
OUT_ROOT = '/home/ben/shared/Linux_desktop/data/datasets/Projects/AlterEco/'
DEFAULT_LOG_PATH = OUT_ROOT+'/Glider_data/logs/'
DEFAULT_PLT_DIR = OUT_ROOT+'/Glider_data/plots/'
DEFAULT_CFG_DIR = os.path.dirname(os.path.realpath(__file__))+'/cfg/'
DEFAULT_CFG_FILE = DEFAULT_CFG_DIR+'config_main.py'

#-arguments---------------------------------------------------------------------

PARSER = argparse.ArgumentParser()
PARSER.add_argument('-cfg', '--config_file', type=str,\
                    default=DEFAULT_CFG_FILE,\
                    help='Config file')
PARSER.add_argument('-p', '--plot_dir', type=str,\
                    default=DEFAULT_PLT_DIR,\
                    help='Plot plotting directory')
PARSER.add_argument('-v', '--verbose',\
                    action='store_true')
PARSER.add_argument('-l', '--log_path', type=str,\
                    default=DEFAULT_LOG_PATH,\
                    help='log file output path')
ARGS = PARSER.parse_args()

#-main--------------------------------------------------------------------------
if __name__ == "__main__":
    interp_flag = False
    verbose = ARGS.verbose
    re_stage = True

    # preliminary stuff
    LOGFILE = ARGS.log_path+"AlterEco_staging_"+\
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

    count = -1
    for file_name in file_names:

        print(file_name)
        count        = count + 1
        
        try:
            preproc_file = file_name[0].replace(MODULE_DICT['download_dir'], \
                                         MODULE_DICT['staged_dir'])

            if not os.path.exists(os.path.dirname(preproc_file)):
                os.makedirs(os.path.dirname(preproc_file))
                os.chmod(os.path.dirname(preproc_file), 0o777)

            if int(is_staged[count][0]) == 1 and re_stage == False:
                db.shout(file_name[0]+' not updated & already staged; skipping',\
                     logging=logging, verbose=verbose)
            else:
                if 'Melonhead' in file_name[0] or 'Orca' in file_name[0]:
                    GLIDER_CONFIG = DEFAULT_CFG_DIR+'config_EGO_Melonhead.py'
                    MODULE_DICT['gnumber'] = int(glider_number[count][0])         
                    MODULE_DICT['gtype'] = glider_type[count][0]
                    MODULE_DICT['gprefix'] = glider_prefix[count][0]

                elif 'Eltanin' in file_name[0]:
                    GLIDER_CONFIG = DEFAULT_CFG_DIR+'config_Eltanin_Xing.py'
                    MODULE_DICT['gnumber'] = int(glider_number[count][0])         
                    MODULE_DICT['gtype'] = glider_type[count][0]
                    MODULE_DICT['gprefix'] = glider_prefix[count][0]
       
                elif glider_prefix[count][0] == 'sg':
                    GLIDER_CONFIG = DEFAULT_CFG_DIR+'config_seaglider.py'
                    MODULE_DICT['gnumber'] = int(glider_number[count][0])         
                    MODULE_DICT['gtype'] = glider_type[count][0]
                    MODULE_DICT['gprefix'] = glider_prefix[count][0]
                elif glider_prefix[count][0] == 'UEA':
                    GLIDER_CONFIG = DEFAULT_CFG_DIR+'config_UEA.py'
                    MODULE_DICT['gnumber'] = int(glider_number[count][0])         
                    MODULE_DICT['gtype'] = glider_type[count][0]
                    MODULE_DICT['gprefix'] = glider_prefix[count][0]
                elif glider_prefix[count][0] == 'EGO':
                    GLIDER_CONFIG = DEFAULT_CFG_DIR+'config_EGO.py'
                    MODULE_DICT['gnumber'] = int(glider_number[count][0])         
                    MODULE_DICT['gtype'] = glider_type[count][0]
                    MODULE_DICT['gprefix'] = glider_prefix[count][0]
                else:
                    print('No good config....skipping')
                    continue

                success = process_file(master_database, file_name[0], \
                                   preproc_file, GLIDER_CONFIG, MODULE_DICT, \
                                   interp_flag=interp_flag, logging=logging, \
                                   verbose=verbose)

                if success:
                    db.shout(file_name[0]+' has been successfully staged', \
                         logging=logging, verbose=verbose)

                    #update database(s)
                    for database in all_databases:
                        today = "'"+\
                            datetime.datetime.now().strftime('%Y%m%d_%H%M')+"'"

                        conn, c = db.connectDB(database)
                        c.execute("UPDATE {tn} SET {sn} = 1 WHERE {fn} = {fname}".\
                                 format(tn=MODULE_DICT['table_name'],\
                                 sn=MODULE_DICT['stage_column'],\
                                 fn=MODULE_DICT['file_name_column'],\
                                 fname='"'+file_name[0]+'"'))

                        c.execute("UPDATE {tn} SET {sn} = {val} \
                                 WHERE {fn} = {fname}".\
                                 format(tn=MODULE_DICT['table_name'],\
                                 sn=MODULE_DICT['stage_dir_column'],\
                                 val='"'+os.path.dirname(preproc_file)+'"',\
                                 fn=MODULE_DICT['file_name_column'],\
                                 fname='"'+file_name[0]+'"'))

                        c.execute("UPDATE {tn} SET {sn} = {val} \
                                 WHERE {fn} = {fname}".\
                                 format(tn=MODULE_DICT['table_name'],\
                                 sn=MODULE_DICT['stage_column']+'_date',\
                                 val=today,\
                                 fn=MODULE_DICT['file_name_column'],\
                                 fname='"'+file_name[0]+'"'))

                        #zero the flags in case of re-processing
                        c.execute("UPDATE {tn} SET {sn1} = 0, {sn2} = 0, {sn3} = 0,"
                                  " {sn4} = 0, {sn5} = 0, {sn6} = 0"
                                  " WHERE {fn} = {fname}".\
                                  format(tn=MODULE_DICT['table_name'],\
                                  sn1=MODULE_DICT['EO_column'],\
                                  sn2=MODULE_DICT['preproc_column'],\
                                  sn3=MODULE_DICT['spectral_column'],\
                                  sn4=MODULE_DICT['corrected_column'],\
                                  sn5=MODULE_DICT['pp_column'],\
                                  sn6=MODULE_DICT['postproc_column'],\
                                  fn=MODULE_DICT['file_name_column'],\
                                  fname='"'+file_name[0]+'"'))
                        conn.commit()
                        conn.close()

                else:
                    db.shout(file_name[0]+' failed to stage', \
                             logging=logging, verbose=verbose)
        except:
            db.shout(file_name[0]+' failed to stage', \
                     logging=logging, verbose=True)
#--EOF
