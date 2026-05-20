#!/usr/bin/env python
'''
Purpose:    Run the precompiled Morel91 PP model per station, using the
            corrected chl + eds inputs from the corrected stage. Produces
            depth-resolved primary productivity profiles.

            Three runs per station are emitted, mirroring STAGE 6 of the
            historical operational_code/Process_PP_gliders.run:
              - pp_uncorr  : uncorrected chl + uncorrected eds   (.txt)
              - pp_corr    : corrected   chl + corrected   eds   (.corr)
              - pp_split   : uncorrected chl + corrected   eds   (.split)

            The "split" run isolates the contribution of the Ed correction
            alone vs the full corrected pipeline.

            Author of the underlying physics: Morel, A. (1991), Light and
            marine photosynthesis: a spectral model with geochemical and
            climatological implications, Prog. Oceanogr. 26, 263–306.

License:    See LICENCE.txt. The morel91 binary itself is in models/, which
            per README.md is NOT redistributable.
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
    out = {}
    with open(path) as fh:
        for line in fh:
            parts = line.strip().split()
            if len(parts) >= 2:
                out[parts[0]] = parts[1]
    return out


def run_morel91(binary, lib_dir, kc, kw, aw, bw, Achl, max_depth,
                euphotic_ratio, phi_mu_max,
                chl_file, ed_file, temp, profile_out, logging=None):
    '''Invoke morel91 with the args from STAGE 6 of Process_PP_gliders.run.'''
    env = os.environ.copy()
    env['LD_LIBRARY_PATH'] = lib_dir + ':' + env.get('LD_LIBRARY_PATH', '')

    cmd = [
        binary,
        '--chl_read', chl_file,
        '--T', str(temp),
        '--max_depth', str(max_depth),
        '--euphotic_ratio', str(euphotic_ratio),
        '--kc_read', kc,
        '--kw_read', kw,
        '--aw_read', aw,
        '--bw_read', bw,
        '--Achl_read', Achl,
        '--phi_mu_max', str(phi_mu_max),
        '--ed_read', ed_file,
        '--profile_write', profile_out,
    ]

    if os.path.exists(profile_out):
        os.remove(profile_out)

    proc = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if proc.returncode != 0:
        if logging is not None:
            logging.error('morel91 failed (rc=%d) for %s: %s',
                          proc.returncode, profile_out, proc.stderr)
        raise RuntimeError(
            f'morel91 returned {proc.returncode}: {proc.stderr.strip()}')
    return profile_out


#-arguments---------------------------------------------------------------------
PARSER = argparse.ArgumentParser()
PARSER.add_argument('-cfg', '--config_file', type=str,
                    default=DEFAULT_CFG_FILE,
                    help='Config file')
PARSER.add_argument('-v', '--verbose', action='store_true')
PARSER.add_argument('-l', '--log_path', type=str,
                    default=DEFAULT_LOG_PATH)
PARSER.add_argument('-ag', '--allowed_gliders', type=str, default='')
PARSER.add_argument('--no_uncorr', action='store_true',
                    help='skip the uncorrected pp run')
PARSER.add_argument('--no_corr', action='store_true',
                    help='skip the fully-corrected pp run')
PARSER.add_argument('--no_split', action='store_true',
                    help='skip the chl-only/Ed-corrected split pp run')
ARGS = PARSER.parse_args()

#-main--------------------------------------------------------------------------
if __name__ == "__main__":
    verbose = ARGS.verbose
    allowed = [g for g in ARGS.allowed_gliders.split(',') if g]

    if not os.path.exists(os.path.abspath(ARGS.log_path)):
        os.makedirs(ARGS.log_path)
    LOGFILE = os.path.join(
        ARGS.log_path,
        'PPglider_primary_prod_' +
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
    corrected_root = os.path.abspath(cfg['CORRECTED']['corrected_dir'])
    pp_root = os.path.abspath(cfg['PRIMARY_PROD']['primary_prod_dir'])

    morel91 = cfg['PRIMARY_PROD']['morel91_binary']
    lib_dir = cfg['PRIMARY_PROD']['morel91_lib_dir']
    kc = cfg['PRIMARY_PROD']['kc_data']
    kw = cfg['PRIMARY_PROD']['kw_data']
    aw = cfg['PRIMARY_PROD']['aw_data']
    bw = cfg['PRIMARY_PROD']['bw_data']
    Achl = cfg['PRIMARY_PROD']['Achl_data']
    max_depth = cfg['PRIMARY_PROD']['max_depth']
    euphotic_ratio = cfg['PRIMARY_PROD']['euphotic_ratio']
    phi_mu_max = cfg['PRIMARY_PROD']['phi_mu_max']

    for path in (morel91, kc, kw, aw, bw, Achl):
        if not os.path.exists(path):
            db.shout(f'required file missing: {path}',
                     logging=logging, verbose=True)
            sys.exit(1)

    if not os.path.exists(pp_root):
        os.makedirs(pp_root)
        os.chmod(pp_root, 0o777)

    all_keys = list(cfg['DATABASE_columns'].keys())
    nitems, db_dict = db.get_status(
        database_name, cfg['DATABASE']['table_name'],
        all_keys, logging=logging, verbose=verbose)

    glider_tags = [str(p) + '_' + str(n) + '_' + str(nm)
                   for p, n, nm in zip(db_dict['glider_prefix'],
                                       db_dict['glider_number'],
                                       db_dict['glider_name'])]
    is_corrected = np.asarray(db_dict['corrected']).astype(int)

    seen = set()
    for item in range(nitems):
        glider_tag = glider_tags[item]
        if glider_tag in seen:
            continue
        seen.add(glider_tag)

        if allowed and glider_tag not in allowed:
            continue
        if is_corrected[item] != 1:
            db.shout(f'{glider_tag}: corrected not done; skipping pp',
                     logging=logging, verbose=verbose)
            continue

        pp_dir = os.path.join(preproc_root, 'pp', glider_tag)
        spectral_dir = os.path.join(spectral_root, glider_tag)
        corrected_dir = os.path.join(corrected_root, glider_tag)
        out_dir = os.path.join(pp_root, glider_tag)
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
            os.chmod(out_dir, 0o777)

        # Discover stations from corrected eds files
        eds_uncorr_files = sorted(glob.glob(
            os.path.join(corrected_dir, 'eds_station_*.txt')))
        if not eds_uncorr_files:
            db.shout(f'{glider_tag}: no eds files in {corrected_dir}',
                     logging=logging, verbose=True)
            continue

        # Suffix discovery (strip 'eds_station_NNNNNN' prefix)
        sample = os.path.basename(eds_uncorr_files[0])
        suffix = sample[len('eds_station_') + 6:]

        produced = []
        success_count = 0
        for i, eds_uncorr in enumerate(eds_uncorr_files):
            sid = os.path.basename(eds_uncorr)[len('eds_station_'):][:6]

            chl_uncorr = os.path.join(
                pp_dir, f'chl_profile_station_{sid}{suffix}')
            chl_corr = os.path.join(
                corrected_dir,
                f'chl_profile_station_{sid}{suffix}'.replace('.txt', '.corr'))
            eds_corr = eds_uncorr.replace('.txt', '.corr')
            telem = os.path.join(pp_dir, f'telemetry_station_{sid}{suffix}')

            if not (os.path.exists(chl_uncorr) and os.path.exists(chl_corr)
                    and os.path.exists(eds_corr) and os.path.exists(telem)):
                continue

            td = parse_kv_file(telem)
            temp = float(td.get('temp', 'nan'))
            if not np.isfinite(temp):
                continue

            pp_uncorr = os.path.join(out_dir,
                                     f'pp_station_{sid}{suffix}')
            pp_corr = os.path.join(out_dir,
                                   f'pp_station_{sid}{suffix}'
                                   .replace('.txt', '.corr'))
            pp_split = os.path.join(out_dir,
                                    f'pp_station_{sid}{suffix}'
                                    .replace('.txt', '.split'))

            try:
                if not ARGS.no_uncorr:
                    run_morel91(morel91, lib_dir, kc, kw, aw, bw, Achl,
                                max_depth, euphotic_ratio, phi_mu_max,
                                chl_uncorr, eds_uncorr, temp, pp_uncorr,
                                logging=logging)
                    produced.append(pp_uncorr)
                if not ARGS.no_corr:
                    run_morel91(morel91, lib_dir, kc, kw, aw, bw, Achl,
                                max_depth, euphotic_ratio, phi_mu_max,
                                chl_corr, eds_corr, temp, pp_corr,
                                logging=logging)
                    produced.append(pp_corr)
                if not ARGS.no_split:
                    run_morel91(morel91, lib_dir, kc, kw, aw, bw, Achl,
                                max_depth, euphotic_ratio, phi_mu_max,
                                chl_uncorr, eds_corr, temp, pp_split,
                                logging=logging)
                    produced.append(pp_split)
                success_count += 1
            except Exception as e:
                if logging is not None:
                    logging.exception('morel91 failed for station %s: %s',
                                      sid, e)

            if verbose and (i + 1) % 500 == 0:
                print(f'  {i + 1}/{len(eds_uncorr_files)} stations done')

        db.shout(f'{glider_tag}: pp on '
                 f'{success_count}/{len(eds_uncorr_files)} stations',
                 logging=logging, verbose=True)

        if success_count > 0:
            today = "'" + datetime.datetime.now().strftime('%Y%m%d_%H%M') + "'"
            files_csv = ','.join(sorted(produced))
            tn = cfg['DATABASE']['table_name']
            conn, c = db.connectDB(database_name)
            for di in np.where(np.array(glider_tags) == glider_tag)[0]:
                gd = str(db_dict['staged_dir'][di])
                c.execute(f"UPDATE {tn} SET primary_prod = 1 "
                          f"WHERE staged_dir = \"{gd}\"")
                c.execute(f"UPDATE {tn} SET primary_prod_date = {today} "
                          f"WHERE staged_dir = \"{gd}\"")
                c.execute(f"UPDATE {tn} SET primary_prod_dir = \"{out_dir}\" "
                          f"WHERE staged_dir = \"{gd}\"")
                c.execute(f"UPDATE {tn} SET primary_prod_files = \"{files_csv}\" "
                          f"WHERE staged_dir = \"{gd}\"")
            conn.commit()
            conn.close()
#--EOF
