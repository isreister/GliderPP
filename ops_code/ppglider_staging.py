#!/usr/bin/env python
'''
Purpose:	Stages MARS/NOC/BODC data from download directory to
            preprocessed directory ready for ingestion into the processing chain
            Bins allowed variables if requested.

Version:    v1.0 (10/2021)

Author:		Ben Loveday, Plymouth Marine Laboratory
            Tim Smyth, Plymouth Marine Laboratory

License:    See LICENCE.txt
'''
#-imports-----------------------------------------------------------------------
import os
import datetime
import logging
import argparse
import warnings
import sys
import configparser

# add paths/tools
import tools.database_tools as db
import tools.glider_tools as gt

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

    return good_flag, split_files

#-default parameters------------------------------------------------------------
OUT_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
DEFAULT_LOG_PATH = os.path.join(OUT_ROOT, 'logs')
DEFAULT_PLT_PATH = os.path.join(OUT_ROOT, 'plots')
DEFAULT_CFG_DIR = os.path.join(OUT_ROOT, 'configs')
DEFAULT_CFG_FILE = os.path.join(DEFAULT_CFG_DIR, 'config_main.ini')

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

    # read processing config file
    module_config = configparser.ConfigParser(allow_no_value=True)
    module_config.read(ARGS.config_file)

    # set database names
    database_name = os.path.join(os.path.abspath(module_config['DIRECTORIES']['database_dir']),
      module_config['DATABASE']['database_name'])

    all_keys = [item for item in module_config['DATABASE_columns'].keys()]

    # get database statuses
    nitems, db_dict = db.get_status(database_name,
        module_config['DATABASE']['table_name'],all_keys,
        logging=logging, verbose=verbose)

    for item in range(nitems):

        try:
            preproc_file = db_dict['file_downloaded'][item].replace(
                            os.path.abspath(module_config['DIRECTORIES']['download_dir']), \
                            os.path.abspath(module_config['DIRECTORIES']['staged_dir']))

            if not os.path.exists(os.path.dirname(preproc_file)):
                os.makedirs(os.path.dirname(preproc_file))
                os.chmod(os.path.dirname(preproc_file), 0o777)

            if int(db_dict['staged'][item]) == 1 and re_stage == False:
                db.shout(file_name+' not updated & already staged; skipping',\
                     logging=logging, verbose=verbose)
            else:
                GLIDER_CONFIG = os.path.join(DEFAULT_CFG_DIR,
                    f"config_{db_dict['glider_prefix'][item]}_{db_dict['glider_number'][item]}_{db_dict['glider_name'][item]}.ini")

                if not os.path.exists(os.path.abspath(GLIDER_CONFIG)):
                    print(f"Config {GLIDER_CONFIG} does not exist; please create it!!")
                    continue

                db.shout(f"Using config: {GLIDER_CONFIG} on {db_dict['file_downloaded'][item]}",
                     logging=logging, verbose=verbose)

                success, split_files = process_file(database_name, db_dict['file_downloaded'][item], \
                                   preproc_file, GLIDER_CONFIG, module_config, \
                                   interp_flag=interp_flag, logging=logging, \
                                   verbose=verbose)

                # convetr list to string
                split_files = ','.join(split_files)

                if success:
                    db.shout(f"{db_dict['file_downloaded'][item]} has been successfully staged", \
                         logging=logging, verbose=verbose)

                    #update database(s)
                    today = "'"+\
                        datetime.datetime.now().strftime('%Y%m%d_%H%M')+"'"

                    conn, c = db.connectDB(database_name)
                    c.execute("UPDATE {tn} SET {sn} = 1 WHERE {fn} = {fname}".\
                              format(tn=module_config['DATABASE']['table_name'],\
                              sn='staged',\
                              fn='file_downloaded',\
                              fname='"'+db_dict['file_downloaded'][item]+'"'))

                    c.execute("UPDATE {tn} SET {sn} = {val} \
                              WHERE {fn} = {fname}".\
                              format(tn=module_config['DATABASE']['table_name'],\
                              sn='staged_dir',\
                              val='"'+os.path.dirname(preproc_file)+'"',\
                              fn='file_downloaded',\
                              fname='"'+db_dict['file_downloaded'][item]+'"'))

                    c.execute("UPDATE {tn} SET {sn} = {val} \
                              WHERE {fn} = {fname}".\
                              format(tn=module_config['DATABASE']['table_name'],\
                              sn='staged_date',\
                              val=today,\
                              fn='file_downloaded',\
                              fname='"'+db_dict['file_downloaded'][item]+'"'))

                    c.execute("UPDATE {tn} SET {sn} = {val} \
                              WHERE {fn} = {fname}".\
                              format(tn=module_config['DATABASE']['table_name'],\
                              sn='staged_files',\
                              val=f'"{split_files}"',\
                              fn='file_downloaded',\
                              fname='"'+db_dict['file_downloaded'][item]+'"'))

                    #zero the flags in case of re-processing
                    c.execute("UPDATE {tn} SET {sn1} = 0, {sn2} = 0, {sn3} = 0,"
                              " {sn4} = 0, {sn5} = 0, {sn6} = 0"
                              " WHERE {fn} = {fname}".\
                              format(tn=module_config['DATABASE']['table_name'],\
                              sn1='EO_acquire',\
                              sn2='preproc',\
                              sn3='spectral',\
                              sn4='corrected',\
                              sn5='primary_prod',\
                              sn6='postproc',\
                              fn='file_downloaded',\
                              fname='"'+db_dict['file_downloaded'][item]+'"'))
                    conn.commit()
                    conn.close()

                else:
                    db.shout(f"{db_dict['file_downloaded'][item]} failed to stage", \
                             logging=logging, verbose=verbose)
        except:
            db.shout(f"{db_dict['file_downloaded'][item]} failed to stage", \
                     logging=logging, verbose=True)
#--EOF
