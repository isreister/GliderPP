#!/usr/bin/env python
'''
Purpose:    Tools to facilitate downloading

Version:    v1.0 10/2021

Author:     Ben Loveday, Plymouth Marine Laboratory / Innoflair UG
            Time Smyth, Plymouth Marine Laboratory

License:    See LICENCE.txt
'''
import argparse, os, sys, shutil, datetime, logging
import subprocess
import numpy as np
import fnmatch
from ecmwfapi import ECMWFDataServer
from dateutil.relativedelta import relativedelta

from . import glider_tools as gt
from . import database_tools as db


def get_ecmwf(COORDS_LIST, D0, D1, var_file, clim=False, logging=None,\
        verbose=False):
    server     = ECMWFDataServer()
    area       = [float(COORDS_LIST[3]),\
                  float(COORDS_LIST[0]),\
                  float(COORDS_LIST[2]),\
                  float(COORDS_LIST[1])] #N/W/S/E

    ecmwf_dict = ecmwf_cfg(D0, D1, area, var_file, clim=clim)      
    if verbose:
        print(ecmwf_dict)
    server.retrieve(ecmwf_dict)

def ecmwf_cfg(D0,D1,area,outfile,clim=False):
   # https://software.ecmwf.int/wiki/display/WEBAPI/Python+ERA-interim+examples

   date_formatted  = D0.strftime('%Y-%m-%d')+'/to/'+\
                     D1.strftime('%Y-%m-%d')
   area_formatted  = str(area[0])+'/'+\
                     str(area[1])+'/'+\
                     str(area[2])+'/'+\
                     str(area[3])
   #                
   #                 U_10m/V_10m/Cloud/MSLP/O3/tcwv/t2m/d2m
   vars_form = "165.128/166.128/164.128/151.128/206.128/137.128/167.128/168.128"

   if clim:
      # need to alter date format
      Diter=D0
      date_formatted=str(D0.year)+str(D0.month).zfill(2)+'01'
      while Diter <= D1:
         Diter = Diter + relativedelta(months=1)
         if Diter < D1:
            date_formatted=date_formatted+'/'+str(Diter.year)\
                           +str(Diter.month).zfill(2)+'01'

      ecmwf_dict = {'stream'    : "moda",
                    'levtype'   : "sfc",
                    'param'     : vars_form,
                    'dataset'   : "interim",
                    'step'      : "0",
                    'expver'    : "1",
                    'grid'      : "0.75/0.75",
                    'date'      : date_formatted,
                    'type'      : "an",
                    'class'     : "ei",
                    'area'      : area_formatted,
                    'format'    : "netcdf",
                    'target'    : outfile
      }
   else:
      ecmwf_dict = {'stream'    : "oper",
                    'levtype'   : "sfc",
                    'param'     : vars_form,
                    'dataset'   : "interim",
                    'step'      : "0",
                    'expver'    : "1",
                    'grid'      : "0.75/0.75",
                    'time'      : "00:00:00/06:00:00/12:00:00/18:00:00",
                    'date'      : date_formatted,
                    'type'      : "an",
                    'class'     : "ei",
                    'area'      : area_formatted,
                    'format'    : "netcdf",
                    'target'    : outfile
      }

   return ecmwf_dict


def get_remote(COORDS_LIST, D0, D1, TRA_CONFIG, variable, VAR_dir, \
               logging=None, verbose=False):
    '''
     Gets remote data
    '''
    for dd in np.arange(D0, D1, datetime.timedelta(days=1)):
        this_date = dd.astype(datetime.datetime)
        url = TRA_CONFIG[variable]['url_root']+\
              TRA_CONFIG[variable]['url_template']
        url = url.replace('$Y',this_date.strftime('%Y'))
        url = url.replace('$m',this_date.strftime('%m'))
        url = url.replace('$d',this_date.strftime('%d'))
        url = url.replace('$j',this_date.strftime('%j'))

        tmp_dir = '/home/ben/shared/Linux_desktop/local1/data/scratch/blo/AlterEco/operational_code/'
        downloaded_tmp_file = VAR_dir + '/' \
                              + os.path.basename(url).replace('.nc.nc','.nc')

        if os.path.exists(downloaded_tmp_file):
            os.remove(downloaded_tmp_file)

        bashCommand = "ncks -O -D 1 -d lon,"+COORDS_LIST[0]+","+\
                      COORDS_LIST[1]+" "+"-d lat,"+COORDS_LIST[2]+","+\
                      COORDS_LIST[3]+" "+"-v "+\
                      ",".join(TRA_CONFIG[variable]['vars'])+\
                      " "+url+" -l "+tmp_dir + " " + os.path.basename(downloaded_tmp_file)

        db.shout(bashCommand, logging=logging, verbose=verbose)

        try:
            gt.execute(bashCommand,logging)
            gt.permit(os.path.join(tmp_dir,os.path.basename(downloaded_tmp_file)))
            db.shout('Process succeeded', logging=logging, verbose=verbose)
        except:
            db.shout('Process failed', logging=logging, verbose=verbose)
        
        os.rename(os.path.join(tmp_dir,os.path.basename(downloaded_tmp_file)), downloaded_tmp_file)
        os.chmod(downloaded_tmp_file, 0o777)
        
        # add time dimension
        try:
            out_file = downloaded_tmp_file.replace('.nc','_time_add.nc')
            file_time = (this_date - datetime.datetime(2000,1,1,0,0,0))\
                                 .total_seconds()
            bashCommand = "ncap2 -O -s 'defdim("+\
                          '"time"'+",1);time[time]=double("\
                          +str(file_time)+")' "+downloaded_tmp_file+\
                          " "+out_file
            db.shout(bashCommand, logging=logging, verbose=verbose)
            gt.execute(bashCommand,logging)
            os.remove(downloaded_tmp_file)
            db.shout('Process succeeded', logging=logging, verbose=verbose)
        except:
            db.shout('Process failed', logging=logging, verbose=verbose)

        # add time dimension to vars and make record dim
        try:
            out_file2 = out_file.replace('_time_add.nc','_time_record.nc')
            bashCommand = "ncecat -u time "+out_file+" "+out_file2
            db.shout(bashCommand, logging=logging, verbose=verbose)

            gt.execute(bashCommand,logging)
            os.remove(out_file)
            db.shout('Process succeeded', logging=logging, verbose=verbose)
        except:
            db.shout('Process failed', logging=logging, verbose=verbose)

    #getting file list:
    match_files = []
    for root, _, filenames in os.walk(VAR_dir):
        for filename in fnmatch.filter(filenames,\
                                            '*.nc'):
            db.shout('Adding '+os.path.join(root, filename)+\
                     ' to file list', logging=logging, \
                       verbose=verbose)
            match_files.append(os.path.join(root, filename))

    return sorted(match_files)

def get_CMEMS_remote(COORDS_LIST, D0, D1, TRA_CONFIG, variable, VAR_dir, \
               logging=None, verbose=False):

    # set variables
    v_string=' --variable '
    all_variables = ' '
    for vv in TRA_CONFIG[variable]['vars']:
        all_variables=v_string+"'"+vv+"'"+all_variables

    this_date = D0
    while this_date <= D1:
        Dfname = this_date.strftime('%Y-%m-%d')
        D0_format = this_date.strftime('%Y-%m-%d %H:%M:%S')
        D1_format = this_date+\
                    datetime.timedelta(days=1)-datetime.timedelta(seconds=1)
        D1_format = D1_format.strftime('%Y-%m-%d %H:%M:%S')
        outname = TRA_CONFIG[variable]['product_id']+\
                  '_'+Dfname+'.nc'
    
        CMD="python "+\
          " -m motuclient "+\
          " --user '"+TRA_CONFIG[variable]['EO_username']+"'"+\
          " --pwd '"+TRA_CONFIG[variable]['EO_password']+"'"+\
          " --motu '"+TRA_CONFIG[variable]['url_root']+"'"+\
          " --service-id '"+TRA_CONFIG[variable]['service_id']+"'"+\
          " --product-id '"+TRA_CONFIG[variable]['product_id']+"'"+\
          " --longitude-min '"+str(COORDS_LIST[0])+"'"+\
          " --longitude-max '"+str(COORDS_LIST[1])+"'"+\
          " --latitude-min '"+str(COORDS_LIST[2])+"'"+\
          " --latitude-max '"+str(COORDS_LIST[3])+"'"+\
          " --date-min '"+D0_format+"'"+\
          " --date-max '"+D1_format+"'"+\
          all_variables+\
          " --depth-min '"+str(TRA_CONFIG[variable]['depth_range'][0])+"'"+\
          " --depth-max '"+str(TRA_CONFIG[variable]['depth_range'][1])+"'"+\
          " --out-dir '"+VAR_dir+'/'+"'"+\
          " --out-name '"+outname+"'"

        this_date = this_date + datetime.timedelta(days=1)
        db.shout(CMD, logging=logging, verbose=verbose)
        try:
            output = gt.execute(CMD,logging)
            print(output)
            if 'Invalid date range' in str(output):
                db.shout('Command unsuccessful (Invalid date range); trying alternate', logging=logging, verbose=verbose)
                CMD = CMD.replace(TRA_CONFIG[variable]['service_id'],TRA_CONFIG[variable]['alt_service_id'])
                CMD = CMD.replace(TRA_CONFIG[variable]['product_id'],TRA_CONFIG[variable]['alt_product_id'])
                CMD = CMD.replace(TRA_CONFIG[variable]['url_root'],TRA_CONFIG[variable]['alt_url_root']) 
                db.shout(CMD, logging=logging, verbose=verbose)
                gt.execute(CMD,logging)
                db.shout('Command successful', logging=logging, verbose=verbose)
            else:
                db.shout('Command successful', logging=logging, verbose=verbose)
        except:
            db.shout('Command failed; proceeding to next iterate', \
                     logging=logging, verbose=verbose)

    #getting file list:
    match_files = []
    for root, _, filenames in os.walk(VAR_dir):
        for filename in fnmatch.filter(filenames,\
                                            '*.nc'):
            db.shout('Adding '+os.path.join(root, filename)+\
                     ' to file list', logging=logging, \
                       verbose=verbose)
            match_files.append(os.path.join(root, filename))

    return sorted(match_files)

def get_local(COORDS_LIST, D0, D1, TRA_CONFIG, variable, logging=None,\
              verbose=False):
    #getting file list:
    match_files = []

    #need to date sort to be selective
    for dd in np.arange(D0, D1, datetime.timedelta(days=1)):
        match_str = dd.astype(datetime.datetime)\
                             .strftime('%Y%m%d')+'*.nc'
        for root, _, filenames in os.walk(TRA_CONFIG[variable]\
                                                    ['local_path_root']):
            for filename in fnmatch.filter(filenames,'*'+match_str):
                db.shout('Adding '+os.path.join(root, filename)+\
                         ' to file list', logging=logging, verbose=verbose)
                match_files.append(os.path.join(root, filename))

    return sorted(match_files)

def concat_files(TRA_CONFIG, variable, VAR_dir, var_file, match_files, \
                 COORDS_LIST, logging=None, verbose=False):

    #subset and add record dimension with sub-process
    tmp_dir = VAR_dir+'/tmp/'
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
    os.makedirs(tmp_dir)
    os.chmod(tmp_dir, 0o777)

    prepared_files = []
    count = -1
    for match_file in match_files:
        count = count + 1
        db.shout('Preparing '+match_file, logging=logging, verbose=verbose)

        prepared_file = tmp_dir + '/' + os.path.basename(match_file)
        prepared_file_regrid = prepared_file.replace('.nc','_regrid.nc')
        # Handle CMEMS file naming
        prepared_file = prepared_file.replace('-rt-','-rep-')
        prepared_file_renamed = prepared_file.replace('-nrt-','-rep-')

        # make sure lon coord is on correct frame:
        lon = TRA_CONFIG[variable]['lon_var']
        bashCommand = 'ncap2 -O -s "where('+lon+'>180)'+lon+'='+lon+'-360" '+\
                      match_file+' '+prepared_file_regrid

        db.shout(bashCommand, logging=logging, verbose=verbose)

        try:
            # be wary, nco does not report errors very well...investigate
            gt.execute(bashCommand,logging)
            db.shout('Command successful', logging=logging, verbose=verbose)
        except:
            db.shout('Command failed; proceeding to next iterate', \
                     logging=logging, verbose=verbose)  

        bashCommand = "ncks -O --mk_rec_dmn "+\
                      TRA_CONFIG[variable]['t_var']+\
                      " -d "+TRA_CONFIG[variable]['lon_var']+","+\
                      COORDS_LIST[0]+","+COORDS_LIST[1]+" "+\
                      " -d "+TRA_CONFIG[variable]['lat_var']+","+\
                      COORDS_LIST[2]+","+COORDS_LIST[3]+" "+\
                      "-v "+",".join(TRA_CONFIG[variable]['vars'])+\
                      " "+prepared_file_regrid+" "+prepared_file_renamed

        db.shout(bashCommand, logging=logging, verbose=verbose)
        prepared_files.append(prepared_file_renamed)

        try:
            # be wary, nco does not report errors very well...investigate
            gt.execute(bashCommand,logging)
            db.shout('Command successful', logging=logging, verbose=verbose)
            os.remove(prepared_file_regrid)
        except:
            db.shout('Command failed; proceeding to next iterate', \
                     logging=logging, verbose=verbose)

    #concat files into cube using subprocess
    bashCommand = "ncrcat -O "+\
                       " ".join(sorted(prepared_files))+" "+var_file
    db.shout(bashCommand, logging=logging, verbose=verbose)
    try:
        gt.execute(bashCommand,logging)
        db.shout(bashCommand, logging=logging, verbose=verbose)
        db.shout('Command successful', logging=logging, verbose=verbose)

        if os.path.exists(VAR_dir):
            shutil.rmtree(VAR_dir)

    except:
        db.shout('Command failed; proceeding to next variable', \
                 logging=logging, verbose=verbose)

