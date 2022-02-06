#!/usr/bin/env python
'''
Purpose: 
Database creation/access/update tools

History:

Created by blo: 10/2016
'''
import sqlite3
import datetime
import os, sys
from netCDF4 import Dataset

#-------------------------------------------------------------------------------
#-functions-
def get_status(database, table_name, keys, \
               logging=False, verbose=False):

    if 1==1:
        db_dict = {}
        # read database
        shout("Reading database", logging=logging, verbose=verbose)

        conn, c = connectDB(database)

        # get filenames to establish sort index
        c.execute("SELECT {cn} FROM {tn}".\
                  format(tn=table_name,cn="file_downloaded"))
        items = c.fetchall()
        items = [item[0] for item in items]
        sort_index = sorted(range(len(items)), key=lambda k: items[k])

        for key in keys:
            print(f"Reading: {key}")

            # check filename(s)
            c.execute("SELECT {cn} FROM {tn}".\
                      format(tn=table_name,cn=key))
            items = c.fetchall()
            items = [item[0] for item in items]
            db_dict[key] = [items[i] for i in sort_index]

        shout("Read database", logging=logging, verbose=verbose)
        # close database, re-open as required later on to prevent locking
        conn.close()

        return len(sort_index), db_dict

    else:
        shout("Failed to read database", logging=logging, verbose=verbose)
        sys.exit()

def shout(message, logging=None, verbose=False, level='info'):
    if logging:
        if level == 'info':
           logging.info(message)
        elif level == 'error':
           logging.error(message)
        elif level == 'warning':
           logging.warning(message)
        else:
           logging.debug(message)
        if verbose:
            print(message)
    else:
        if verbose:
            print(message)

def connectDB(DB_file):
    '''
    Make connection to an SQLite database file
    '''
    conn = sqlite3.connect(DB_file)
    c = conn.cursor()
    return conn, c

def get_SQL_data(c,table_name, column_name, column_id,match):
    '''
    Read data from SQLite DB
    '''
    c.execute('SELECT ({coi}) FROM {tn} WHERE {cn}="{sn}"'.\
              format(coi=column_name, tn=table_name, cn=column_id, sn=match))
    VAR=c.fetchall()
    return VAR

def add_new_file_row(DB, column_name, CFG, file_name, timestamp,\
                     logging=None, verbose=False):
    '''
    Adds new row to database, or updates statuses as required
    '''
    # connect
    conn,c = connectDB(DB)  

    # get table name
    c.execute("SELECT name FROM sqlite_master WHERE type='table';")
    table_name=str(c.fetchall()[0][0])

    # get filenames
    c.execute("SELECT {cn} FROM {tn}".\
              format(tn=table_name,cn=column_name))
    all_rows = c.fetchall()

    # look for filename
    found_file = 0
    for row in all_rows:
       if str(row[0]) == file_name:
          found_file = 1

    if not found_file:
        # grab some keys from file
        nc_fid = Dataset(file_name)
        glider_prefix = ''
        if 'naming_authority' in nc_fid.ncattrs() and 'EGO' in nc_fid.getncattr('naming_authority'):
            # This "should" be standardised
            glider_prefix = nc_fid.getncattr('naming_authority').lower()
            glider_platform = ''.join([x.decode() for x in nc_fid.variables["PLATFORM_TYPE"][:] if x != "masked"]).lower()
            glider_name = str(nc_fid.getncattr('id')).split('_')[0].lower() # quite unreliable
            glider_number = str(nc_fid.getncattr('id')).split('_')[1] # quite unreliable
        else:
            # This is almost certainly not standardised
            glider_prefix = 'glider'
            if 'source' in nc_fid.ncattrs():
                glider_platform = nc_fid.getncattr('source').split(' ')[0].lower()
                glider_name = nc_fid.getncattr('source').split(' ')[1].lower()
                glider_number = nc_fid.getncattr('source').split(' ')[1].lower() # this is often not defined in the metadata!
            else:
                print("WARNING: CANNOT INTERPRET THIS GLIDER'S METADATA")
                glider_platform = "unknown"
                glider_name = "unknown"
                glider_number = "unknown"
        nc_fid.close()

        print('Adding File name: ' + file_name)
        print('Glider prefix: ' + glider_prefix)
        print('Glider platform: ' + glider_platform)
        print('Glider name: ' + glider_name)
        print('Glider number: ' + glider_number)

        cDOWN  = '1'
        cDATE  = "'"+datetime.datetime.fromtimestamp(timestamp).\
                 strftime('%Y%m%d_%H%M')+"'"
        cSTAGE = '0'
        cEO = '0'
        cPREPROC = '0'
        cSPECTRAL = '0'
        cCORRECTIONS = '0'
        cPRIMARY = '0'
        cPOSTPROC = '0'

        shout("Adding new row to "+os.path.basename(DB),\
              logging=logging,verbose=verbose)

        c.execute("INSERT INTO {tn} VALUES ({ctype},{cprefix},{cnum},{cnam},{cdown},"
                 "{cdowntime},{cdownfile},{cstage},?,?,?,{ceo},?,?,?,?,{cpreproc},?,"
                 "?,?,{cspectral},?,?,?,{ccorrection},?,?,?,{cprimary},?,?,?,"
                 "{cpostproc},?,?,?)".
                 format(tn=table_name, 
                        ctype="'"+glider_platform+"'",
                        cprefix="'"+glider_prefix+"'",
                        cnum="'"+glider_number+"'",
                        cnam="'"+glider_name+"'",
                        cdown="'"+cDOWN+"'",
                        cdowntime=cDATE,
                        cdownfile="'"+file_name+"'",
                        cstage=cSTAGE,
                        ceo=cEO,
                        cpreproc=cPREPROC,
                        cspectral=cSPECTRAL,
                        ccorrection=cCORRECTIONS,
                        cprimary=cPRIMARY,
                        cpostproc=cPOSTPROC),
                        (None,None,None,None,None,None,None,None,
                         None,None,None,None,None,None,None,None,
                         None, None, None, None, None, None))

    # commit changes
    conn.commit()

    # close database
    conn.close()

def rezero(database, table_name, file_column, file_name, update_column, newval):

   # RE-ZERO
   conn, c = connectDB(database)
   c.execute("UPDATE {tn} SET {uc} = {nv} WHERE {fn} = {fname}".\
             format(tn=table_name, uc=update_column, nv = newval, \
             fn=file_column, fname='"'+file_name[0]+'"'))
   conn.commit()
   conn.close()

#--EOF
