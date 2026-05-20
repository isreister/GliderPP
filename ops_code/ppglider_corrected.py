#!/usr/bin/env python
'''
Purpose:    Apply CHL and Ed scaling factors from the spectral stage to the
            per-station chl/par/ed text files.

            For each station the spectral stage produced a `scale` file with
            two factors:
              - CHL_scale: per-profile chlorophyll correction (noisy, smoothed
                here using a configurable median-day window)
              - Ed_scale : per-profile broadband irradiance correction
                (applied as-is, not smoothed)

            Outputs:
              - chl_profile_*.corr        — chl values multiplied by smoothed
                                            CHL_scale
              - eds_profile_*.txt         — time-nearest single-timestep
                                            subset of the spectral ed file
              - eds_profile_*.corr        — eds values multiplied by Ed_scale

            Ported from operational_code/apply_Chl_Ed_corrections.py
            (commit aa5ddf5, Ben Loveday, 2018), adapted to the current
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
import sys
import warnings

import numpy as np

import tools.database_tools as db

#-messages----------------------------------------------------------------------
print('RUNNING: WARNINGS ARE SUPPRESSED')
warnings.filterwarnings('ignore')

#-default parameters------------------------------------------------------------
OUT_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
DEFAULT_LOG_PATH = os.path.join(OUT_ROOT, 'logs')
DEFAULT_CFG_DIR = os.path.join(OUT_ROOT, 'configs')
DEFAULT_CFG_FILE = os.path.join(DEFAULT_CFG_DIR, 'config_main.ini')


def parse_kv_file(path):
    '''Read a 'key value' text file (telemetry, scale, etc.).'''
    out = {}
    with open(path) as fh:
        for line in fh:
            parts = line.strip().split()
            if len(parts) >= 2:
                out[parts[0]] = parts[1]
    return out


def collect_stations(spectral_dir, suffix='_xing.txt'):
    '''Find every scale_station_NNNNNN<suffix> in spectral_dir, return a
    sorted list of (station_id, full_scale_path).'''
    pattern = os.path.join(spectral_dir, f'scale_station_*{suffix}')
    stations = []
    for f in sorted(glob.glob(pattern)):
        base = os.path.basename(f)
        # base = 'scale_station_NNNNNN<suffix>'
        after = base[len('scale_station_'):]
        station_id = after[:6]
        stations.append((station_id, f))
    return stations


def smooth_chl_scale(ord_dates, chl_scaling, window_days):
    '''Median-window smoothing of CHL_scale across nearby profiles in time,
    excluding stations where CHL_scale was pinned to 1.0 (the bad-PAR
    fallback). Returns smoothed array + per-window std.'''
    chl_smooth = np.full(len(chl_scaling), np.nan)
    chl_std = np.full(len(chl_scaling), np.nan)
    for i in range(len(chl_scaling)):
        lo = ord_dates[i] - window_days / 2
        hi = ord_dates[i] + window_days / 2
        in_scope = np.where((ord_dates >= lo) & (ord_dates <= hi))[0]
        good = chl_scaling[in_scope]
        good = good[good != 1.0]
        if len(good) > 0:
            chl_smooth[i] = float(np.mean(good))
            chl_std[i] = float(np.std(good))
        else:
            chl_smooth[i] = 1.0
            chl_std[i] = 0.0
    return chl_smooth, chl_std


def write_corrected_chl(chl_in, chl_out, scale):
    '''Read chl text rows ("HH:MM depth chl") and write rows with chl scaled.'''
    if os.path.exists(chl_out):
        os.chmod(chl_out, 0o777)
        os.remove(chl_out)
    with open(chl_in) as in_f, open(chl_out, 'w') as out_f:
        for line in in_f:
            parts = line.split(' ')
            if len(parts) < 3:
                out_f.write(line)
                continue
            try:
                scaled = float(parts[-1]) * scale
            except ValueError:
                out_f.write(line)
                continue
            out_f.write(f'{parts[0]} {parts[1]} {scaled}\n')
    os.chmod(chl_out, 0o777)


def write_subset_ed(ed_file, eds_file, glider_time, is_day):
    '''Subset the multi-time/wavelength ed file to the timestep nearest
    `glider_time`. Zero-out values when is_day == 0.'''
    rows = np.genfromtxt(ed_file, dtype=('|S10', float, float, float))
    times = np.array([r[0].decode('utf-8') for r in rows])
    wv = np.array([r[1] for r in rows])
    ed = np.array([r[2] for r in rows])
    mu0 = np.array([r[3] for r in rows])

    hh, mm = glider_time.split(':')
    t_glider = datetime.datetime(2000, 1, 1, int(hh), int(mm))
    t_off = np.array([
        abs((datetime.datetime(2000, 1, 1, int(t.split(':')[0]),
                                int(t.split(':')[1])) - t_glider).total_seconds())
        for t in times
    ])
    sel = np.where(t_off == np.nanmin(t_off))[0]

    wv_sel = wv[sel]
    mu0_sel = mu0[sel]
    times_sel = times[sel]
    if float(is_day) == 0.0:
        ed_sel = ed[sel] * 0.0
    else:
        ed_sel = ed[sel]

    if os.path.exists(eds_file):
        os.chmod(eds_file, 0o777)
        os.remove(eds_file)

    with open(eds_file, 'w') as fh:
        for i in range(len(mu0_sel)):
            line = f'{times_sel[i]}\t{int(wv_sel[i])}\t{ed_sel[i]}\t{mu0_sel[i]}'
            fh.write(line + ('\n' if i < len(mu0_sel) - 1 else ''))
    os.chmod(eds_file, 0o777)


def write_corrected_ed(eds_in, eds_out, scale):
    '''Apply Ed_scale to each row of an eds file.'''
    if os.path.exists(eds_out):
        os.chmod(eds_out, 0o777)
        os.remove(eds_out)
    with open(eds_in) as in_f, open(eds_out, 'w') as out_f:
        for line in in_f:
            parts = line.rstrip('\n').split('\t')
            if len(parts) < 4:
                out_f.write(line if line.endswith('\n') else line + '\n')
                continue
            try:
                scaled = float(parts[2]) * scale
            except ValueError:
                out_f.write(line if line.endswith('\n') else line + '\n')
                continue
            out_f.write(f'{parts[0]}\t{parts[1]}\t{scaled}\t{parts[3]}\n')
    os.chmod(eds_out, 0o777)


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
                    help='comma-separated whitelist of glider tags')
PARSER.add_argument('--no_chl_correction', action='store_true',
                    help='skip the smoothed CHL correction (force CHL_scale=1)')
ARGS = PARSER.parse_args()

#-main--------------------------------------------------------------------------
if __name__ == "__main__":
    verbose = ARGS.verbose
    allowed = [g for g in ARGS.allowed_gliders.split(',') if g]

    if not os.path.exists(os.path.abspath(ARGS.log_path)):
        os.makedirs(ARGS.log_path)
    LOGFILE = os.path.join(
        ARGS.log_path,
        'PPglider_corrected_' +
        datetime.datetime.now().strftime('%Y%m%d_%H%M') + '.log')
    if os.path.exists(LOGFILE):
        os.remove(LOGFILE)
    print('logging to: ' + LOGFILE)
    logging.basicConfig(filename=LOGFILE, level=logging.DEBUG)

    module_config = configparser.ConfigParser(allow_no_value=True,
                                              interpolation=configparser.ExtendedInterpolation())
    module_config.read(ARGS.config_file)

    database_name = os.path.join(
        os.path.abspath(module_config['DIRECTORIES']['database_dir']),
        module_config['DATABASE']['database_name'])
    spectral_root = os.path.abspath(module_config['SPECTRAL']['spectral_dir'])
    preproc_root = os.path.abspath(module_config['EO_ACQUIRE']['preproc_dir'])
    corrected_root = os.path.abspath(module_config['CORRECTED']['corrected_dir'])
    smooth_window = int(module_config['CORRECTED']['chl_smooth_window_days'])

    if not os.path.exists(corrected_root):
        os.makedirs(corrected_root)
        os.chmod(corrected_root, 0o777)

    all_keys = list(module_config['DATABASE_columns'].keys())
    nitems, db_dict = db.get_status(
        database_name, module_config['DATABASE']['table_name'],
        all_keys, logging=logging, verbose=verbose)

    glider_tags = [str(p) + '_' + str(n) + '_' + str(nm)
                   for p, n, nm in zip(db_dict['glider_prefix'],
                                       db_dict['glider_number'],
                                       db_dict['glider_name'])]
    is_spectral = np.asarray(db_dict['spectral']).astype(int)

    seen = set()
    for item in range(nitems):
        glider_tag = glider_tags[item]
        if glider_tag in seen:
            continue
        seen.add(glider_tag)

        if allowed and glider_tag not in allowed:
            continue
        if is_spectral[item] != 1:
            db.shout(f'{glider_tag}: spectral not done; skipping corrected',
                     logging=logging, verbose=verbose)
            continue

        spectral_dir = os.path.join(spectral_root, glider_tag)
        pp_dir = os.path.join(preproc_root, 'pp', glider_tag)
        out_dir = os.path.join(corrected_root, glider_tag)
        if not os.path.isdir(spectral_dir):
            db.shout(f'{glider_tag}: spectral dir missing: {spectral_dir}',
                     logging=logging, verbose=True)
            continue
        if not os.path.isdir(pp_dir):
            db.shout(f'{glider_tag}: preproc text dir missing: {pp_dir}',
                     logging=logging, verbose=True)
            continue
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
            os.chmod(out_dir, 0o777)

        # Discover stations + suffix from the scale files
        scale_files = sorted(glob.glob(
            os.path.join(spectral_dir, 'scale_station_*')))
        if not scale_files:
            db.shout(f'{glider_tag}: no scale files in {spectral_dir}',
                     logging=logging, verbose=True)
            continue

        # All scale files in a glider dir share the same suffix
        sample = os.path.basename(scale_files[0])
        suffix = sample[len('scale_station_') + 6:]

        n = len(scale_files)
        chl_scaling = np.full(n, np.nan)
        ed_scaling = np.full(n, np.nan)
        ord_dates = np.full(n, np.nan)
        station_ids = []

        for i, sf in enumerate(scale_files):
            base = os.path.basename(sf)
            sid = base[len('scale_station_'):][:6]
            station_ids.append(sid)

            sd = parse_kv_file(sf)
            chl_scaling[i] = float(sd.get('CHL_scale', 'nan'))
            ed_scaling[i] = float(sd.get('Ed_scale', 'nan'))

            # use telemetry from the preproc text dir
            telem = os.path.join(pp_dir, f'telemetry_station_{sid}{suffix}')
            if not os.path.exists(telem):
                continue
            td = parse_kv_file(telem)
            try:
                ord_dates[i] = float(datetime.datetime.strptime(
                    td['jday'] + td['year'], '%j%Y').toordinal())
            except (KeyError, ValueError):
                pass

        good_dates = np.isfinite(ord_dates)
        if not np.any(good_dates):
            db.shout(f'{glider_tag}: no valid jday/year in telemetry',
                     logging=logging, verbose=True)
            continue

        chl_smooth, chl_std = smooth_chl_scale(
            ord_dates, chl_scaling, smooth_window)
        if ARGS.no_chl_correction:
            chl_smooth[:] = 1.0
        # NaNs in the smoothed series default to 1.0 (no correction)
        chl_smooth = np.nan_to_num(chl_smooth, nan=1.0)
        ed_scaling_filled = np.nan_to_num(ed_scaling, nan=1.0)

        produced = []
        success_count = 0
        for i, sid in enumerate(station_ids):
            chl_in = os.path.join(pp_dir, f'chl_profile_station_{sid}{suffix}')
            chl_out = os.path.join(out_dir, f'chl_profile_station_{sid}{suffix}'
                                   .replace('.txt', '.corr'))
            ed_in = os.path.join(spectral_dir, f'ed_station_{sid}{suffix}')
            eds_out = os.path.join(out_dir,
                                   f'eds_station_{sid}{suffix}')
            eds_corr = os.path.join(out_dir,
                                    f'eds_station_{sid}{suffix}'
                                    .replace('.txt', '.corr'))

            telem = os.path.join(pp_dir, f'telemetry_station_{sid}{suffix}')
            if not (os.path.exists(chl_in) and os.path.exists(ed_in)
                    and os.path.exists(telem)):
                continue
            td = parse_kv_file(telem)

            try:
                write_corrected_chl(chl_in, chl_out, chl_smooth[i])
                write_subset_ed(ed_in, eds_out,
                                td.get('time', '12:00'),
                                td.get('is_day', '0'))
                write_corrected_ed(eds_out, eds_corr, ed_scaling_filled[i])
                produced.extend([chl_out, eds_out, eds_corr])
                success_count += 1
            except Exception as e:
                if logging is not None:
                    logging.exception('correction failed for station %s: %s',
                                      sid, e)

            if verbose and (i + 1) % 1000 == 0:
                print(f'  {i + 1}/{n} stations corrected')

        db.shout(f'{glider_tag}: corrected '
                 f'{success_count}/{n} stations',
                 logging=logging, verbose=True)

        # DB update
        if success_count > 0:
            today = "'" + datetime.datetime.now().strftime('%Y%m%d_%H%M') + "'"
            files_csv = ','.join(sorted(produced))
            tn = module_config['DATABASE']['table_name']
            conn, c = db.connectDB(database_name)
            for di in np.where(np.array(glider_tags) == glider_tag)[0]:
                gd = str(db_dict['staged_dir'][di])
                c.execute(f"UPDATE {tn} SET corrected = 1 "
                          f"WHERE staged_dir = \"{gd}\"")
                c.execute(f"UPDATE {tn} SET corrected_date = {today} "
                          f"WHERE staged_dir = \"{gd}\"")
                c.execute(f"UPDATE {tn} SET corrected_dir = \"{out_dir}\" "
                          f"WHERE staged_dir = \"{gd}\"")
                c.execute(f"UPDATE {tn} SET corrected_files = \"{files_csv}\" "
                          f"WHERE staged_dir = \"{gd}\"")
            conn.commit()
            conn.close()
#--EOF
