#!/usr/bin/env python
'''
Purpose:	Autodownloads MARS/NOC/BODC data from sftp source

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
'''
#-imports-----------------------------------------------------------------------
from __future__ import print_function
import argparse, os, sys, shutil, datetime, logging
import paramiko
from stat import S_ISDIR
import fnmatch

# add paths/tools
sys.path.append(os.path.dirname(os.path.realpath(__file__))+'/tools/')
import db_tools as db

#-functions---------------------------------------------------------------------
def check_files(MODULE_CONFIG, logging=None, verbose=False, port=22):
    '''
     ftplib does not support sftp, so using paramiko. Checks for files matching
     supplied pattern on remote sftp server; and downloads if they differ from
     what we have.
    '''
    matches = MODULE_CONFIG['fmatch'].split(',')
    excludes = MODULE_CONFIG['fexclude'].split(',')

    db.shout("Connecting to: "+MODULE_CONFIG['host'], logging=logging, verbose=verbose)

    transport = paramiko.Transport((MODULE_CONFIG['host'], port))
    transport.connect(username=MODULE_CONFIG['username'],\
                      password=MODULE_CONFIG['password'])
    sftp = paramiko.SFTPClient.from_transport(transport)

    download_dir(MODULE_CONFIG, MODULE_CONFIG['product_dir'],\
                 MODULE_CONFIG['download_dir'], sftp, matches, excludes, \
                 logging=logging, verbose=verbose)

    sftp.close()
    transport.close()
    db.shout("Transfers completed", logging=logging, verbose=verbose)

def download_dir(MODULE_CONFIG, remote_dir, local_dir, sftp, matches,\
                 excludes, logging=logging, verbose=False):
    '''
     loops through directories and downloads files on single connection.
    '''
    
    database_NRT = MODULE_CONFIG['database_NRT']
    database_DT = MODULE_CONFIG['database_DT']

    local_dir = remote_dir.replace(MODULE_CONFIG['product_dir'],\
                                   MODULE_CONFIG['download_dir'])

    if not os.path.exists(local_dir):
        os.makedirs(local_dir)

    dir_items = sftp.listdir_attr(remote_dir)
    for item in dir_items:
        remote_path = os.path.join(remote_dir, item.filename)
        local_path = os.path.join(local_dir, item.filename)
        if S_ISDIR(item.st_mode):
            download_dir(MODULE_CONFIG, remote_path, local_path, sftp, matches,\
                         excludes, logging=logging, verbose=verbose)
        else:
            for match in matches:
                if str(match) in remote_path:
                    for exclude in excludes:
                        if str(exclude) in remote_path:
                            continue

                    if not os.path.exists(local_path):
                        # get file if no corresponding local target
                        # update DB
                        db.shout("Transferring: "+\
                                 os.path.basename(remote_path),\
                                 logging=logging, verbose=verbose)

                        sftp.get(remote_path, local_path)
                        timestamp  = os.stat(local_path).st_mtime
                        db.add_new_file_row(MODULE_CONFIG['database_NRT'],\
                                            "file_downloaded",\
                                            MODULE_CONFIG,\
                                            local_path,\
                                            timestamp,\
                                            logging=logging,\
                                            verbose=verbose)
                        db.add_new_file_row(MODULE_CONFIG['database_DT'],\
                                            "file_downloaded",\
                                            MODULE_CONFIG,\
                                            local_path,\
                                            timestamp,\
                                            logging=logging,\
                                            verbose=verbose)
                    else:
                        # update DB if local path is correct size
                        # but target is missing from DB
                        local_file_info = os.stat(local_path)
                        if local_file_info.st_size == item.st_size:
                            timestamp  = os.stat(local_path).st_mtime
                            db.shout("Present, correct size, checking DB(s): "\
                                     +os.path.basename(local_path),\
                                     logging=logging, verbose=verbose)

                            db.add_new_file_row(MODULE_CONFIG['database_NRT'],\
                                                "file_downloaded",\
                                                MODULE_CONFIG,\
                                                local_path,\
                                                timestamp,\
                                                logging=logging,\
                                                verbose=verbose)

                            db.add_new_file_row(MODULE_CONFIG['database_DT'],\
                                                "file_downloaded",\
                                                MODULE_CONFIG,\
                                                local_path,\
                                                timestamp,\
                                                logging=logging,\
                                                verbose=verbose)
                        else:
                            # get file if local target is wrong size
                            # update DB
                            db.shout("Incorrect size, transferring: "\
                                     +os.path.basename(remote_path),\
                                     logging=logging, verbose=verbose)                            
                            sftp.get(remote_path, local_path)
                            timestamp  = os.stat(local_path).st_mtime

                            db.add_new_file_row(MODULE_CONFIG['database_NRT'],\
                                                "file_downloaded",\
                                                MODULE_CONFIG,\
                                                local_path,\
                                                timestamp,\
                                                logging=logging,\
                                                verbose=verbose)

                            db.add_new_file_row(MODULE_CONFIG['database_DT'],\
                                                "file_downloaded",\
                                                MODULE_CONFIG,\
                                                local_path,\
                                                timestamp,\
                                                logging=logging,\
                                                verbose=verbose)

#-default parameters------------------------------------------------------------
OUT_ROOT = '/Users/benloveday/Desktop/'
DEFAULT_LOG_PATH = OUT_ROOT+'/Glider_data/logs/'
DEFAULT_PLT_DIR = OUT_ROOT+'/Glider_data/plots/'
DEFAULT_CFG_DIR = os.path.dirname(os.path.realpath(__file__))+'/cfg/'
DEFAULT_CFG_FILE = DEFAULT_CFG_DIR+'config_main.py'

#-ARGS--------------------------------------------------------------------------

PARSER = argparse.ArgumentParser()
PARSER.add_argument('-cfg', '--config_file', type=str,\
                    default=DEFAULT_CFG_FILE,\
                    help='Config file')
PARSER.add_argument('-v', '--verbose',\
                    action='store_true')
PARSER.add_argument('-l', '--log_path', type=str,\
                    default=DEFAULT_LOG_PATH,\
                    help='log file output path')
ARGS = PARSER.parse_args()

#-main--------------------------------------------------------------------------
if __name__ == "__main__":
    # preliminary stuff
    LOGFILE = ARGS.log_path+"AlterEco_autodownload_"+\
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

    # read config file
    MODULE_CONFIG = {}
    try:
        logging.info("Reading configuration file...")
        with open(ARGS.config_file) as myfile:
            for line in myfile:
                if '#' in line:
                    continue
                else:
                    name, var = line.partition("=")[::2]
                    MODULE_CONFIG[name.strip()] = str(var.replace('\n', ''))
    except:
        logging.warning("Failed to read configuration file")
        sys.exit()

    #try:
    #    check_files(MODULE_CONFIG, logging=logging, verbose=ARGS.verbose)
    #except:
    #    logging.warning("Failed to contact server!!")

    #check for previously downloaded files that are missing from the database 
    #(e.g. in case of a total rebuild)
    existing_files=[]
    for root, _, filenames in os.walk(MODULE_CONFIG['download_dir']):
        for filename in fnmatch.filter(filenames,'*.nc'):
            existing_files.append(os.path.join(root, filename))
            if ARGS.verbose:
                print('Found: '+filename)
            logging.info('Found: '+os.path.join(root, filename)) 

    logging.info("Updating database with pre-existing files if required...")

    for existing_file in existing_files:
        print(existing_file)
        base_fname = os.path.basename(existing_file)
        timestamp  = os.stat(existing_file).st_mtime
        # update database
        if '_R.nc' in existing_file and 'EGO' not in existing_file:
            print('Skipping '+existing_file+' as spurious or duplicate')
            continue
        #if 'Melonhead' not in existing_file:
        #    continue 
        db.add_new_file_row(MODULE_CONFIG['database_NRT'],\
                            "file_downloaded",\
                            MODULE_CONFIG,\
                            existing_file,\
                            timestamp,\
                            logging=logging,\
                            verbose=ARGS.verbose)

        db.add_new_file_row(MODULE_CONFIG['database_DT'],\
                            "file_downloaded",\
                            MODULE_CONFIG,\
                            existing_file,\
                            timestamp,\
                            logging=logging,\
                            verbose=ARGS.verbose)

#--EOF
