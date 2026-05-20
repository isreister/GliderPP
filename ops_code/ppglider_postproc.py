#!/usr/bin/env python
'''
Purpose:    Aggregate per-station primary-productivity outputs from the
            primary_prod stage into a mission-level NetCDF.

            For each profile we collect:
              - Depth-resolved Morel91 outputs (PP, Chl, PAR, etc.) on a
                shared depth grid (interpolated to 1-m bins from min_depth
                to max_depth).
              - Column-integrated PP (trapezoidal across depth) for the
                three Morel91 runs (uncorrected, corrected, split).
              - Per-profile metadata from the preproc telemetry file:
                TIME, LAT, LON, temp, MLD, ZEU, CHL_traj, ZEU_traj.
              - The smoothed CHL_scale and Ed_scale that were applied.

            Note: this driver was written from scratch — the historical
            Process_PP_gliders.run STAGE 7 referenced a
            postprocess_gliders.py file that was never committed (the bash
            script even exits before STAGE 7). Output structure here is
            designed to be a sensible default; refine as analysis needs
            evolve.

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
from netCDF4 import Dataset

import tools.database_tools as db

#-messages----------------------------------------------------------------------
print('RUNNING: WARNINGS ARE SUPPRESSED')
warnings.filterwarnings('ignore')

#-default parameters------------------------------------------------------------
OUT_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
DEFAULT_LOG_PATH = os.path.join(OUT_ROOT, 'logs')
DEFAULT_CFG_DIR = os.path.join(OUT_ROOT, 'configs')
DEFAULT_CFG_FILE = os.path.join(DEFAULT_CFG_DIR, 'config_main.ini')

# Column layout produced by morel91 --profile_write (see
# models/morel91/morel91_calculate.cc:427).
PP_COLUMNS = ['Z', 'PP', 'Achl_max', 'Chl', 'Phi_mu_max', 'PUR_total',
              'PAR_einsteins', 'PAR_watts', 'Ed_400nm', 'Beta', 'KPUR']

# Standard 1-m depth grid for aggregation (matches max_depth in PRIMARY_PROD).
DEPTH_GRID = np.arange(0, 101, 1).astype(np.int32)


def parse_kv_file(path):
    out = {}
    with open(path) as fh:
        for line in fh:
            parts = line.strip().split()
            if len(parts) >= 2:
                out[parts[0]] = parts[1]
    return out


def read_pp_file(path):
    '''Parse a morel91 profile_write output. Returns a dict
    column_name -> 1-D array, or None if the file is empty/unreadable.'''
    try:
        rows = np.genfromtxt(path, skip_header=1, dtype=float)
    except Exception:
        return None
    if rows.size == 0:
        return None
    rows = np.atleast_2d(rows)
    if rows.shape[1] < len(PP_COLUMNS):
        return None
    return {name: rows[:, i] for i, name in enumerate(PP_COLUMNS)}


def interpolate_to_grid(z, values, grid):
    '''Interpolate `values` defined at integer depths `z` onto `grid`.
    Out-of-range points become NaN.'''
    out = np.full(len(grid), np.nan)
    if len(z) == 0:
        return out
    sort = np.argsort(z)
    zs = z[sort]
    vs = values[sort]
    in_range = (grid >= zs.min()) & (grid <= zs.max())
    out[in_range] = np.interp(grid[in_range], zs, vs)
    return out


def column_integrate(z, pp):
    '''Trapezoidal depth-integration of PP. NaN-safe.'''
    z = np.asarray(z, dtype=float)
    pp = np.asarray(pp, dtype=float)
    good = np.isfinite(z) & np.isfinite(pp)
    if good.sum() < 2:
        return np.nan
    return float(np.trapz(pp[good], z[good]))


def parse_glider_time(year_str, jday_str, hhmm_str):
    '''Combine year+jday+HH:MM into a UTC datetime.'''
    try:
        d = datetime.datetime.strptime(year_str + jday_str, '%Y%j')
        hh, mm = hhmm_str.split(':')
        return d.replace(hour=int(hh), minute=int(mm))
    except (ValueError, KeyError):
        return None


def collect_station_data(pp_dir, primary_prod_dir, spectral_dir, suffix,
                         logging=None):
    '''Walk the per-station files and return a dict of arrays ready for
    NetCDF write. Stations missing required pieces are skipped.'''

    pp_files = sorted(glob.glob(os.path.join(primary_prod_dir,
                                             f'pp_station_*{suffix}')))
    if not pp_files:
        return None

    station_ids = []
    times = []
    lats = []
    lons = []
    temps = []
    mlds = []
    zeus = []
    chl_trajs = []
    zeu_trajs = []
    chl_scales = []
    ed_scales = []
    is_days = []

    pp_uncorr_grid = []
    pp_corr_grid = []
    pp_split_grid = []
    chl_grid = []
    par_einsteins_grid = []
    par_watts_grid = []

    pp_int_uncorr = []
    pp_int_corr = []
    pp_int_split = []

    for pp_uncorr_file in pp_files:
        sid = os.path.basename(pp_uncorr_file)[len('pp_station_'):][:6]
        pp_corr_file = pp_uncorr_file.replace('.txt', '.corr')
        pp_split_file = pp_uncorr_file.replace('.txt', '.split')
        telem_file = os.path.join(pp_dir, f'telemetry_station_{sid}{suffix}')
        scale_file = os.path.join(spectral_dir,
                                  f'scale_station_{sid}{suffix}')

        if not os.path.exists(telem_file):
            continue

        td = parse_kv_file(telem_file)
        gt_dt = parse_glider_time(td.get('year', ''), td.get('jday', ''),
                                  td.get('time', '12:00'))

        u = read_pp_file(pp_uncorr_file)
        c = read_pp_file(pp_corr_file) if os.path.exists(pp_corr_file) else None
        s = read_pp_file(pp_split_file) if os.path.exists(pp_split_file) else None
        if u is None and c is None and s is None:
            continue

        # Anchor the grids on whichever run is available
        anchor = u or c or s
        z = anchor['Z']
        chl_grid.append(interpolate_to_grid(z, anchor['Chl'], DEPTH_GRID))
        par_einsteins_grid.append(
            interpolate_to_grid(z, anchor['PAR_einsteins'], DEPTH_GRID))
        par_watts_grid.append(
            interpolate_to_grid(z, anchor['PAR_watts'], DEPTH_GRID))

        pp_uncorr_grid.append(
            interpolate_to_grid(z, u['PP'], DEPTH_GRID) if u is not None
            else np.full(len(DEPTH_GRID), np.nan))
        pp_corr_grid.append(
            interpolate_to_grid(c['Z'], c['PP'], DEPTH_GRID) if c is not None
            else np.full(len(DEPTH_GRID), np.nan))
        pp_split_grid.append(
            interpolate_to_grid(s['Z'], s['PP'], DEPTH_GRID) if s is not None
            else np.full(len(DEPTH_GRID), np.nan))

        pp_int_uncorr.append(
            column_integrate(u['Z'], u['PP']) if u is not None else np.nan)
        pp_int_corr.append(
            column_integrate(c['Z'], c['PP']) if c is not None else np.nan)
        pp_int_split.append(
            column_integrate(s['Z'], s['PP']) if s is not None else np.nan)

        # Per-profile metadata
        station_ids.append(int(sid))
        times.append(gt_dt.timestamp() if gt_dt else np.nan)
        try:
            lats.append(float(td['latitude']))
            lons.append(float(td['longitude']))
        except (KeyError, ValueError):
            lats.append(np.nan)
            lons.append(np.nan)
        temps.append(float(td.get('temp', 'nan')))
        mlds.append(float(td.get('MLD', 'nan')))
        zeus.append(float(td.get('ZEU', 'nan')))
        chl_trajs.append(float(td.get('CHL_traj', 'nan')))
        zeu_trajs.append(float(td.get('ZEU_traj', 'nan')))
        is_days.append(float(td.get('is_day', 'nan')))

        if os.path.exists(scale_file):
            sd = parse_kv_file(scale_file)
            chl_scales.append(float(sd.get('CHL_scale', 'nan')))
            ed_scales.append(float(sd.get('Ed_scale', 'nan')))
        else:
            chl_scales.append(np.nan)
            ed_scales.append(np.nan)

    if not station_ids:
        return None

    return {
        'station_id': np.array(station_ids, dtype=np.int32),
        'time': np.array(times, dtype=np.float64),
        'latitude': np.array(lats, dtype=np.float64),
        'longitude': np.array(lons, dtype=np.float64),
        'temperature': np.array(temps, dtype=np.float64),
        'mld': np.array(mlds, dtype=np.float64),
        'zeu': np.array(zeus, dtype=np.float64),
        'chl_traj': np.array(chl_trajs, dtype=np.float64),
        'zeu_traj': np.array(zeu_trajs, dtype=np.float64),
        'is_day': np.array(is_days, dtype=np.float64),
        'chl_scale': np.array(chl_scales, dtype=np.float64),
        'ed_scale': np.array(ed_scales, dtype=np.float64),
        'pp_int_uncorr': np.array(pp_int_uncorr, dtype=np.float64),
        'pp_int_corr': np.array(pp_int_corr, dtype=np.float64),
        'pp_int_split': np.array(pp_int_split, dtype=np.float64),
        'pp_profile_uncorr': np.vstack(pp_uncorr_grid),
        'pp_profile_corr': np.vstack(pp_corr_grid),
        'pp_profile_split': np.vstack(pp_split_grid),
        'chl_profile': np.vstack(chl_grid),
        'par_einsteins_profile': np.vstack(par_einsteins_grid),
        'par_watts_profile': np.vstack(par_watts_grid),
    }


def write_mission_netcdf(out_file, data, glider_tag, suffix):
    '''Build the per-mission NetCDF.'''
    if os.path.exists(out_file):
        os.remove(out_file)

    n_profiles = len(data['station_id'])
    n_depth = len(DEPTH_GRID)

    with Dataset(out_file, 'w', format='NETCDF4') as nc:
        nc.title = f'Glider primary productivity — {glider_tag}'
        nc.source = ('GliderPP pipeline (init_db -> staging -> acquire_eo -> '
                     'preproc -> spectral -> corrected -> primary_prod -> '
                     'postproc)')
        nc.glider_tag = glider_tag
        nc.processing_date = datetime.datetime.utcnow().isoformat() + 'Z'
        nc.suffix = suffix
        nc.institution = 'Plymouth Marine Laboratory'

        nc.createDimension('profile', n_profiles)
        nc.createDimension('depth', n_depth)

        depth_v = nc.createVariable('depth', 'i4', ('depth',))
        depth_v[:] = DEPTH_GRID
        depth_v.units = 'm'
        depth_v.long_name = 'depth (positive down)'

        # 1-D per-profile variables
        defs_1d = [
            ('station_id', 'i4', 'station identifier (sequential)', '1'),
            ('time', 'f8', 'profile time (UTC)', 'seconds since 1970-01-01'),
            ('latitude', 'f8', 'profile latitude', 'degrees_north'),
            ('longitude', 'f8', 'profile longitude', 'degrees_east'),
            ('temperature', 'f8', 'sea surface temperature', 'degC'),
            ('mld', 'f8', 'mixed layer depth (preproc)', 'm'),
            ('zeu', 'f8', 'euphotic depth (preproc)', 'm'),
            ('chl_traj', 'f8', 'satellite-derived CHL on glider track', 'mg m-3'),
            ('zeu_traj', 'f8', 'satellite-derived ZEU on glider track', 'm'),
            ('is_day', 'f8', '1 if profile is daytime, else 0', '1'),
            ('chl_scale', 'f8', 'per-profile CHL_scale from spectral', '1'),
            ('ed_scale', 'f8', 'per-profile Ed_scale from spectral', '1'),
            ('pp_int_uncorr', 'f8',
             'depth-integrated PP (uncorrected chl, uncorrected Ed)',
             'mg C m-2 day-1'),
            ('pp_int_corr', 'f8',
             'depth-integrated PP (corrected chl, corrected Ed)',
             'mg C m-2 day-1'),
            ('pp_int_split', 'f8',
             'depth-integrated PP (uncorrected chl, corrected Ed)',
             'mg C m-2 day-1'),
        ]
        for name, dtype, long_name, units in defs_1d:
            kwargs = {'fill_value': np.nan} if dtype.startswith('f') else {}
            v = nc.createVariable(name, dtype, ('profile',), **kwargs)
            v[:] = data[name]
            v.long_name = long_name
            v.units = units

        # 2-D depth-resolved variables
        defs_2d = [
            ('pp_profile_uncorr', 'PP profile (uncorrected)', 'mg C m-3 day-1'),
            ('pp_profile_corr', 'PP profile (corrected chl + corrected Ed)',
             'mg C m-3 day-1'),
            ('pp_profile_split', 'PP profile (uncorrected chl, corrected Ed)',
             'mg C m-3 day-1'),
            ('chl_profile', 'chlorophyll-a profile (Morel91 input)', 'mg m-3'),
            ('par_einsteins_profile', 'PAR profile (Morel91 output)',
             'uE m-2 s-1'),
            ('par_watts_profile', 'PAR profile (Morel91 output)', 'W m-2'),
        ]
        for name, long_name, units in defs_2d:
            v = nc.createVariable(name, 'f8', ('profile', 'depth'),
                                  fill_value=np.nan, zlib=True,
                                  complevel=4)
            v[:, :] = data[name]
            v.long_name = long_name
            v.units = units


#-arguments---------------------------------------------------------------------
PARSER = argparse.ArgumentParser()
PARSER.add_argument('-cfg', '--config_file', type=str,
                    default=DEFAULT_CFG_FILE)
PARSER.add_argument('-v', '--verbose', action='store_true')
PARSER.add_argument('-l', '--log_path', type=str,
                    default=DEFAULT_LOG_PATH)
PARSER.add_argument('-ag', '--allowed_gliders', type=str, default='')
ARGS = PARSER.parse_args()

#-main--------------------------------------------------------------------------
if __name__ == "__main__":
    verbose = ARGS.verbose
    allowed = [g for g in ARGS.allowed_gliders.split(',') if g]

    if not os.path.exists(os.path.abspath(ARGS.log_path)):
        os.makedirs(ARGS.log_path)
    LOGFILE = os.path.join(
        ARGS.log_path,
        'PPglider_postproc_' +
        datetime.datetime.now().strftime('%Y%m%d_%H%M') + '.log')
    if os.path.exists(LOGFILE):
        os.remove(LOGFILE)
    print('logging to: ' + LOGFILE)
    logging.basicConfig(filename=LOGFILE, level=logging.DEBUG)

    cfg = configparser.ConfigParser(allow_no_value=True,
                                    interpolation=configparser.ExtendedInterpolation())
    cfg.read(ARGS.config_file)

    database_name = os.path.join(
        os.path.abspath(cfg['DIRECTORIES']['database_dir']),
        cfg['DATABASE']['database_name'])
    preproc_root = os.path.abspath(cfg['EO_ACQUIRE']['preproc_dir'])
    spectral_root = os.path.abspath(cfg['SPECTRAL']['spectral_dir'])
    pp_root = os.path.abspath(cfg['PRIMARY_PROD']['primary_prod_dir'])
    postproc_root = os.path.abspath(cfg['POSTPROC']['postproc_dir'])

    if not os.path.exists(postproc_root):
        os.makedirs(postproc_root)
        os.chmod(postproc_root, 0o777)

    all_keys = list(cfg['DATABASE_columns'].keys())
    nitems, db_dict = db.get_status(
        database_name, cfg['DATABASE']['table_name'],
        all_keys, logging=logging, verbose=verbose)

    glider_tags = [str(p) + '_' + str(n) + '_' + str(nm)
                   for p, n, nm in zip(db_dict['glider_prefix'],
                                       db_dict['glider_number'],
                                       db_dict['glider_name'])]
    is_pp = np.asarray(db_dict['primary_prod']).astype(int)

    seen = set()
    for item in range(nitems):
        glider_tag = glider_tags[item]
        if glider_tag in seen:
            continue
        seen.add(glider_tag)

        if allowed and glider_tag not in allowed:
            continue
        if is_pp[item] != 1:
            db.shout(f'{glider_tag}: primary_prod not done; skipping postproc',
                     logging=logging, verbose=verbose)
            continue

        pp_dir = os.path.join(preproc_root, 'pp', glider_tag)
        spectral_dir = os.path.join(spectral_root, glider_tag)
        primary_prod_dir = os.path.join(pp_root, glider_tag)

        # Suffix discovery from any pp_station_* file
        candidates = sorted(glob.glob(
            os.path.join(primary_prod_dir, 'pp_station_*')))
        if not candidates:
            db.shout(f'{glider_tag}: no pp files in {primary_prod_dir}',
                     logging=logging, verbose=True)
            continue
        # Use the first .txt suffix
        suffix = None
        for cand in candidates:
            base = os.path.basename(cand)
            if base.endswith('.txt'):
                after = base[len('pp_station_'):]
                suffix = after[6:]
                break
        if suffix is None:
            db.shout(f'{glider_tag}: no .txt pp files in {primary_prod_dir}',
                     logging=logging, verbose=True)
            continue

        data = collect_station_data(pp_dir, primary_prod_dir, spectral_dir,
                                    suffix, logging=logging)
        if data is None:
            db.shout(f'{glider_tag}: collect_station_data returned nothing',
                     logging=logging, verbose=True)
            continue

        out_file = os.path.join(postproc_root, f'{glider_tag}_pp_mission.nc')
        write_mission_netcdf(out_file, data, glider_tag, suffix)
        db.shout(f'{glider_tag}: wrote {out_file} '
                 f'(profiles={len(data["station_id"])})',
                 logging=logging, verbose=True)

        today = "'" + datetime.datetime.now().strftime('%Y%m%d_%H%M') + "'"
        tn = cfg['DATABASE']['table_name']
        conn, c = db.connectDB(database_name)
        for di in np.where(np.array(glider_tags) == glider_tag)[0]:
            gd = str(db_dict['staged_dir'][di])
            c.execute(f"UPDATE {tn} SET postproc = 1 "
                      f"WHERE staged_dir = \"{gd}\"")
            c.execute(f"UPDATE {tn} SET postproc_date = {today} "
                      f"WHERE staged_dir = \"{gd}\"")
            c.execute(f"UPDATE {tn} SET postproc_dir = \"{postproc_root}\" "
                      f"WHERE staged_dir = \"{gd}\"")
            c.execute(f"UPDATE {tn} SET postproc_files = \"{out_file}\" "
                      f"WHERE staged_dir = \"{gd}\"")
        conn.commit()
        conn.close()
#--EOF
