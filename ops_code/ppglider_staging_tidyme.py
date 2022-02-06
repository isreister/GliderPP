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
import os
import shutil
import datetime
import logging
import argparse
import numpy as np
import fnmatch
import glob
import warnings
import sys

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
                 module_config, interp_flag=False, logging=None, verbose=False):
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
                                GLIDER_CONFIG, module_config,\
                                interp_flag=interp_flag,\
                                logging=logging)
                logging.info("Created interpolated: "+split_file)
            else:
                gt.interpolate_dive(split_file, \
                                split_file.replace('.nc','_st.nc'),\
                                GLIDER_CONFIG, module_config,\
                                interp_flag=interp_flag,\
                                logging=logging)
                logging.info("Created: "+split_file)

    except:
        db.shout("Failed to process profile", logging=logging, verbose=verbose)   
        good_flag = False

    return good_flag

#-default parameters------------------------------------------------------------
OUT_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
DEFAULT_LOG_PATH = os.path.join(OUT_ROOT, 'logs')
DEFAULT_PLT_PATH = os.path.join(OUT_ROOT, 'plots')
DEFAULT_CFG_DIR = os.path.join(OUT_ROOT, 'configs')
DEFAULT_CFG_FILE = os.path.join(DEFAULT_CFG_DIR, 'config_main.py')

#-arguments---------------------------------------------------------------------

PARSER = argparse.ArgumentParser()
PARSER.add_argument('-cfg', '--config_file', type=str,\
                    default=DEFAULT_CFG_FILE,\
                    help='Config file')
PARSER.add_argument('-p', '--plot_dir', type=str,\
                    default=DEFAULT_PLT_PATH,\
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
    LOGFILE = os.path.join(ARGS.log_path,"PPglider_stage_"+\
              datetime.datetime.now().strftime('%Y%m%d_%H%M')+".log")

    # make required log directory if it does not exist
    if not os.path.exists(os.path.abspath(ARGS.log_path)):
        os.makedirs(ARGS.log_path)

    # set file logger
    try:
        if os.path.exists(LOGFILE):
            os.remove(LOGFILE)
        print("logging to: "+LOGFILE)
        logging.basicConfig(filename=LOGFILE, level=logging.DEBUG)
    except:
        print("Failed to set logger")
        sys.exit()

    # read config file
    module_config = {}
    try:
        db.shout("Reading configuration file...", verbose=verbose)
        with open(ARGS.config_file, 'r', encoding='UTF-8') as myfile:
            for line in myfile:
                if '#' in line:
                    continue
                name, var = line.partition("=")[::2]
                module_config[name.strip()] = str(var.replace('\n', ''))
    except OSError as error :
        print(error)
        db.shout("Failed to read configuration file", verbose=verbose,
          level='error')

    # set database names
    database_name = os.path.join(os.path.abspath(module_config['database_dir']),
      module_config['database_name'])

    # get database statuses
    glider_types, glider_prefixes, glider_numbers, glider_names, file_names, \
        is_staged, stage_dir, is_EO, is_preproc, is_spectral, is_corrected, \
        is_pp, is_postproc = db.get_status(database_name,\
        module_config['table_name'],\
        module_config['glider_type_column'],\
        module_config['glider_prefix_column'],\
        module_config['glider_number_column'],\
        module_config['glider_name_column'],\
        module_config['file_name_column'],\
        module_config['stage_column'],\
        module_config['stage_dir_column'],\
        module_config['EO_column'],\
        module_config['preproc_column'],\
        module_config['spectral_column'],\
        module_config['corrected_column'],\
        module_config['pp_column'],\
        module_config['postproc_column'],\
        logging=logging, verbose=verbose)

    for file_name, glider_prefix, glider_number, glider_name, glider_is_staged in \
      zip(file_names, glider_prefixes, glider_numbers, glider_names, is_staged):
        
        if 1==1:
            preproc_file = file_name[0].replace(module_config['download_dir'], \
                                         module_config['staged_dir'])

            if not os.path.exists(os.path.dirname(preproc_file)):
                os.makedirs(os.path.dirname(preproc_file))
                os.chmod(os.path.dirname(preproc_file), 0o777)

            if int(glider_is_staged[0]) == 1 and re_stage == False:
                db.shout(file_name[0]+' not updated & already staged; skipping',\
                     logging=logging, verbose=verbose)
            else:
                GLIDER_CONFIG = os.path.join(DEFAULT_CFG_DIR,f"config_{glider_prefix[0]}_{glider_number[0]}_{glider_name[0]}.py")
                if not os.path.exists(os.path.abspath(GLIDER_CONFIG)):
                    print(f"Config {GLIDER_CONFIG} does not exist; please create it!!")
                    continue

                success = process_file(database_name, file_name[0], \
                                   preproc_file, GLIDER_CONFIG, module_config, \
                                   interp_flag=interp_flag, logging=logging, \
                                   verbose=verbose)

                if success:
                    db.shout(file_name[0]+' has been successfully staged', \
                         logging=logging, verbose=verbose)

                    #update database(s)
                    today = "'"+\
                        datetime.datetime.now().strftime('%Y%m%d_%H%M')+"'"

                    conn, c = db.connectDB(database_name)
                    c.execute("UPDATE {tn} SET {sn} = 1 WHERE {fn} = {fname}".\
                             format(tn=module_config['table_name'],\
                             sn=module_config['stage_column'],\
                             fn=module_config['file_name_column'],\
                             fname='"'+file_name[0]+'"'))

                    c.execute("UPDATE {tn} SET {sn} = {val} \
                             WHERE {fn} = {fname}".\
                             format(tn=module_config['table_name'],\
                             sn=module_config['stage_dir_column'],\
                             val='"'+os.path.dirname(preproc_file)+'"',\
                             fn=module_config['file_name_column'],\
                             fname='"'+file_name[0]+'"'))

                    c.execute("UPDATE {tn} SET {sn} = {val} \
                             WHERE {fn} = {fname}".\
                             format(tn=module_config['table_name'],\
                             sn=module_config['stage_column']+'_date',\
                             val=today,\
                             fn=module_config['file_name_column'],\
                             fname='"'+file_name[0]+'"'))

                    #zero the flags in case of re-processing
                    c.execute("UPDATE {tn} SET {sn1} = 0, {sn2} = 0, {sn3} = 0,"
                              " {sn4} = 0, {sn5} = 0, {sn6} = 0"
                              " WHERE {fn} = {fname}".\
                              format(tn=module_config['table_name'],\
                              sn1=module_config['EO_column'],\
                              sn2=module_config['preproc_column'],\
                              sn3=module_config['spectral_column'],\
                              sn4=module_config['corrected_column'],\
                              sn5=module_config['pp_column'],\
                              sn6=module_config['postproc_column'],\
                              fn=module_config['file_name_column'],\
                              fname='"'+file_name[0]+'"'))
                    conn.commit()
                    conn.close()

                else:
                    db.shout(file_name[0]+' failed to stage', \
                             logging=logging, verbose=verbose)
        else:
            db.shout(file_name[0]+' failed to stage', \
                     logging=logging, verbose=True)
#--EOF
