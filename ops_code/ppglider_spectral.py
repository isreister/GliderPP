#!/usr/bin/env python
'''
Purpose:    For each preprocessed glider station, generate a spectral GC90 PAR
            irradiance file via the precompiled `par` binary, then determine
            CHL and Ed scaling factors that minimise RMSE between the
            depth-projected modelled PAR profile and the measured glider PAR
            profile. Outputs:
              - ed_NNNNNN_<suffix>     (multi-time × multi-wavelength irradiance)
              - zen_NNNNNN_<suffix>    (zenith angles per timestep)
              - scale_NNNNNN_<suffix>  (CHL_scale, Ed_scale)

            Ported from the deleted operational_code/project_spectral_PAR.py
            and STAGE 4 of operational_code/Process_PP_gliders.run
            (commit aa5ddf5, Ben Loveday, 2020), adapted to the current
            ppglider_* / ConfigParser conventions.

Author:     Ben Loveday, Plymouth Marine Laboratory (original)
            Tim Smyth, Plymouth Marine Laboratory (original)

License:    See LICENCE.txt
'''
#-imports-----------------------------------------------------------------------
import argparse
import configparser
import datetime
import glob
import logging
import os
import subprocess
import sys
import warnings

import numpy as np
from scipy.integrate import simps
from scipy.interpolate import interp1d

import tools.database_tools as db

#-messages----------------------------------------------------------------------
print('RUNNING: WARNINGS ARE SUPPRESSED')
warnings.filterwarnings('ignore')

#-default parameters------------------------------------------------------------
OUT_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
DEFAULT_LOG_PATH = os.path.join(OUT_ROOT, 'logs')
DEFAULT_CFG_DIR = os.path.join(OUT_ROOT, 'configs')
DEFAULT_CFG_FILE = os.path.join(DEFAULT_CFG_DIR, 'config_main.ini')

# Pure-seawater attenuation coefficients for the standard 400-700 nm @ 5 nm
# grid the GC90 binary emits. Lifted verbatim from the original
# project_spectral_PAR.py (Loveday 2017). Indexed by wavelength bin.
A_WV = np.asarray([
    0.0171, 0.01665, 0.0162, 0.01575, 0.0153, 0.01485, 0.0144, 0.01445, 0.0145,
    0.0145, 0.0145, 0.01505, 0.0156, 0.0156, 0.0156, 0.0166, 0.0176, 0.0186,
    0.0196, 0.02265, 0.0257, 0.0307, 0.0357, 0.0417, 0.0477, 0.0492, 0.0507,
    0.05325, 0.0558, 0.0598, 0.0638, 0.0673, 0.0708, 0.07535, 0.0799, 0.09395,
    0.108, 0.1325, 0.157, 0.2005, 0.244, 0.2665, 0.289, 0.299, 0.309, 0.314,
    0.319, 0.324, 0.329, 0.339, 0.349, 0.3745, 0.4, 0.415, 0.43, 0.44, 0.45,
    0.475, 0.5, 0.575, 0.65,
]).astype(float)

B_WV = np.asarray([
    0.0076, 0.0072, 0.0068, 0.00645, 0.0061, 0.0058, 0.0055, 0.0052, 0.0049,
    0.0047, 0.0045, 0.0043, 0.0041, 0.0039, 0.0037, 0.00355, 0.0034, 0.00325,
    0.0031, 0.003, 0.0029, 0.00275, 0.0026, 0.0025, 0.0024, 0.0023, 0.0022,
    0.00215, 0.0021, 0.002, 0.0019, 0.00185, 0.0018, 0.00175, 0.0017, 0.00165,
    0.0016, 0.00155, 0.0015, 0.00145, 0.0014, 0.00135, 0.0013, 0.00125, 0.0012,
    0.00115, 0.0011, 0.00105, 0.001, 0.001, 0.001, 0.0009, 0.0008, 0.0008,
    0.0008, 0.00075, 0.0007, 0.0007, 0.0007, 0.0007, 0.0007,
]).astype(float)

E_WV = np.asarray([
    0.64358, 0.647665, 0.65175, 0.65546, 0.65917, 0.6625, 0.66583, 0.66879,
    0.67175, 0.674335, 0.67692, 0.67913, 0.68134, 0.683175, 0.68501, 0.686475,
    0.68794, 0.688745, 0.68955, 0.689175, 0.6888, 0.687235, 0.68567, 0.68291,
    0.68015, 0.676195, 0.67224, 0.667095, 0.66195, 0.65561, 0.64927, 0.644635,
    0.64, 0.6315, 0.623, 0.6165, 0.61, 0.614, 0.618, 0.622, 0.626, 0.63, 0.634,
    0.638, 0.642, 0.6475, 0.653, 0.658, 0.663, 0.6675, 0.672, 0.677, 0.682,
    0.6885, 0.695, 0.694, 0.693, 0.6665, 0.64, 0.62, 0.6,
]).astype(float)

X_WV = np.asarray([
    0.11748, 0.120035, 0.12259, 0.12264, 0.12269, 0.12024, 0.11779, 0.11371,
    0.10963, 0.10564, 0.10165, 0.09779, 0.09393, 0.09021, 0.08649, 0.082905,
    0.07932, 0.07587, 0.07242, 0.069105, 0.06579, 0.06261, 0.05943, 0.05642,
    0.05341, 0.05085, 0.04829, 0.04624, 0.04419, 0.04265, 0.04111, 0.040055,
    0.039, 0.0375, 0.036, 0.0345, 0.033, 0.03275, 0.0325, 0.03325, 0.034,
    0.035, 0.036, 0.03725, 0.0385, 0.04025, 0.042, 0.043, 0.044, 0.0445, 0.045,
    0.04625, 0.0475, 0.0495, 0.0515, 0.051, 0.0505, 0.04475, 0.039, 0.0345,
    0.03,
]).astype(float)


def parse_telemetry(telemetry_file):
    '''Read a 'key value' telemetry file produced by ppglider_preproc.py.'''
    out = {}
    with open(telemetry_file) as fh:
        for line in fh:
            parts = line.strip().split()
            if len(parts) >= 2:
                out[parts[0]] = parts[1]
    return out


def run_par_binary(par_binary, par_lib_dir, gcirrad_data, telem,
                   ed_file, zen_file, time_step=5, logging=None):
    '''Invoke the precompiled GC90 `par` binary with the right env and args.
    Mirrors STAGE 4 of operational_code/Process_PP_gliders.run.'''

    env = os.environ.copy()
    env['LD_LIBRARY_PATH'] = par_lib_dir + ':' + env.get('LD_LIBRARY_PATH', '')

    cmd = [
        par_binary,
        '--lon', str(telem['longitude']),
        '--lat', str(telem['latitude']),
        '--atmo_read', gcirrad_data,
        '--D', str(int(float(telem['jday']))),
        '--P', str(telem['mslp']),
        '--O_3', str(telem['o3']),
        '--C', str(telem['cloud']),
        '--W', str(telem['wspd']),
        '--RH', str(telem['rh']),
        '--WV', str(telem['tcwv']),
        '--time_step', str(time_step),
        '--par', ed_file,
        '--zen', zen_file,
    ]

    if os.path.exists(ed_file):
        os.remove(ed_file)
    if os.path.exists(zen_file):
        os.remove(zen_file)

    proc = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if proc.returncode != 0:
        if logging is not None:
            logging.error('par binary failed (rc=%d): %s', proc.returncode,
                          proc.stderr)
        raise RuntimeError('par binary returned %d: %s' %
                           (proc.returncode, proc.stderr.strip()))
    return ed_file, zen_file


def read_ed_file(ed_file):
    '''Read the multi-time × multi-wavelength irradiance produced by `par`.
    Each row: HH:MM<TAB>wavelength<TAB>Ed<TAB>alpha.'''
    rows = np.genfromtxt(ed_file, dtype=("|S10", float, float, float))
    times = np.array([r[0].decode('utf-8') for r in rows])
    wv = np.array([r[1] for r in rows])
    ed = np.array([r[2] for r in rows])
    return times, wv, ed


def select_nearest_time(times, wv, ed, glider_time):
    '''Pick the row(s) whose timestep is closest to glider_time (HH:MM).'''
    hh, mm = glider_time.split(':')
    t_glider = datetime.datetime(2000, 1, 1, int(hh), int(mm))
    t_off = np.array([
        abs((datetime.datetime(2000, 1, 1, int(t.split(':')[0]),
                                int(t.split(':')[1])) - t_glider).total_seconds())
        for t in times
    ])
    sel = np.where(t_off == np.nanmin(t_off))[0]
    return wv[sel], ed[sel]


def spectral_par_depth(ed_wv, wv, depths, chl, scaling, a_wv, b_wv, e_wv, x_wv):
    '''Project spectral PAR through depth using exponential attenuation.'''
    e_depth = np.full((len(depths), len(wv)), np.nan)
    kw = a_wv + 0.5 * b_wv  # pure-water attenuation, depth-independent
    for zz in range(len(depths)):
        kc = x_wv * (chl[zz] * scaling) ** e_wv
        ktot = kw + kc
        if zz == 0:
            e_depth[zz, :] = ed_wv * np.exp(-ktot * depths[0])
        else:
            e_depth[zz, :] = e_depth[zz - 1, :] * \
                             np.exp(-ktot * (depths[zz] - depths[zz - 1]))
    wv_diff = np.nanmean(wv[1:] - wv[:-1])
    modelled_par = np.nansum(e_depth * wv_diff, axis=1)
    return modelled_par


def rmse(meas, mod):
    good = np.isfinite(meas) & np.isfinite(mod)
    if not np.any(good):
        return np.inf
    return float(((meas[good] - mod[good]) ** 2).mean() ** 0.5)


def process_station(station_id, suffix, pp_dir, out_dir,
                    par_binary, par_lib_dir, gcirrad_data,
                    time_step, logging=None, verbose=False):
    '''Run the spectral pipeline for a single station. Returns (success, files).'''

    chl_file = os.path.join(pp_dir, f'chl_profile_station_{station_id}{suffix}')
    par_file = os.path.join(pp_dir, f'par_profile_station_{station_id}{suffix}')
    telem_file = os.path.join(pp_dir, f'telemetry_station_{station_id}{suffix}')

    for f in (chl_file, par_file, telem_file):
        if not os.path.exists(f):
            return False, []

    telem = parse_telemetry(telem_file)
    if telem.get('is_day', '0').strip() in ('0', '0.0'):
        if logging is not None:
            logging.info('Station %s nighttime — skipping spectral.', station_id)
        return False, []

    ed_file = os.path.join(out_dir, f'ed_station_{station_id}{suffix}')
    zen_file = os.path.join(out_dir, f'zen_station_{station_id}{suffix}')
    scale_file = os.path.join(out_dir, f'scale_station_{station_id}{suffix}')

    try:
        run_par_binary(par_binary, par_lib_dir, gcirrad_data, telem,
                       ed_file, zen_file, time_step=time_step, logging=logging)
    except Exception as e:
        if logging is not None:
            logging.exception('par binary failed for station %s: %s',
                              station_id, e)
        return False, []

    times, wv_all, ed_all = read_ed_file(ed_file)
    glider_time = telem.get('time', '12:00')
    wv, ed = select_nearest_time(times, wv_all, ed_all, glider_time)

    e0p = float(telem.get('E0p', 'nan'))
    ed_total_modelled = simps(ed, dx=5)
    if e0p <= 0.0 or not np.isfinite(e0p) or ed_total_modelled <= 0.0:
        ed_scale = 1.0
    else:
        ed_scale = e0p / ed_total_modelled
    ed_new = ed * ed_scale

    # Read profile data: each row is "HH:MM depth value".
    chl_data = np.atleast_2d(np.genfromtxt(chl_file, dtype=float))
    par_data = np.atleast_2d(np.genfromtxt(par_file, dtype=float))
    if chl_data.shape[1] < 3 or par_data.shape[1] < 3:
        if logging is not None:
            logging.info('Station %s profile too short, scale=1.', station_id)
        chl_scale = 1.0
    else:
        depths = chl_data[:, 1]
        chl = chl_data[:, 2]
        par_meas = par_data[:, 2]

        # Ensure surface-first ordering.
        good_d = depths[np.isfinite(depths)]
        if good_d.size and abs(good_d[0]) > abs(good_d[-1]):
            par_meas = par_meas[::-1]
            chl = chl[::-1]
            depths = depths[::-1]

        good_par = par_meas[np.isfinite(par_meas)]
        if (good_par.size == 0 or
                good_par[-1] >= good_par[0] or
                np.nanmax(par_meas) < 1):
            chl_scale = 1.0
        else:
            chl_scale = 1.0
            best = np.inf
            for trial in np.arange(0.2, 25.0, 0.2):
                mod_par = spectral_par_depth(
                    ed_new, wv, depths, chl, trial,
                    A_WV, B_WV, E_WV, X_WV)
                err = rmse(par_meas, mod_par)
                if err < best:
                    best = err
                    chl_scale = float(trial)

    with open(scale_file, 'w') as fh:
        fh.write('CHL_scale ' + str(chl_scale) + '\n')
        fh.write('Ed_scale ' + str(ed_scale))

    return True, [ed_file, zen_file, scale_file]


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
                         '(empty processes all preprocessed gliders)')
ARGS = PARSER.parse_args()

#-main--------------------------------------------------------------------------
if __name__ == "__main__":
    verbose = ARGS.verbose
    allowed = [g for g in ARGS.allowed_gliders.split(',') if g]

    if not os.path.exists(os.path.abspath(ARGS.log_path)):
        os.makedirs(ARGS.log_path)
    LOGFILE = os.path.join(
        ARGS.log_path,
        'PPglider_spectral_' +
        datetime.datetime.now().strftime('%Y%m%d_%H%M') + '.log')
    if os.path.exists(LOGFILE):
        os.remove(LOGFILE)
    print('logging to: ' + LOGFILE)
    logging.basicConfig(filename=LOGFILE, level=logging.DEBUG)

    module_config = configparser.ConfigParser(allow_no_value=True)
    module_config.read(ARGS.config_file)

    database_name = os.path.join(
        os.path.abspath(module_config['DIRECTORIES']['database_dir']),
        module_config['DATABASE']['database_name'])
    preproc_root = os.path.abspath(module_config['EO_ACQUIRE']['preproc_dir'])
    spectral_root = os.path.abspath(module_config['SPECTRAL']['spectral_dir'])
    par_binary = module_config['SPECTRAL']['par_binary']
    par_lib_dir = module_config['SPECTRAL']['par_lib_dir']
    gcirrad_data = module_config['SPECTRAL']['gcirrad_data']
    time_step = int(module_config['SPECTRAL']['time_step'])

    if not os.path.exists(par_binary):
        db.shout(f'par binary not found at {par_binary}',
                 logging=logging, verbose=True)
        sys.exit(1)
    if not os.path.exists(gcirrad_data):
        db.shout(f'gcirrad.dat not found at {gcirrad_data}',
                 logging=logging, verbose=True)
        sys.exit(1)

    if not os.path.exists(spectral_root):
        os.makedirs(spectral_root)
        os.chmod(spectral_root, 0o777)

    all_keys = list(module_config['DATABASE_columns'].keys())
    nitems, db_dict = db.get_status(
        database_name, module_config['DATABASE']['table_name'],
        all_keys, logging=logging, verbose=verbose)

    glider_tags = [str(p) + '_' + str(n) + '_' + str(nm)
                   for p, n, nm in zip(db_dict['glider_prefix'],
                                       db_dict['glider_number'],
                                       db_dict['glider_name'])]
    is_preproc = np.asarray(db_dict['preproc']).astype(int)

    seen = set()
    for item in range(nitems):
        glider_tag = glider_tags[item]
        if glider_tag in seen:
            continue
        seen.add(glider_tag)

        if allowed and glider_tag not in allowed:
            continue
        if is_preproc[item] != 1:
            db.shout(f'{glider_tag}: preproc not done; skipping spectral',
                     logging=logging, verbose=verbose)
            continue

        # per-glider preproc text dir (matches ppglider_preproc.py layout)
        pp_dir = os.path.join(preproc_root, 'pp', glider_tag)
        if not os.path.isdir(pp_dir):
            db.shout(f'{glider_tag}: no preproc text dir at {pp_dir}',
                     logging=logging, verbose=True)
            continue

        out_dir = os.path.join(spectral_root, glider_tag)
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
            os.chmod(out_dir, 0o777)

        # Collect station IDs from existing telemetry files; their suffix is
        # whatever follows 'station_NNNNNN' in the filename.
        telem_files = sorted(glob.glob(
            os.path.join(pp_dir, 'telemetry_station_*')))
        stations = []
        for tf in telem_files:
            base = os.path.basename(tf)
            # base = 'telemetry_station_NNNNNN<suffix>' where suffix often
            # starts with '_' or '.', e.g. '_xing.txt'
            after = base[len('telemetry_station_'):]
            # split off the leading 6-digit station id
            station_id = after[:6]
            suffix = after[6:]
            stations.append((station_id, suffix))

        if not stations:
            db.shout(f'{glider_tag}: no telemetry files in {pp_dir}',
                     logging=logging, verbose=True)
            continue

        db.shout(f'{glider_tag}: spectral on {len(stations)} stations',
                 logging=logging, verbose=verbose)

        success_count = 0
        produced_files = []
        for idx, (station_id, suffix) in enumerate(stations):
            try:
                ok, files = process_station(
                    station_id, suffix, pp_dir, out_dir,
                    par_binary, par_lib_dir, gcirrad_data,
                    time_step, logging=logging, verbose=verbose)
                if ok:
                    success_count += 1
                    produced_files.extend(files)
            except Exception as e:
                if logging is not None:
                    logging.exception('Station %s failed: %s', station_id, e)
            if verbose and (idx + 1) % 500 == 0:
                print(f'  {idx + 1}/{len(stations)} stations processed')

        if success_count > 0:
            today = "'" + datetime.datetime.now().strftime('%Y%m%d_%H%M') + "'"
            files_csv = ','.join(sorted(produced_files))
            tn = module_config['DATABASE']['table_name']
            conn, c = db.connectDB(database_name)
            for di in np.where(np.array(glider_tags) == glider_tag)[0]:
                gd = str(db_dict['staged_dir'][di])
                c.execute(
                    "UPDATE {tn} SET spectral = 1 "
                    "WHERE staged_dir = \"{gd}\"".format(tn=tn, gd=gd))
                c.execute(
                    "UPDATE {tn} SET spectral_date = {td} "
                    "WHERE staged_dir = \"{gd}\"".format(
                        tn=tn, td=today, gd=gd))
                c.execute(
                    "UPDATE {tn} SET spectral_dir = \"{sd}\" "
                    "WHERE staged_dir = \"{gd}\"".format(
                        tn=tn, sd=out_dir, gd=gd))
                c.execute(
                    "UPDATE {tn} SET spectral_files = \"{fs}\" "
                    "WHERE staged_dir = \"{gd}\"".format(
                        tn=tn, fs=files_csv, gd=gd))
            conn.commit()
            conn.close()
            db.shout(f'{glider_tag}: spectral OK on '
                     f'{success_count}/{len(stations)} stations',
                     logging=logging, verbose=True)
        else:
            db.shout(f'{glider_tag}: spectral failed for all stations',
                     logging=logging, verbose=True)
#--EOF
