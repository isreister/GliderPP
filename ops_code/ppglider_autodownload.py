#!/usr/bin/env python
'''
Purpose:	Autodownloads MARS/NOC/BODC data from sftp source

Version:    v1.0 (10/2021)

Version:    v1.0 10/2021

Author:     Ben Loveday, Plymouth Marine Laboratory
            Time Smyth, Plymouth Marine Laboratory

License:    See LICENCE.txt
'''
#-imports-----------------------------------------------------------------------
import os
import datetime
import logging
import argparse
import fnmatch
from stat import S_ISDIR
import paramiko
import tools.database_tools as db
import configparser

#-functions---------------------------------------------------------------------
def check_files(config):
    '''
     Using paramiko as it supports SFTP. Checks for files matching supplied
     pattern on remote sftp server; and downloads if they differ from what we
     have locally.
    '''
    matches = config['DOWNLOADING']['fmatch'].split(',')
    excludes = config['DOWNLOADING']['fexclude'].split(',')

    db.shout("Connecting to: " + config['DOWNLOADING']['ftp_host'], logging=logging,
      verbose=verbose)

    transport = paramiko.Transport((config['DOWNLOADING']['ftp_host'],
      int(config['DOWNLOADING']['ftp_port'])))
    transport.connect(username=config['DOWNLOADING']['ftp_user'],\
                      password=config['DOWNLOADING']['ftp_pwrd'])
    sftp = paramiko.SFTPClient.from_transport(transport)

    mirror_dir(config, os.path.abspath(config['DOWNLOADING']['ftp_path']),\
                 os.path.abspath(config['DIRECTORIES']['download_dir']), sftp, 
                 matches, excludes)

    sftp.close()
    transport.close()

    db.shout("Transfers completed", logging=logging, verbose=verbose)

def mirror_dir(config, remote_dir, local_dir, sftp, matches,\
                 excludes):
    '''
     loops through directories and downloads files on single connection.
    '''

    local_dir = os.path.abspath(remote_dir.replace(config['DOWNLOADING']['ftp_path'],\
                                   config['DIRECTORIES']['download_dir']))
    
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)

    dir_items = sftp.listdir_attr(remote_dir)

    for item in dir_items:
        remote_path = os.path.join(remote_dir, item.filename)
        local_path = os.path.join(local_dir, item.filename)
        if S_ISDIR(item.st_mode):
            mirror_dir(config, remote_path, local_path, sftp, matches,\
                         excludes)
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
                        db.add_new_file_row(database_name,\
                                            "file_downloaded",\
                                            config,\
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

                            db.add_new_file_row(database_name,\
                                                "file_downloaded",\
                                                config,\
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

                            db.add_new_file_row(database_name,\
                                                "file_downloaded",\
                                                config,\
                                                local_path,\
                                                timestamp,\
                                                logging=logging,\
                                                verbose=verbose)

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
PARSER.add_argument('-v', '--verbose',\
                    action='store_true')
PARSER.add_argument('-l', '--log_path', type=str,\
                    default=DEFAULT_LOG_PATH,\
                    help='log file output path')
ARGS = PARSER.parse_args()

#-main--------------------------------------------------------------------------
if __name__ == "__main__":

    # preliminary stuff
    verbose = ARGS.verbose
    LOGFILE = os.path.join(ARGS.log_path,"PPglider_autodownload_"+\
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

    # make required data directory if it does not exist
    if not os.path.exists(os.path.abspath(module_config['DIRECTORIES']['download_dir'])):
        os.makedirs(os.path.abspath(module_config['DIRECTORIES']['download_dir']))

    # set database names
    database_name = os.path.join(os.path.abspath(module_config['DIRECTORIES']['database_dir']),
      module_config['DATABASE']['database_name'])

    # Get new files
    try:
        check_files(module_config)
    except ConnectionError as error:
        print(error)
        db.shout("Failed to contact server!!", verbose=verbose,
          level='warning')

    # Check for previously downloaded files that are missing from the database
    existing_files = []
    for root, _, filenames in os.walk(os.path.abspath(module_config['DIRECTORIES']['download_dir'])):
        for filename in fnmatch.filter(filenames,'*.nc'):
            existing_files.append(os.path.join(root, filename))
            if ARGS.verbose:
                print('Found: '+filename)
            logging.info('Found: %s', os.path.join(root, filename))

    db.shout("Updating database with pre-existing files if required...")

    for existing_file in existing_files:
        base_fname = os.path.basename(existing_file)
        tstamp  = os.stat(existing_file).st_mtime

        db.add_new_file_row(database_name,\
                            "file_downloaded",\
                            module_config,\
                            existing_file,\
                            tstamp,\
                            logging=logging,\
                            verbose=verbose)

#--EOF
