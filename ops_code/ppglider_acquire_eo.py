#!/usr/bin/env python
'''
Purpose:    Build EO data cube to support glider missions

Version:    v1.0 10/2021

Author:     Ben Loveday, Plymouth Marine Laboratory
            Time Smyth, Plymouth Marine Laboratory

License:    See LICENCE.txt
'''
#-imports-----------------------------------------------------------------------
import argparse, os, sys, shutil, datetime, logging
import numpy as np
import fnmatch
import glob
import warnings
from netCDF4 import Dataset
import configparser

# add paths/tools
import tools.database_tools as db
import tools.glider_tools as gt
import tools.download_tools as dlt

#-messages----------------------------------------------------------------------
print('RUNNING: WARNINGS ARE SUPPRESSED')
warnings.filterwarnings('ignore')

#-default parameters------------------------------------------------------------
OUT_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
DEFAULT_LOG_PATH = os.path.join(OUT_ROOT, 'logs')
DEFAULT_PLT_PATH = os.path.join(OUT_ROOT, 'plots')
DEFAULT_CFG_DIR = os.path.join(OUT_ROOT, 'configs')
DEFAULT_CFG_FILE = os.path.join(DEFAULT_CFG_DIR, 'config_main.ini')

#-ARGS--------------------------------------------------------------------------

PARSER = argparse.ArgumentParser()
PARSER.add_argument('-cfg', '--config_file', type=str,\
                    default=DEFAULT_CFG_FILE,\
                    help='Config file')
PARSER.add_argument('-p', '--plot_dir', type=str,\
                    default=DEFAULT_PLT_PATH,\
                    help='Plot plotting directory')
PARSER.add_argument('-v', '--verbose',\
                    action='store_true')
PARSER.add_argument('-l', '--log_path', type=str,\
                    default=DEFAULT_LOG_PATH,\
                    help='log file output path')
ARGS = PARSER.parse_args()

#-main--------------------------------------------------------------------------
if __name__ == "__main__":

    verbose = ARGS.verbose
    skip_boundary = False
    nrecords = 50 # a rough estimate of max number of feasible new profiles per
                  # day; if we are missing more than this, do a total data cube
                  # recreation

    # preliminary stuff
    LOGFILE = os.path.join(ARGS.log_path,"PPglider_acquire_EO_"+\
              datetime.datetime.now().strftime('%Y%m%d_%H%M')+".log")

    # make required log directory if it does not exist
    if not os.path.exists(os.path.abspath(ARGS.log_path)):
        os.makedirs(ARGS.log_path)

    # set file logger
    try:
        if os.path.exists(LOGFILE):
            os.remove(LOGFILE)
        print("logging to: "+LOGFILE)
        logging.basicConfig(filename=LOGFILE, level=logging.DEBUG)
    except:
        print("Failed to set logger")
        sys.exit()

    # read processing config file
    module_config = configparser.ConfigParser(allow_no_value=True)
    module_config.read(ARGS.config_file)

    # set database names
    database_name = os.path.join(os.path.abspath(module_config['DIRECTORIES']['database_dir']),
      module_config['DATABASE']['database_name'])

    all_keys = [item for item in module_config['DATABASE_columns'].keys()]

    # get database statuses
    nitems, db_dict = db.get_status(database_name,
        module_config['DATABASE']['table_name'],all_keys,
        logging=logging, verbose=verbose)

    # convert database keys to integer arrays
    is_EO_int = np.asarray(db_dict["eo_acquire"]).astype(int)
    EO_statuses = db_dict["eo_acquire_state"]
    is_staged_int = np.asarray(db_dict["staged"]).astype(int)
    prefixes = np.asarray(db_dict["glider_prefix"]).astype(str)

    # get the glider directories
    variables = module_config['EO_ACQUIRE']['variables'].split(',')
   
    # keys of glider tag, not storage directory
    glider_tags = [str(m)+'_'+str(n)+'_'+str(p) \
                   for m,n,p in zip(db_dict["glider_prefix"],db_dict["glider_number"],db_dict["glider_name"])]

    glider_prefix_array = np.asarray(db_dict["glider_prefix"]).astype(str)
    glider_number_array = np.asarray(db_dict["glider_number"]).astype(str)

    # loop through glider directories
    for glider_tag in np.unique(glider_tags):

        if os.path.exists("./oceandata.sci.gsfc.nasa.gov/"):
            shutil.rmtree("./oceandata.sci.gsfc.nasa.gov/")

        # REMOVE
        if 'SCAPA' in glider_tag.upper() or 'OMG' in glider_tag.upper() or 'AMMONITE' in glider_tag.upper():
            continue

        GLIDER_CONFIG = os.path.join(DEFAULT_CFG_DIR,
            f"config_{glider_tag}.ini")

        if not os.path.exists(os.path.abspath(GLIDER_CONFIG)):
            print(f"Config {GLIDER_CONFIG} does not exist; please create it!!")
            continue

        match_tag = '*'+glider_tag.split('_')[0]+glider_tag.split('_')[1]+'*.nc'

        # find matching directory rows
        matching_dirs = np.asarray([i for i,x in enumerate(glider_tags)\
                                    if x == glider_tag]).astype(int)

        # select directories containing data for this glider 
        glider_tmp_dirs = np.unique([db_dict['staged_dir'][i] for i in matching_dirs])
        glider_dirs = [x for x in glider_tmp_dirs if x is not None]

        # check for boundary file
        EO_dir = os.path.join(os.path.abspath(module_config['DIRECTORIES']['eo_dir']), glider_tag)
        boundary_file = os.path.join(EO_dir, 'boundaries.txt')

        if not os.path.exists(EO_dir):
            if not os.path.exists(os.path.dirname(EO_dir)):
                os.makedirs(EO_dir)

        # check for trajectory file & make if required
        trajectory_file = os.path.join(EO_dir, glider_tag+'_trajectory.nc')

        if not os.path.exists(trajectory_file):
            existing_files = []
            for glider_dir in glider_dirs:
                existing_files.append(glob.glob(os.path.join(glider_dir, '*.nc')))
            existing_files = [item for sublist in existing_files for item in sublist]
            existing_files = sorted(existing_files)
            print('Found '+str(len(existing_files))+' matching files')

            # argument too long if we do this all in one go; so...
            count = -1
            partition = 100
            tmp_output_files = []
            for ii in range(0,len(existing_files), partition):
                count = count + 1
                these_files = existing_files[ii:ii+partition]
                tmp_trajectory_file = trajectory_file.replace('_trajectory.nc','_trajectory'+str(count).zfill(6)+'.nc')
                tmp_output_files.append(tmp_trajectory_file)
                gt.write_trajectory_file(GLIDER_CONFIG, these_files, tmp_trajectory_file, logging=logging)
                
            if len(tmp_output_files) > 1:
                gt.write_trajectory_file(GLIDER_CONFIG, tmp_output_files, trajectory_file, logging=logging)
                for tmp_output_file in tmp_output_files:
                    os.remove(tmp_output_file)
            else:
                os.rename(tmp_output_files[0], trajectory_file)
        else:
            print('Found trajectory file')
        
        num_dirs = len(matching_dirs)
        sum_staged_keys = sum(is_staged_int[matching_dirs])[0]
        sum_EO_keys = sum(is_EO_int[matching_dirs])[0]

        geo_update = False
        time_update = False

        # check if boundary file is present and up to date
        if num_dirs == sum_staged_keys and num_dirs == sum_EO_keys and \
           os.path.exists(boundary_file) or skip_boundary:
            COORDS_LIST = [0]*6
            # read old boundary values
            with open(boundary_file, "r") as filestream:
                for line in filestream:
                    COORDS_LIST = line.split(',')

            lon_average, lat_average, \
                  time_average, profile_average = \
                  gt.glider_average_values(trajectory_file, GLIDER_CONFIG, \
                  COORDS_LIST,logging=logging, verbose=verbose)

            db.shout("Boundary data already up-to-date", logging=logging,\
                     verbose=verbose)
        else:
            db.shout("Updating boundary data", logging=logging,\
                     verbose=verbose)
            COORDS_LIST = [0]*6

            # read old boundary values if it exists
            if os.path.exists(boundary_file):
                with open(boundary_file, "r") as filestream:
                    for line in filestream:
                        COORDS_LIST = line.split(',')

            if os.path.exists(boundary_file) and not skip_boundary:
                boundary_backup = boundary_file.replace('.txt','.bak')
                if os.path.exists(boundary_backup):
                    os.remove(boundary_backup)
                    os.move(boundary_file,boundary_backup)

            geo_update, time_update, lon_average, lat_average, \
                  time_average, profile_average = \
                  gt.define_boundary_file(trajectory_file, GLIDER_CONFIG, \
                  COORDS_LIST, os.path.join(EO_dir,'boundaries.txt'),\
                  float(module_config['date_pad']), logging=logging, verbose=verbose)

        # now get new boundary values
        with open(boundary_file, "r") as filestream:
            for line in filestream:
                COORDS_LIST = line.split(',')

        logging.info('Using boundary file: '+boundary_file)

        D0 = datetime.datetime.strptime(COORDS_LIST[4],'%Y-%m-%d %H:%M:%S')
        D1 = datetime.datetime.strptime(COORDS_LIST[5],'%Y-%m-%d %H:%M:%S')

        # set data limits for DT chain:
        if ARGS.proc_chain == 'DT':
            # https://www.ecmwf.int/en/why-cant-i-download-era-interim-data-current-month
            if (D1 - datetime.datetime.today()).total_seconds()/86400 > -90:
                # this could be better.....could request data up to this point
                # and check what is available
                logging.info("Delayed time data not available")
                continue
 
        Yref0,Mref0,Dref0,Jref0 = D0.strftime('%Y'),D0.strftime('%m'),\
                                  D0.strftime('%d'),D0.strftime('%j')
        Yref1,Mref1,Dref1,Jref1 = D1.strftime('%Y'),D1.strftime('%m'),\
                                  D1.strftime('%d'),D1.strftime('%j')

        # this tells us if relevant profiles for this glider have been 
        # processed against each EO variable.
        matched_EO_keys = np.nansum(matched_variables[matching_dirs,:],axis=0)

        # loop through EO types to download/augment EO data cubes
        count = -1
        for variable in variables:
            if not TRA_CONFIG[variable]['include']:
                print('Skipping cube generation for: '+variable)
                continue
            else:
                print('Considering running cube generation for: '+variable)

            count = count + 1
            get_cube = False         
            var_file = os.path.join(EO_dir,variable + '_' + \
                                    TRA_CONFIG[variable]['source']+'.nc')

            if os.path.exists(var_file) and time_update and not geo_update:
                 get_cube=True
                 #check_times...
                 nc_fid = Dataset(var_file)
                 cube_time = nc_fid.varables[TRA_CONFIG[variable]['t_var']][:]
 
                 if TRA_CONFIG[variable]['t_base'] == 'seconds':
                     D0 = \
                      datetime.datetime.strptime(TRA_CONFIG[variable]['t_ref'],\
                      '%Y-%m-%d %H:%M:%S')+\
                      datetime.timedelta(seconds=int(np.nanmax(cube_time)))
                 elif TRA_CONFIG[variable]['t_base'] == 'days':
                     D0 = \
                      datetime.datetime.strptime(TRA_CONFIG[variable]['t_ref'],\
                      '%Y-%m-%d %H:%M:%S')+\
                      datetime.timedelta(days=int(np.nanmax(cube_time)))
                 else:
                     db.shout('Bad time base', logging=logging, verbose=verbose)

            elif not os.path.exists(var_file) or geo_update==True:
                 #or matched_EO_keys[count]<sum_EO_keys-nrecords:
                 get_cube=True

            if get_cube:
                print('Running cube generation for: '+variable)
                #get whole or partial new cube according to limits
                db.shout('Sourcing '+variable, logging=logging, verbose=verbose)

                if os.path.exists(var_file):
                    os.remove(var_file)

                # begin data cube grab
                if 'ATMOS' in variable:
                    if ARGS.proc_chain == 'NRT' and TRA_CONFIG[variable]['NRT_clim']:
                        shutil.copy(TRA_CONFIG[variable]['clim_file'],var_file)
                    else:  
                        dlt.get_ecmwf(COORDS_LIST, D0, D1, var_file,\
                                      logging=logging, verbose=verbose)

                else:
                    VAR_dir=module_config['DAP_dir']+'/'+variable

                    if os.path.exists(VAR_dir):
                        shutil.rmtree(VAR_dir)

                    os.makedirs(VAR_dir)
                    os.chmod(VAR_dir, 0o777)

                    if TRA_CONFIG[variable]['local_path_root'] == None:
                        db.shout('Downloading files via OpenDAP',\
                                 logging=logging, verbose=verbose)
                        if TRA_CONFIG[variable]['source'] == 'CMEMS':
                            match_files = dlt.get_CMEMS_remote(COORDS_LIST, D0,\
                                          D1, TRA_CONFIG, variable, VAR_dir, \
                                          logging=logging,\
                                          verbose=verbose)
                        else:
                            match_files = dlt.get_remote(COORDS_LIST, D0, D1, \
                                          TRA_CONFIG, variable, VAR_dir, \
                                          logging=logging,\
                                          verbose=verbose)
                    else:
                        db.shout('Collecting files locally',\
                                 logging=logging, verbose=verbose)

                        if ARGS.proc_chain == 'NRT' and \
                           TRA_CONFIG[variable]['NRT_clim']:
                            logging.info('Replaced with climatology')
                        else:
                            match_files = dlt.get_local(COORDS_LIST, D0, D1, \
                                          TRA_CONFIG, variable, \
                                          logging=logging, \
                                          verbose=verbose)

                    if ARGS.proc_chain == 'NRT' and \
                      TRA_CONFIG[variable]['NRT_clim']:
                        shutil.copy(TRA_CONFIG[variable]['clim_file'],var_file)
                    else:
                        #update/replace existing cube
                        # have to fix concat here....later!!
                        dlt.concat_files(TRA_CONFIG, variable, VAR_dir, \
                          var_file, match_files, COORDS_LIST, logging=logging, \
                          verbose=verbose)
            else:
                print('Data cube already present for '+variable)
                db.shout('Data cube already present for '+variable,\
                         logging=logging, verbose=verbose)

        # now fly through and update database if successful
        for variable in variables:

            if not TRA_CONFIG[variable]['include']:
                print('Skipping cube flying for: '+variable)
                continue
            else:
                print('Cube flying for: '+variable)

            # change surface time to be dataset compatible
            adapted_time = gt.convert_time(time_average,\
                                          TRA_CONFIG[variable]['t_ref'],\
                                          TRA_CONFIG[variable]['t_base'])
            #define output file
            nc_concat_file = os.path.join(EO_dir,variable + '_' + \
                                    TRA_CONFIG[variable]['source']+'.nc')

            nc_outfile = nc_concat_file.replace('.nc','_traj.nc')

            # blo late edit; may want to remove this; or do a date compare
            if not os.path.exists(nc_outfile):
                print('Cube flying for: '+variable)
            else:
                print('Skipping cube flying for: '+variable)
                continue

            db.shout('Flying glider through: '+nc_concat_file, logging=logging, 
                      verbose=verbose)

            if ARGS.proc_chain == 'NRT' and TRA_CONFIG[variable]['NRT_clim']:
                clim = True
            else:
                clim = False

            success = gt.fly_cube(variable, TRA_CONFIG, GLIDER_CONFIG, \
                        module_config, nc_concat_file, nc_outfile, \
                        adapted_time, time_average,\
                        lon_average, lat_average, profile_average,\
                        clim=clim, \
                        logging=logging, verbose=verbose)

            if success:
                # update database for entire record processed
                db.shout(glider_tag+\
                         ' now has trajectory for '+variable, \
                         logging=logging, verbose=verbose)

                today = "'"+datetime.datetime.now().strftime('%Y%m%d_%H%M')+"'"
                print(database)
                conn, c = db.connectDB(database)
                for glider_dir in glider_dirs:
                    c.execute("UPDATE {tn} SET {sn} = 1 WHERE {fn} = {fm}".\
                              format(tn=module_config['table_name'],\
                                     sn=module_config['EO_column'],\
                                     fn=module_config['stage_dir_column'],\
                                     fm='"'+glider_dir+'"'))

                    c.execute("UPDATE {tn} SET {sn} = {val} WHERE {fn} = {fm}".\
                              format(tn=module_config['table_name'],\
                                     sn=module_config['EO_column']+'_date',\
                                     val=today,\
                                     fn=module_config['stage_dir_column'],\
                                     fm='"'+glider_dir+'"'))
                    conn.commit()
                conn.close()
            else:
                db.shout(glider_tag+\
                         ' failed to generate trajectory for '+variable, \
                         logging=logging, verbose=verbose)
#--EOF
