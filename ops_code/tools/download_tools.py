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
import cdsapi
from dateutil.relativedelta import relativedelta
import pandas as pd
import code

from . import glider_tools as gt
from . import database_tools as db


def get_ecmwf(COORDS_LIST, D0, D1, var_file, clim=False, logging=None,\
        verbose=False, lat_lon_pad=1.0):

    c = cdsapi.Client()

    # COORDS_LIST is [W, E, S, N, t0, t1] — pad to ensure interpolation neighbours.
    N = float(COORDS_LIST[3]) + lat_lon_pad
    S = float(COORDS_LIST[2]) - lat_lon_pad
    W = float(COORDS_LIST[0]) - lat_lon_pad
    E = float(COORDS_LIST[1]) + lat_lon_pad
    area = [N, W, S, E]

    if D0.year != D1.year:
        raise NotImplementedError(
            'Multi-year ATMOS download not yet supported; deployment {}–{} spans years.'\
            .format(D0.isoformat(), D1.isoformat())
        )

    # Per-month retrieves to stay under CDS-Beta cost limits, then concat with ncrcat.
    tmp_dir = os.path.join(os.path.dirname(var_file), 'atmos_tmp')
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
    os.makedirs(tmp_dir)

    month_files = []
    year = D0.year
    for month in range(D0.month, D1.month + 1):
        month_file = os.path.join(tmp_dir, 'ATMOS_ECMWF_{}_{:02d}.nc'.format(year, month))
        ecmwf_dict = ecmwf_cfg(year, month, area)
        if logging is not None:
            logging.info('CDS request (year=%d, month=%d): %s', year, month, ecmwf_dict)
            logging.info('CDS target file: %s', month_file)
        print('Retrieving ATMOS for {}-{:02d}'.format(year, month))
        c.retrieve('reanalysis-era5-single-levels', ecmwf_dict, month_file)
        month_files.append(month_file)

    # Concat months along valid_time dim. ncrcat needs a record dim — make valid_time one.
    rec_files = []
    for mf in month_files:
        rec_file = mf.replace('.nc', '_rec.nc')
        cmd = 'ncks -O --mk_rec_dmn valid_time {} {}'.format(mf, rec_file)
        if logging is not None:
            logging.info(cmd)
        gt.execute(cmd, logging)
        rec_files.append(rec_file)

    cmd = 'ncrcat -O {} {}'.format(' '.join(sorted(rec_files)), var_file)
    if logging is not None:
        logging.info(cmd)
    gt.execute(cmd, logging)

    shutil.rmtree(tmp_dir)

def ecmwf_cfg(year, month, area):

    days   = ['{:02d}'.format(d) for d in range(1, 32)]
    hours  = ['{:02d}:00'.format(h) for h in range(24)]

    ecmwf_dict = {'product_type': 'reanalysis',
                'data_format': 'netcdf',
                'download_format': 'unarchived',
                'variable': [
                '10m_u_component_of_wind',
                '10m_v_component_of_wind',
                '2m_dewpoint_temperature',
                '2m_temperature',
                'mean_sea_level_pressure',
                'total_cloud_cover',
                'total_column_ozone',
                'total_column_water_vapour'],
                'year': str(year),
                'month': '{:02d}'.format(month),
                'day': days,
                'time': hours,
                'area': area}

    return ecmwf_dict


def get_remote(COORDS_LIST, D0, D1, TRA_CONFIG, variable, VAR_dir, \
               logging=None, verbose=False):
    '''
     Gets remote data
    '''

    tmp_dir = os.path.join(os.getcwd(),'tmp')
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
    os.makedirs(tmp_dir)
    os.chmod(tmp_dir, 0o777)

    for dd in np.arange(D0, D1, datetime.timedelta(days=1)):
        this_date = dd.astype(datetime.datetime)
        url = TRA_CONFIG[variable]['dt_url_root'] + TRA_CONFIG[variable]['url_template']
        url = url.replace('$Y', this_date.strftime('%Y'))
        url = url.replace('$m', this_date.strftime('%m'))
        url = url.replace('$d', this_date.strftime('%d'))
        url = url.replace('$j', this_date.strftime('%j'))

        downloaded_tmp_file = os.path.join(
            VAR_dir, os.path.basename(url).replace('.nc.dap.nc4', '.nc')
        )

        if os.path.exists(downloaded_tmp_file):
            os.remove(downloaded_tmp_file)

        # ---------------------------------------
        # NEW: Download via wget using Earthdata cookies
        # ---------------------------------------
        cookie_file = os.path.expanduser("~/.urs_cookies")
        netrc_file = os.path.expanduser("~/.netrc")
        local_download = os.path.join(tmp_dir, os.path.basename(downloaded_tmp_file))

        bashCommand = (
            f"wget --quiet --load-cookies {cookie_file} "
            f"--save-cookies {cookie_file} --keep-session-cookies "
            f"--netrc {netrc_file} -O {local_download} {url}"
        )
        db.shout(bashCommand, logging=logging, verbose=verbose)
        try:
            gt.execute(bashCommand, logging)
            gt.permit(local_download)
            db.shout('Download succeeded', logging=logging, verbose=verbose)
        except Exception as e:
            db.shout(f'Download failed: {e}', logging=logging, verbose=verbose)
            continue

        # ---------------------------------------
        # Now process the *local* file with ncks
        # ---------------------------------------
        bashCommand = (
            "ncks -O -D 1 "
            f"-d lon,{COORDS_LIST[0]},{COORDS_LIST[1]} "
            f"-d lat,{COORDS_LIST[2]},{COORDS_LIST[3]} "
            f"-v {','.join(TRA_CONFIG[variable]['vars'])} "
            f"{local_download} {os.path.join(tmp_dir, os.path.basename(downloaded_tmp_file))}"
        )

        db.shout(bashCommand, logging=logging, verbose=verbose)
        try:
            gt.execute(bashCommand, logging)
            gt.permit(os.path.join(tmp_dir, os.path.basename(downloaded_tmp_file)))
            db.shout('Subset succeeded', logging=logging, verbose=verbose)
        except Exception as e:
            db.shout(f'Subset failed: {e}', logging=logging, verbose=verbose)
            continue

        os.rename(os.path.join(tmp_dir, os.path.basename(downloaded_tmp_file)), downloaded_tmp_file)
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

    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)

    return sorted(match_files)

import os, fnmatch, datetime, subprocess, sys

def get_CMEMS_remote(COORDS_LIST, D0, D1, TRA_CONFIG, variable, VAR_dir, env_name="ppglider_cm", logging=None, verbose=False):
    """
    Download CMEMS data using Copernicus Marine Toolbox.

    Parameters:
        COORDS_LIST: [lon_min, lon_max, lat_min, lat_max]
        D0: datetime start
        D1: datetime end
        TRA_CONFIG: dict with dataset configuration
        variable: str, e.g., 'CHL'
        VAR_dir: directory to store downloaded files
        env_name: conda environment where copernicusmarine is installed
        logging, verbose: optional

    Returns:
        Sorted list of downloaded NetCDF files
    """

    os.makedirs(VAR_dir, exist_ok=True)
    this_date = D0
    
    while this_date <= D1:
        Dfname = this_date.strftime('%Y-%m-%d')
        D0_format = this_date.strftime('%Y-%m-%d %H:%M:%S')
        D1_format = (this_date + datetime.timedelta(days=1) - datetime.timedelta(seconds=1)).strftime('%Y-%m-%d %H:%M:%S')
        outname = f"{TRA_CONFIG[variable]['dt_product_id']}_{Dfname}.nc"

        # Build variable string
        vars_list = TRA_CONFIG[variable]['vars']
        var_flags = []
        for vv in vars_list:
            var_flags.extend(["-v", vv])

        # Build CopernicusMarine subset command
        CMD = [
            "conda", "run", "-n", env_name, "copernicusmarine", "subset",
            "-i", TRA_CONFIG[variable]['dt_product_id'],
            "--start-datetime", D0_format,
            "--end-datetime", D1_format,
            "--minimum-longitude", str(COORDS_LIST[0]),
            "--maximum-longitude", str(COORDS_LIST[1]),
            "--minimum-latitude", str(COORDS_LIST[2]),
            "--maximum-latitude", str(COORDS_LIST[3]),
            "--minimum-depth", str(TRA_CONFIG[variable]['depth_range'][0]),
            "--maximum-depth", str(TRA_CONFIG[variable]['depth_range'][1]),
            "--username", TRA_CONFIG[variable]['EO_username'],
            "--password", TRA_CONFIG[variable]['EO_password'],
            "--output-directory", VAR_dir,
            "--output-filename", outname
        ] + var_flags

        # Logging
        if verbose:
            print("Executing:", " ".join(CMD))
        if logging:
            logging.info("Executing: " + " ".join(CMD))

        try:
            subprocess.run(CMD, check=True)
            if logging:
                logging.info("Command successful")
            if verbose:
                print("Command successful")
        except subprocess.CalledProcessError as e:
            if logging:
                logging.error(f"Command failed: {e}")
            if verbose:
                print(f"Command failed: {e}")

        this_date += datetime.timedelta(days=1)

    # Collect downloaded files
    match_files = []
    for root, _, filenames in os.walk(VAR_dir):
        for filename in fnmatch.filter(filenames, '*.nc'):
            if logging:
                logging.info(f"Adding {os.path.join(root, filename)} to file list")
            if verbose:
                print(f"Adding {os.path.join(root, filename)} to file list")
            match_files.append(os.path.join(root, filename))

    return sorted(match_files)

def get_local(COORDS_LIST, D0, D1, TRA_CONFIG, variable, logging=None, verbose=False):
    # getting file list:
    match_files = []

    # need to date sort to be selective
    for dd in np.arange(D0, D1, datetime.timedelta(days=1)):
        dt = dd.astype(datetime.datetime)
        # two possible date formats
        match_strs = [
            dt.strftime('%Y-%m-%d') + '*.nc',   # format: 2018-05-03
            dt.strftime('%Y%m%d') + '*.nc'      # format: 20180503
        ]
        for root, _, filenames in os.walk(TRA_CONFIG[variable]['local_path_root']):
            for match_str in match_strs:
                for filename in fnmatch.filter(filenames, '*' + match_str):
                    db.shout('Adding ' + os.path.join(root, filename) + ' to file list',
                             logging=logging, verbose=verbose)
                    match_files.append(os.path.join(root, filename))

    return sorted(match_files)

def concat_files(TRA_CONFIG, variable, VAR_dir, var_file, match_files, \
                 COORDS_LIST, logging=None, verbose=False):

    #subset and add record dimension with sub-process
    tmp_dir = os.path.join(os.getcwd(),'tmp')
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

    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
