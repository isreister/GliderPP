#!/bin/bash
'''
# clean up first
rm -r backups/ databases/ logs/ data/ staged/ EO_data/

# instantiate database
./ops_code/ppglider_init_db.py -v

# autodownload data
./ops_code/ppglider_autodownload.py -v

# stage the data
./ops_code/ppglider_staging.py -v
'''
# Get the supporting EO data cube
./ops_code/ppglider_acquire_eo.py -v