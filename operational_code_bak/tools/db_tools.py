#!/usr/bin/env python
'''
Purpose: 
Database creation/access/update tools

History:

Created by blo: 10/2016
'''
from __future__ import print_function
import sqlite3
import datetime
import logging
import os, sys, shutil

#-------------------------------------------------------------------------------
#-functions-
def get_status(database, table_name, glider_type_column, glider_prefix_column, \
               glider_number_column, glider_name_column, file_downloaded, \
               stage_column, stage_dir, EO_column, preproc_column, \
               spectral_column, corrected_column, pp_column, postproc_column, \
               logging=False, verbose=False):
    try:
        # read InSure database
        shout("Reading database", logging=logging, verbose=verbose)

        conn, c = connectDB(database)

        # check filename(s)
        c.execute("SELECT {cn} FROM {tn}".\
                  format(tn=table_name,cn=file_downloaded))
        file_names = c.fetchall()

        # check filename(s)
        c.execute("SELECT {cn} FROM {tn}".\
                  format(tn=table_name,cn=glider_type_column))
        glider_type = c.fetchall()

        # check filename(s)
        c.execute("SELECT {cn} FROM {tn}".\
                  format(tn=table_name,cn=glider_prefix_column))
        glider_prefix = c.fetchall()

        # check filename(s)
        c.execute("SELECT {cn} FROM {tn}".\
                  format(tn=table_name,cn=glider_number_column))
        glider_number = c.fetchall()

        # check filename(s)
        c.execute("SELECT {cn} FROM {tn}".\
                  format(tn=table_name,cn=glider_name_column))
        glider_name = c.fetchall()

        # check if staged
        c.execute("SELECT {cn} FROM {tn}".\
                  format(tn=table_name,cn=stage_column))
        is_staged  = c.fetchall()

        # check stage directory
        c.execute("SELECT {cn} FROM {tn}".\
                  format(tn=table_name,cn=stage_column+'_dir'))
        stage_dir  = c.fetchall()

        # check if we have EO trajectory data
        c.execute("SELECT {cn} FROM {tn}".\
                  format(tn=table_name,cn=EO_column))
        is_EO  = c.fetchall()

        # check if we have preprocessed
        c.execute("SELECT {cn} FROM {tn}".\
                  format(tn=table_name,cn=preproc_column))
        is_preproc  = c.fetchall()

        # check if we have done spectral deconstruction
        c.execute("SELECT {cn} FROM {tn}".\
                  format(tn=table_name,cn=spectral_column))
        is_spectral  = c.fetchall()

        # check if we have corrected
        c.execute("SELECT {cn} FROM {tn}".\
                  format(tn=table_name,cn=corrected_column))
        is_corrected  = c.fetchall()

        # check if we have run PP
        c.execute("SELECT {cn} FROM {tn}".\
                  format(tn=table_name,cn=pp_column))
        is_pp  = c.fetchall()

        # check if we have post-processed
        c.execute("SELECT {cn} FROM {tn}".\
                  format(tn=table_name,cn=postproc_column))
        is_postproc  = c.fetchall()

        shout("Read database", logging=logging, verbose=verbose)
        # close database, re-open as required later on to prevent locking
        conn.close()

        return glider_type, glider_prefix, glider_number, glider_name, \
               file_names, is_staged, stage_dir, is_EO, is_preproc, \
               is_spectral, is_corrected, is_pp, is_postproc

    except:
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

def get_SQL_data(c,table_name,column_name,column_id,match):
    '''
    Read data from SQLite DB
    '''
    c.execute('SELECT ({coi}) FROM {tn} WHERE {cn}="{sn}"'.\
              format(coi=column_name, tn=table_name, cn=column_id, sn=match))
    VAR=c.fetchall()
    return VAR

def add_new_file_row(DB,column_name,CFG,file_name,timestamp,\
                     logging=None,verbose=False):
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

    # grab some keys from filename
    glider_sub_dir = os.path.dirname(file_name).replace(CFG['download_dir'],'')
    name_split = glider_sub_dir.split('/')
    if '_R' in file_name:
       glider_prefix = 'EGO'
       glider_platform = 'either'
       glider_number = os.path.basename(file_name).split('_')[-2]
       glider_name = os.path.basename(file_name).split('_')[-3]
    elif 'UEA' in file_name:
       glider_prefix = 'UEA'
       glider_platform = 'seaglider'
       glider_name = name_split[1].split('_')[0]
       glider_number = os.path.basename(file_name).split('_')[1].replace('sg','')
    else:
       glider_prefix = 'sg'
       glider_platform = 'seaglider'
       glider_name = name_split[1].split('_')[0]
       glider_number = os.path.basename(file_name)[1:4]
    print('File name: '+file_name)
    print('Glider prefix: '+glider_prefix)

    #print(file_name+' : '+glider_prefix+' : '+glider_platform+' : '+glider_name+' : '+glider_number)

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

    if not found_file:
        shout("Adding new row to "+os.path.basename(DB),\
              logging=logging,verbose=verbose)

        c.execute("INSERT INTO {tn} VALUES ({ctype},{cprefix},{cnum},{cnam},{cdown},"
                 "{cdowntime},{cdownfile},{cstage},?,?,{ceo},?,?,{cpreproc},?,"
                 "?,{cspectral},?,?,{ccorrection},?,?,{cprimary},?,?,"
                 "{cpostproc},?,?)".\
                 format(tn=table_name, \
                        ctype="'"+glider_platform+"'",\
                        cprefix="'"+glider_prefix+"'",\
                        cnum="'"+glider_number+"'",\
                        cnam="'"+glider_name+"'",\
                        cdown="'"+cDOWN+"'",\
                        cdowntime=cDATE,\
                        cdownfile="'"+file_name+"'",\
                        cstage=cSTAGE,\
                        ceo=cEO,\
                        cpreproc=cPREPROC,\
                        cspectral=cSPECTRAL,\
                        ccorrection=cCORRECTIONS,\
                        cprimary=cPRIMARY,\
                        cpostproc=cPOSTPROC), \
                        (None,None,None,None,None,None,None,\
                         None,None,None,None,None,None,None))

    # commit changes
    conn.commit()

    # close database
    conn.close()

def rezero(database,table_name,file_column,file_name,update_column,newval):

   # RE-ZERO
   conn, c = connectDB(database)
   c.execute("UPDATE {tn} SET {uc} = {nv} WHERE {fn} = {fname}".\
             format(tn=table_name, uc=update_column, nv = newval, \
             fn=file_column, fname='"'+file_name[0]+'"'))
   conn.commit()
   conn.close()

