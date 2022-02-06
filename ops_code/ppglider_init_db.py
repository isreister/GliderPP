#!/usr/bin/env python
'''
Purpose:    Initialises sql database to manage AIS/Sentinel processing
            stages:

Version:    v1.0 (10/2021)

Version:    v1.0 10/2021

Author:     Ben Loveday, Plymouth Marine Laboratory
            Time Smyth, Plymouth Marine Laboratory

License:    See LICENCE.txt

Database table keys
=========
Table entries:

glider_type:        glider type (seaglider or slocum)
glider_prefix:      glider prefix (e.g. sg)
glider_number:      glider number (e.g 537)
glider_name:        glider name (e.g Fin)

downloaded:         yes/no (1/0)
date_added:         date/time scene was added to database
file_downloaded:    downloaded file name

staged:             yes/no (1/0)
staged_date:        date/time scene was staged
staged_dir:         where file was linked/unzipped to

EO_acquire:         yes/no (1/0)
EO_acquire_state:   error messaging
EO_acquire_date:    date/time scene acquired EO trajectory data

preproc:            yes/no (1/0)
preproc_state:      error messaging
preproc_date:       date/time scene was preprocessed

spectral:           yes/no (1/0)
spectral_state:     error messaging
spectral_date:      date/time corrections were derived

corrections:        yes/no (1/0)
corrections_state   error messaging
corrections_date:   date/time corrections were applied

primary_prod:       yes/no (1/0)
proc_state:         error messaging
proc_date:          date/time scene PP was calculated

postproc:           yes/no (1/0)
postproc_state:     error messaging
postproc_date:      date/time scene was postprocessed
'''

import os
import shutil
import datetime
import logging
import argparse
import tools.db_tools as db

#-default parameters------------------------------------------------------------
OUT_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
DEFAULT_LOG_PATH = os.path.join(OUT_ROOT, 'logs')
DEFAULT_CFG_DIR = os.path.join(OUT_ROOT, 'configs')
DEFAULT_CFG_FILE = os.path.join(DEFAULT_CFG_DIR, 'config_main.py')

#-arguments---------------------------------------------------------------------
PARSER = argparse.ArgumentParser()
PARSER.add_argument('-cfg', '--config_file', type=str,\
                    default=DEFAULT_CFG_FILE,\
                    help='Config file')
PARSER.add_argument("-tn", "--table_name",\
                    type=str,\
                    default="PPglider_processing_stages",\
                    help="Table name")
PARSER.add_argument("-r", "--remove_old",\
                    default=False,\
                    help="switch to remove old database")
PARSER.add_argument('-l', '--log_path', type=str,\
                    default=DEFAULT_LOG_PATH,\
                    help='log file output path')
PARSER.add_argument("-c", "--column_names",\
                    type=str,\
                    default="glider_type text, \
                             glider_prefix text, \
                             glider_number text, \
                             glider_name text, \
                             downloaded text, \
                             date_added text, \
                             file_downloaded text, \
                             staged text, \
                             staged_date text, \
                             staged_dir text, \
                             EO_acquire text, \
                             EO_acquire_state text, \
                             EO_acquire_date text, \
                             preproc text, \
                             preproc_state text, \
                             preproc_date text, \
                             spectral text, \
                             spectral_state text, \
                             spectral_date text, \
                             corrections text, \
                             corrections_state text, \
                             corrections_date text, \
                             primary_prod text, \
                             primary_prod_state text, \
                             primary_prod_date text, \
                             postproc text, \
                             postproc_state text, \
                             postproc_date text", \
                             help="Column names")
PARSER.add_argument('-v', '--verbose',\
                    action='store_true')
ARGS = PARSER.parse_args()

#-main--------------------------------------------------------------------------
if __name__ == "__main__":

    # preliminary stuff
    verbose = ARGS.verbose
    LOGFILE = os.path.join(ARGS.log_path,"PPglider_initialise_"+\
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
    except OSError as error :
        print(error)
        print("Failed to set logger")

    # read processing config file
    MODULE_DICT = {}
    try:
        db.shout("Reading configuration file...", verbose=verbose)
        with open(ARGS.config_file, 'r', encoding='UTF-8') as myfile:
            for line in myfile:
                if '#' in line:
                    continue
                name, var = line.partition("=")[::2]
                MODULE_DICT[name.strip()] = str(var.replace('\n', ''))
    except OSError as error :
        print(error)
        db.shout("Failed to read configuration file", verbose=verbose,
          level='error')

    if not os.path.exists(os.path.abspath(MODULE_DICT['backup_dir'])):
        os.makedirs(os.path.abspath(MODULE_DICT['backup_dir']))

    if not os.path.exists(os.path.abspath(MODULE_DICT['database_dir'])):
        os.makedirs(os.path.abspath(MODULE_DICT['database_dir']))

    # set database names
    database_name = os.path.join(os.path.abspath(MODULE_DICT['database_dir']),
      MODULE_DICT['database_name'])

    backup_name = database_name.replace(
      os.path.abspath(MODULE_DICT['database_dir']),
      os.path.abspath(MODULE_DICT['backup_dir'])).replace('.db', '_'
      + datetime.datetime.now().strftime('%Y%m%d') + '.db.bk')

    try:
        NEW_FLAG = True
        if os.path.exists(database_name):
            if ARGS.remove_old:
                # clear old database
                db.shout("Removing old database; new one will be created",\
                         verbose=verbose)
                os.remove(database_name)
            else:
                NEW_FLAG = False
                # backup new database
                db.shout("Backing up old database to " + backup_name,
                  verbose=verbose)
                shutil.copy(database_name, backup_name)
                db.shout("Current database is " + database_name,
                  verbose=verbose)

        if NEW_FLAG:

            db.shout("Initialising database: " + database_name,verbose=verbose)

            # connect to database
            conn,c = db.connectDB(database_name)

            # Create table
            c.execute(f'''CREATE TABLE {ARGS.table_name} ({ARGS.column_names})''')

            # Save (commit) the changes
            conn.commit()

            # close database
            conn.close()

            db.shout("New database initialised",verbose=verbose)
    except OSError as error :
        print(error)
        db.shout("Database initialisation or backup failed", verbose=verbose,
          level='warning')
#--EOF
