#! /usr/bin/env python
'''
Purpose:	Initialises sql database to manage AIS/Sentinel processing 
		stages:

Version: 	v1.0 02/2018

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

Databse table keys
=========
Table entries:

glider_type:			glider type (seaglider or slocum)
glider_prefix:			glider prefix (e.g. sg)
glider_number:			glider number (e.g 537)
glider_name:			glider name (e.g Fin)

downloaded:			yes/no (1/0)
date_added:			date/time scene was added to database
file_downloaded:    		downloaded file name

staged:				yes/no (1/0)
staged_date:			date/time scene was staged
staged_dir:			where file was linked/unzipped to

---------------------------TWO DATABASES (DT & NRT)-----------------------------

EO_acquire:			yes/no (1/0)
EO_acquire_state:		error messaging
EO_acquire_date:		date/time scene acquired EO trajectory data

preproc:			yes/no (1/0)
preproc_state:			error messaging
preproc_date:			date/time scene was preprocessed (NRT/DT)

spectral:			yes/no (1/0)
spectral_state:			error messaging
spectral_date:			date/time corrections were derived (NRT/DT)

corrections:			yes/no (1/0)
corrections_state		error messaging
corrections_date:		date/time corrections were applied (NRT/DT)

primary_prod:			yes/no (1/0)
proc_state:			error messaging
proc_date:			date/time scene PP was calculated (NRT/DT)

postproc:			yes/no (1/0)
postproc_state:			error messaging
postproc_date:			date/time scene was postprocessed (NRT/DT)
'''
from __future__ import print_function
import sqlite3
import argparse, os, sys, shutil, datetime, logging

# add paths/tools
sys.path.append(os.path.dirname(os.path.realpath(__file__))+'/tools/')
import db_tools as db


#-default parameters------------------------------------------------------------
OUT_ROOT = os.path.dirname(os.path.realpath(__file__))
DEFAULT_LOG_PATH = OUT_ROOT+'/logs/'
DEFAULT_CFG_DIR = os.path.dirname(os.path.realpath(__file__))+'/cfg/'
DEFAULT_CFG_FILE = DEFAULT_CFG_DIR+'config_main.py'

#-------------------------------------------------------------------------------
#-arguments-
PARSER = argparse.ArgumentParser()
PARSER.add_argument('-cfg', '--config_file', type=str,\
                    default=DEFAULT_CFG_FILE,\
                    help='Config file')
PARSER.add_argument("-tn", "--table_name",\
                    type=str,\
                    default="AlterEco_glider_processing_stages",\
                    help="Table name")
PARSER.add_argument("-b", "--backup_dir",\
                    type=str,\
                    default="/home/ben/shared/Linux_desktop/data/datasets/Projects/AlterEco/",\
                    help="database backup directory")
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
PARSER.add_argument("-pc", "--proc_chain",\
                    type=str,\
                    default="NRT",\
                    help="processing chain type (NRT or DT)")
PARSER.add_argument('-v', '--verbose',\
                    action='store_true')

ARGS = PARSER.parse_args()

#-------------------------------------------------------------------------------
#-main----
if __name__ == "__main__":

    # preliminary stuff
    LOGFILE = ARGS.log_path+"AlterEco_initialise_"+\
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

    if os.path.exists(ARGS.backup_dir):
        pass
    else:
       os.makedirs(ARGS.backup_dir)

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

    verbose = ARGS.verbose

    if ARGS.proc_chain == 'NRT':
        database_name = MODULE_DICT['database_NRT']
    else :
        database_name = MODULE_DICT['database_DT']

    try:
        new_flag = True
        if os.path.exists(database_name):
            if ARGS.remove_old:
                # clear old database
                db.shout('Removing old database; new one will be created',\
                         verbose=verbose)
                os.remove(database_name)
            else:
                old_db = os.path.basename(database_name)
                new_flag = False
                # backup new database
                db.shout('Backing up old database to '+ARGS.backup_dir+"/"+\
                      old_db+"."+datetime.datetime.now().strftime('%Y%m%d')+\
                      ".old and exiting: "+\
                      datetime.datetime.now().strftime('%Y%m%d'),verbose=verbose)
                if os.path.exists(ARGS.backup_dir+"/"+old_db):
                    # don't overwrite old backups: 
                    # saves one per day, may get out of hand!!
                    shutil.move(ARGS.backup_dir+"/"+old_db,\
                               ARGS.backup_dir+"/"+old_db\
                               +"."+datetime.datetime.now()\
                               .strftime('%Y%m%d')+".old")
                shutil.copy(database_name,ARGS.backup_dir+"/"+\
                            old_db)

        if new_flag:

            db.shout('Initialising database: '+database_name,verbose=verbose)

            # connect to database
            conn,c = db.connectDB(database_name)

            # Create table
            c.execute('''CREATE TABLE {tn} ({cn})'''.\
                      format(tn=ARGS.table_name, cn=ARGS.column_names))

            # Save (commit) the changes
            conn.commit()

            # close database
            conn.close()

            db.shout('New database initialised',verbose=verbose)
    except:
        db.shout('Database initialisation or backup failed',verbose=verbose)
#--EOF
