#!/usr/bin/env python
'''
Purpose:    Initialises sql database to manage AIS/Sentinel processing
            stages:

Version:    v1.0 (10/2021)

Author:     Ben Loveday, Plymouth Marine Laboratory
            Tim Smyth, Plymouth Marine Laboratory

License:    See LICENCE.txt
'''

import os
import shutil
import datetime
import logging
import argparse
import configparser
import tools.database_tools as db

#-default parameters------------------------------------------------------------
OUT_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
DEFAULT_LOG_PATH = os.path.join(OUT_ROOT, 'logs')
DEFAULT_CFG_DIR = os.path.join(OUT_ROOT, 'configs')
DEFAULT_CFG_FILE = os.path.join(DEFAULT_CFG_DIR, 'config_main.ini')

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
    module_config = configparser.ConfigParser(allow_no_value=True)
    module_config.read(ARGS.config_file)

    # create required directories
    if not os.path.exists(os.path.abspath(module_config['DIRECTORIES']['backup_dir'])):
        os.makedirs(os.path.abspath(module_config['DIRECTORIES']['backup_dir']))
    if not os.path.exists(os.path.abspath(module_config['DIRECTORIES']['database_dir'])):
        os.makedirs(os.path.abspath(module_config['DIRECTORIES']['database_dir']))

    # set database names
    database_name = os.path.join(os.path.abspath(module_config['DIRECTORIES']['database_dir']),
      module_config['DATABASE']['database_name'])
    column_names = ','.join([f"{i} {module_config['DATABASE_columns'][i]}" 
      for i in module_config['DATABASE_columns']])

    backup_name = database_name.replace(
      os.path.abspath(module_config['DIRECTORIES']['database_dir']),
      os.path.abspath(module_config['DIRECTORIES']['backup_dir'])).replace('.db', '_'
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
            c.execute(f'''CREATE TABLE {module_config['DATABASE']['table_name']} ({column_names})''')

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
