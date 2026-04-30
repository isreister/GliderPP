#!/usr/bin/env python
'''
Purpose:    Preprocesses staged glider profiles. Applies fluorescence quenching
            correction (per the per-glider config), derives PAR/CHLA-corrected
            fields and mixed-layer / euphotic-depth properties, and writes the
            text-format inputs required by the Morel19 primary-productivity model.

            Ported from the deleted operational_code/AlterEco_preprocessing.py
            (commit aa5ddf5, Ben Loveday, 2020) and adapted to the current
            ppglider_* / ConfigParser conventions.

Author:     Ben Loveday, Plymouth Marine Laboratory (original)
            Tim Smyth, Plymouth Marine Laboratory (original)

License:    See LICENCE.txt
'''
#-imports-----------------------------------------------------------------------
import argparse
import datetime
import glob
import logging
import os
import shutil
import sys
import warnings
import configparser

import numpy as np
from netCDF4 import Dataset
from scipy.interpolate import interp2d

import tools.database_tools as db
import tools.glider_tools as gt
import tools.common_tools as ct
import tools.fluor_correction as fcorr

#-messages----------------------------------------------------------------------
print('RUNNING: WARNINGS ARE SUPPRESSED')
warnings.filterwarnings('ignore')

#-default parameters------------------------------------------------------------
OUT_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
DEFAULT_LOG_PATH = os.path.join(OUT_ROOT, 'logs')
DEFAULT_CFG_DIR = os.path.join(OUT_ROOT, 'configs')
DEFAULT_CFG_FILE = os.path.join(DEFAULT_CFG_DIR, 'config_main.ini')

# Trajectory files we expect from ppglider_acquire_eo.py. Each maps to the
# variable names produced by the corresponding fly_cube derivation.
TRAJ_VAR_MAP = {
    'PAR'  : ['PAR'],
    'KD490': ['KD490'],
    'CHL'  : ['CHL', 'ZEU'],
    'SST'  : ['SST', 'SSS', 'MLD'],
    'ALTIM': ['UGOS', 'VGOS', 'UGOSA', 'VGOSA', 'SLA', 'ADT', 'EKE', 'MKE', 'TKE'],
    'ATMOS': ['WSPD', 'CLOUD', 'MSLP', 'O3', 'TCWV', 'RH'],
}


def load_trajectories(eo_dir, lon_var, lat_var, n_profiles, logging=None):
    '''Read all *_traj.nc files in eo_dir and return a flat dict of
    variable -> 1D array indexed by profile number. Missing trajectories are
    filled with NaNs so downstream code can index uniformly.'''

    traj = {}
    for vars_ in TRAJ_VAR_MAP.values():
        for v in vars_:
            traj[v] = np.full(n_profiles, np.nan)

    LON_traj = np.full(n_profiles, np.nan)
    LAT_traj = np.full(n_profiles, np.nan)

    for traj_file in sorted(glob.glob(os.path.join(eo_dir, '*_traj.nc'))):
        if logging is not None:
            logging.info('Reading trajectory: %s', traj_file)
        with Dataset(traj_file, 'r') as nc_fid:
            for v in nc_fid.variables:
                if v in traj:
                    arr = np.asarray(nc_fid.variables[v][:]).astype(float)
                    if arr.shape[0] == n_profiles:
                        traj[v] = arr
                elif v == lon_var:
                    LON_traj = np.asarray(nc_fid.variables[v][:]).astype(float)
                elif v == lat_var:
                    LAT_traj = np.asarray(nc_fid.variables[v][:]).astype(float)

    # CMEMS trajectory output uses fill-value sentinel; convert to NaN.
    for k, arr in traj.items():
        arr[arr == -9999] = np.nan
        traj[k] = arr

    return traj, LON_traj, LAT_traj


def load_bathy(bathy_file, lon_traj, lat_traj, logging=None):
    '''Interpolate elevation onto the trajectory points. Returns NaNs if
    bathy_file is unset or missing.'''

    if not bathy_file or not os.path.exists(bathy_file):
        if logging is not None:
            logging.info('No bathymetry file available; using NaN bathy.')
        return np.full(np.shape(lon_traj), np.nan)

    with Dataset(bathy_file, 'r') as nc_fid:
        blon = nc_fid.variables['lon'][:]
        blat = nc_fid.variables['lat'][:]
        xx = np.where((blon > np.nanmin(lon_traj)) & (blon < np.nanmax(lon_traj)))[0]
        yy = np.where((blat > np.nanmin(lat_traj)) & (blat < np.nanmax(lat_traj)))[0]
        BATHY = nc_fid.variables['elevation'][yy, xx]

    fn = interp2d(blon[xx], blat[yy], BATHY, kind='cubic')
    glider_bathy = np.full(np.shape(lon_traj), np.nan)
    for ii in range(len(glider_bathy)):
        glider_bathy[ii] = fn(lon_traj[ii], lat_traj[ii]) * -1
    return glider_bathy


def list_staged_files(staged_files_csv, staged_dir, glider_tag):
    '''Resolve the list of staged profile files to preprocess. Prefer the
    comma-separated record from the staged_files DB column; otherwise glob the
    staged_dir for *_st_fin.nc files matching the glider tag.'''

    if staged_files_csv:
        files = [f for f in staged_files_csv.split(',') if f]
        if files and all(os.path.exists(f) for f in files):
            return sorted(files)

    # Fallback: glob. glider_tag is e.g. 'ego_454_cabot' but staged files use
    # name + number ordering ('cabot_454_*_st_fin.nc'). Strip the prefix and
    # rebuild a permissive match pattern.
    parts = glider_tag.split('_')
    if len(parts) >= 3:
        pattern = f'*{parts[2]}*{parts[1]}*_st_fin.nc'
    else:
        pattern = '*_st_fin.nc'
    return sorted(glob.glob(os.path.join(staged_dir, pattern)))


#-arguments---------------------------------------------------------------------

PARSER = argparse.ArgumentParser()
PARSER.add_argument('-cfg', '--config_file', type=str,
                    default=DEFAULT_CFG_FILE,
                    help='Config file')
PARSER.add_argument('-v', '--verbose', action='store_true')
PARSER.add_argument('-l', '--log_path', type=str,
                    default=DEFAULT_LOG_PATH,
                    help='log file output path')
PARSER.add_argument('-ag', '--allowed_gliders', type=str, default='',
                    help='comma-separated whitelist of glider tags '
                         '(e.g. "ego_454_cabot"); empty processes all')
ARGS = PARSER.parse_args()

#-main--------------------------------------------------------------------------
if __name__ == "__main__":

    verbose = ARGS.verbose
    reprocess = True
    allowed_gliders = [g for g in ARGS.allowed_gliders.split(',') if g]

    # logging
    if not os.path.exists(os.path.abspath(ARGS.log_path)):
        os.makedirs(ARGS.log_path)
    LOGFILE = os.path.join(ARGS.log_path,
              "PPglider_preproc_" +
              datetime.datetime.now().strftime('%Y%m%d_%H%M') + ".log")
    try:
        if os.path.exists(LOGFILE):
            os.remove(LOGFILE)
        print("logging to: " + LOGFILE)
        logging.basicConfig(filename=LOGFILE, level=logging.DEBUG)
    except Exception as e:
        print("Failed to set logger: " + str(e))
        sys.exit(1)

    # read processing config
    module_config = configparser.ConfigParser(allow_no_value=True)
    module_config.read(ARGS.config_file)

    database_name = os.path.join(
        os.path.abspath(module_config['DIRECTORIES']['database_dir']),
        module_config['DATABASE']['database_name'])
    staged_root = os.path.abspath(module_config['DIRECTORIES']['staged_dir'])
    eo_root = os.path.abspath(module_config['DIRECTORIES']['eo_dir'])
    preproc_root = os.path.abspath(module_config['EO_ACQUIRE']['preproc_dir'])
    bathy_file = module_config['EO_ACQUIRE'].get('bathy_file', '') or ''

    if not os.path.exists(preproc_root):
        os.makedirs(preproc_root)
        os.chmod(preproc_root, 0o777)

    # database statuses
    all_keys = list(module_config['DATABASE_columns'].keys())
    nitems, db_dict = db.get_status(database_name,
                                    module_config['DATABASE']['table_name'],
                                    all_keys,
                                    logging=logging, verbose=verbose)

    glider_tags = [str(p) + '_' + str(n) + '_' + str(nm)
                   for p, n, nm in zip(db_dict['glider_prefix'],
                                       db_dict['glider_number'],
                                       db_dict['glider_name'])]

    is_eo = np.asarray(db_dict['eo_acquire']).astype(int)
    is_preproc = np.asarray(db_dict['preproc']).astype(int)

    # one preproc pass per unique glider — the trajectory + EO data are shared.
    seen = set()
    for item in range(nitems):
        glider_tag = glider_tags[item]
        if glider_tag in seen:
            continue
        seen.add(glider_tag)

        if allowed_gliders and glider_tag not in allowed_gliders:
            continue

        if not reprocess:
            if is_eo[item] != 1:
                db.shout(f'{glider_tag}: EO not acquired yet, skipping',
                         logging=logging, verbose=verbose)
                continue
            if is_preproc[item] == 1:
                db.shout(f'{glider_tag}: already preprocessed, skipping',
                         logging=logging, verbose=verbose)
                continue

        GLIDER_CONFIG = os.path.join(DEFAULT_CFG_DIR,
                                     f'config_{glider_tag}.ini')
        if not os.path.exists(GLIDER_CONFIG):
            db.shout(f'{glider_tag}: glider config {GLIDER_CONFIG} missing',
                     logging=logging, verbose=True)
            continue

        CONFIG_DICT = gt.read_config_file(GLIDER_CONFIG, logging=logging)
        correct_time = CONFIG_DICT.get('t_base', 'seconds') != 'matlab'
        tref = CONFIG_DICT['t_ref']

        eo_dir = os.path.join(eo_root, glider_tag)
        staged_dir = str(db_dict['staged_dir'][item]) or staged_root
        staged_files_csv = str(db_dict.get('staged_files', [''] * nitems)[item])

        preproc_dir = os.path.join(preproc_root, glider_tag)
        if not os.path.exists(preproc_dir):
            os.makedirs(preproc_dir)
            os.chmod(preproc_dir, 0o777)

        text_dir = os.path.join(preproc_root, 'pp', glider_tag)
        if not os.path.exists(text_dir):
            os.makedirs(text_dir)
            os.chmod(text_dir, 0o777)

        preprocessing_files = list_staged_files(staged_files_csv,
                                                staged_dir, glider_tag)
        if not preprocessing_files:
            db.shout(f'{glider_tag}: no staged files to preprocess',
                     logging=logging, verbose=True)
            continue

        n_profiles = len(preprocessing_files)
        db.shout(f'{glider_tag}: {n_profiles} profiles to preprocess',
                 logging=logging, verbose=verbose)

        # trajectories per profile
        traj, LON_traj, LAT_traj = load_trajectories(
            eo_dir,
            CONFIG_DICT.get('lon_var', 'LONGITUDE'),
            CONFIG_DICT.get('lat_var', 'LATITUDE'),
            n_profiles, logging=logging)

        glider_bathy = load_bathy(bathy_file, LON_traj, LAT_traj,
                                  logging=logging)

        # Hemsley bookkeeping (only meaningful if config selects it)
        all_night = np.zeros(n_profiles)
        all_day = np.zeros(n_profiles)
        all_good = np.zeros(n_profiles)
        all_bad = np.zeros(n_profiles)
        all_no_DCM = np.zeros(n_profiles)
        all_day_PAR = np.zeros(n_profiles)
        E_0_plus = np.zeros(n_profiles)

        output_files = []
        all_quench_methods_used = []
        last_MLD = np.nan
        last_ZEU = np.nan

        success_count = 0
        for traj_index, in_file in enumerate(preprocessing_files):
            output_file = os.path.join(
                preproc_dir,
                os.path.basename(in_file).replace(
                    '.nc', CONFIG_DICT.get('nc_tag', '_pp.nc')))
            if os.path.exists(output_file):
                os.chmod(output_file, 0o777)
                os.remove(output_file)
            shutil.copy(in_file, output_file)
            output_files.append(output_file)

            try:
                (success, all_night[traj_index], all_day[traj_index],
                 all_bad[traj_index], all_good[traj_index],
                 all_no_DCM[traj_index], all_day_PAR[traj_index],
                 E_0_plus[traj_index], quench_method_used,
                 last_MLD, last_ZEU) = gt.preprocess_dive(
                    output_file, GLIDER_CONFIG,
                    traj['PAR'][traj_index],
                    traj['KD490'][traj_index],
                    traj['CHL'][traj_index],
                    glider_bathy[traj_index],
                    traj['WSPD'][traj_index],
                    last_MLD, last_ZEU,
                    logging=logging, verbose=verbose,
                    correct_time=correct_time)
                if success:
                    success_count += 1
            except Exception as e:
                if logging is not None:
                    logging.exception('preprocess_dive failed for %s: %s',
                                      output_file, e)
                quench_method_used = 'None'
            all_quench_methods_used.append(quench_method_used)

        # Hemsley second pass (no-op if quench method not Hemsley)
        if 'Hemsley' in all_quench_methods_used:
            db.shout(f'{glider_tag}: Hemsley correction part 2',
                     logging=logging, verbose=verbose)
            regress = np.where((all_good == 1) & (all_night == 1) &
                               (all_no_DCM == 1))[0]
            correct = np.where((all_good == 1) & (all_day == 1))[0]
            hem_regress = [output_files[i] for i in regress]
            hem_correct = [output_files[i] for i in correct]
            try:
                fcorr.fluor_correction_Hem(GLIDER_CONFIG, hem_regress,
                                           hem_correct, glider_tag,
                                           logging=logging, verbose=verbose)
            except Exception as e:
                if logging is not None:
                    logging.exception('Hemsley pass-2 failed: %s', e)

        # text outputs for the PP model
        for count, output_file in enumerate(sorted(output_files)):
            try:
                with Dataset(output_file, 'r') as nc_fid:
                    PROFILE_NUMBERS = nc_fid.variables['PROFILE_NUMBER'][:]
                    if 'TIME' in nc_fid.variables:
                        TIME = nc_fid.variables['TIME'][:]
                    else:
                        TIME = nc_fid.variables['time'][:]
                    DEPTH = nc_fid.variables['DEPTH_CORRECTED'][:]
                    LAT = nc_fid.variables['LATITUDE_CORRECTED'][:]
                    LON = nc_fid.variables['LONGITUDE_CORRECTED'][:]
                    CHLA = nc_fid.variables['CHLA_CORRECTED'][:]
                    PAR = nc_fid.variables['DOWNWELLING_PAR_CORRECTED'][:]
                    ZEU = nc_fid.variables['EUPHOTIC_DEPTH'][:]
                    MLD = nc_fid.variables['MIXED_LAYER_DEPTH'][:]
                    TEMP = nc_fid.variables['CONSERVATIVE_TEMPERATURE'][:]
            except Exception as e:
                if logging is not None:
                    logging.exception('Skipping text output for %s: %s',
                                      output_file, e)
                continue

            if 'Masked' in str(type(CHLA)):
                CHLA = np.ma.filled(CHLA, np.nan)
            if 'Masked' in str(type(PAR)):
                PAR = np.ma.filled(PAR, np.nan)

            ct.output_text(np.nanmean(PROFILE_NUMBERS), TIME, tref,
                           DEPTH, CHLA, PAR,
                           traj['WSPD'][count], traj['RH'][count],
                           traj['TCWV'][count], traj['O3'][count],
                           traj['MSLP'][count], traj['CLOUD'][count],
                           traj['CHL'][count], traj['ZEU'][count],
                           E_0_plus[count],
                           np.nanmean(MLD), np.nanmean(ZEU),
                           LON, LAT, TEMP, text_dir,
                           'chl_profile', 'par_profile', all_day[count],
                           verbose=verbose, logging=logging,
                           correct_time=correct_time,
                           outfile_suffix=CONFIG_DICT.get(
                               'correction_file_suffix', '.txt'))

        # update DB on overall success
        if success_count > 0:
            today = "'" + datetime.datetime.now().strftime('%Y%m%d_%H%M') + "'"
            files_csv = ','.join(sorted(output_files))
            tn = module_config['DATABASE']['table_name']
            conn, c = db.connectDB(database_name)
            for di in np.where(np.array(glider_tags) == glider_tag)[0]:
                gd = str(db_dict['staged_dir'][di])
                c.execute(
                    "UPDATE {tn} SET preproc = 1 WHERE staged_dir = \"{gd}\"".
                    format(tn=tn, gd=gd))
                c.execute(
                    "UPDATE {tn} SET preproc_date = {td} "
                    "WHERE staged_dir = \"{gd}\"".format(
                        tn=tn, td=today, gd=gd))
                c.execute(
                    "UPDATE {tn} SET preproc_dir = \"{pd}\" "
                    "WHERE staged_dir = \"{gd}\"".format(
                        tn=tn, pd=preproc_dir, gd=gd))
                c.execute(
                    "UPDATE {tn} SET preproc_files = \"{fs}\" "
                    "WHERE staged_dir = \"{gd}\"".format(
                        tn=tn, fs=files_csv, gd=gd))
            conn.commit()
            conn.close()
            db.shout(f'{glider_tag}: preprocessed {success_count}/{n_profiles} '
                     f'profiles successfully', logging=logging,
                     verbose=True)
        else:
            db.shout(f'{glider_tag}: preprocessing failed for all profiles',
                     logging=logging, verbose=True)
#--EOF
