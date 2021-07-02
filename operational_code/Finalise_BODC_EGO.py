#!/usr/bin/env python

import glob
import os, shutil
import netCDF4 as nc
import numpy as np
import datetime
from scipy.interpolate import interp1d
import metadata_specs as ms
import warnings
warnings.filterwarnings('ignore')

def get_clean_pp(PFILE, Z_DEPTHS):

    pp_vars = np.genfromtxt(PFILE,dtype=str,delimiter='\t')
    pp_depth = np.asarray(pp_vars[1:,0]).astype(float)
    # Morel91 outputs as g/C/m3/minute (default time step). Scale up to mg/day
    pp = np.asarray(pp_vars[1:,1]).astype(float)*1000.00*24*60

    # screen out where calculation is deeper than glider
    pp[pp_depth > max(Z_DEPTHS)+1] = np.nan

    # scrape impossible results
    pp[pp>1e8] = np.nan
    pp[pp<0.0] = np.nan

    # check for empties
    if np.all(np.isnan(pp)):
        pp_int_di = np.nan
        pp_int = Z_DEPTHS*np.nan
    else:
        # interpolate
        pp_int = interp1d(pp_depth, pp, bounds_error=False)(Z_DEPTHS)

        # integrated (prior to interpolation) 
        pp_int_di = np.nansum(pp*abs(np.gradient(pp_depth)))
        pp_int_di = np.asarray(pp_int_di).astype(float)

        # scale up to match integral values
        pp_tmp = np.nansum(pp_int*abs(np.gradient(Z_DEPTHS)))
        pp_int = pp_int * pp_int_di / pp_tmp

        if pp_int_di < 0.0:
            pp_int_di = np.nan

    pp_int_di = np.ones(len(pp_int))*pp_int_di

    return pp_int, pp_int_di

def create_netcdf_file(out_file, the_vars, metadata):

    print('Writing output...')
    if os.path.exists(out_file):
        os.remove(out_file)

    try:
        # create a new netCDF file for writing
        nc_file  = nc.Dataset(out_file,'w',format='NETCDF4_CLASSIC')

        # define dimensions
        nc_file.createDimension('TIME')
        
        # define attributes
        nc_file.data_type = metadata['data_type']
        nc_file.format_version = metadata['format_version']
        nc_file.platform_code = metadata['platform_code']
        nc_file.deployment_code = metadata['deployment_code']
        nc_file.project_name = metadata['project_name']
        nc_file.project_description = metadata['project_description']
        nc_file.campaign = metadata['campaign']
        nc_file.date_update = metadata['date_update']
        nc_file.data_mode = metadata['data_mode']
        nc_file.data_type = metadata['data_type']
        nc_file.naming_authority = metadata['naming_authority']
        nc_file.processing = metadata['processing']
        nc_file.ancillary_mission_overview = metadata['ancillary_mission_overview']
        nc_file.ancillary_mission_specifics = metadata['ancillary_mission_specifics']
        nc_file.ancillary_base_data = metadata['ancillary_base_data']

        #define variables and write
        for the_var in the_vars:
            if 'FLAG' in the_var['name'].upper():
                ncvar = nc_file.createVariable(the_var['name'],'i',('TIME'),fill_value=the_var['fill'])
            elif 'TIME' in the_var['name'].upper():
                ncvar = nc_file.createVariable(the_var['name'],'d',('TIME'),fill_value=the_var['fill'])
            else:
                ncvar = nc_file.createVariable(the_var['name'],'f',('TIME'),fill_value=the_var['fill'])

            ncvar.standard_name = the_var['sname']
            ncvar.units = the_var['unit']
            ncvar.description = the_var['desc']
            raw_var = the_var['var']
            raw_var[raw_var > 1e12] = np.nan
            raw_var[raw_var < -1e12] = np.nan
            raw_var[np.isnan(raw_var)] = the_var['fill']
            ncvar[:] = raw_var

        # Close the file.
        nc_file.close()
        os.chmod(out_file, 0o777)
      
        print('Success')
    except:
        print('Failure')

#----------------------
if __name__ == "__main__":

    test_run = True # ok: 0,5
    selected_gliders = -1
    output_path = os.path.join(os.getcwd(),'final_output')

    if not os.path.exists(output_path):
        os.makedirs(output_path)
        os.chmod(output_path, 0o777)

    pp_dirs, orig_files, final_files, metadata_descs = ms.metadata_specs()

    if test_run:
        pp_dirs = [pp_dirs[selected_gliders]]
        orig_files = [orig_files[selected_gliders]]
        final_files = [final_files[selected_gliders]]
        metadata_descs = [metadata_descs[selected_gliders]]

    for pp_dir, orig_file, final_file, metadata_desc in zip(pp_dirs, orig_files, final_files, metadata_descs):
        glider_tag = orig_file.split('_')[0]+'_'+orig_file.split('_')[1]
        print(glider_tag)
        # set up file names
        output_file = os.path.join(output_path,final_file)
        raw_file = os.path.join(os.path.dirname(pp_dir.replace('BODC_pp_data','BODC_data')),orig_file)
        preproc_dir = os.path.dirname(pp_dir.replace('BODC_pp_data','BODC_preprocessed_data'))
        preproc_files_eo = glob.glob(os.path.join(preproc_dir,'*'+glider_tag+'*xing_eo.nc'))
        print(len(preproc_files_eo))

        nc_fid = nc.Dataset(raw_file,'r')
        try:
            ORIG_TIME = nc_fid.variables['TIME'][:]
        except:
            ORIG_TIME = nc_fid.variables['time'][:]
        nc_fid.close()

        ACCUM_TIME = []
        ACCUM_PNUM = []
        ACCUM_LAT = []
        ACCUM_LON = []
        ACCUM_PRES = []
        ACCUM_DEPTH = []
        ACCUM_CHLA_CORR = []
        ACCUM_MLD = []
        ACCUM_ZEU = []
        ACCUM_ZEU_FLAG = []
        ACCUM_PAR_CORR = []
        ACCUM_PAR_CORR_FLAG = []
        ACCUM_PAR_CORR_EO = []
        ACCUM_PAR_CORR_EO_FLAG = []
        ACCUM_PP = []
        ACCUM_PP_DI = []
        ACCUM_PP_EO = []
        ACCUM_PP_DI_EO = []
 
        count = -1
        for preproc_file_eo in sorted(preproc_files_eo):
            print(preproc_file_eo)

            count = count + 1
            if count > 1e9:
                continue

            preproc_file = preproc_file_eo.replace('_eo','')

            profile_number = int(preproc_file.split('_')[-4])

            # Add the corrected and EO variables 
            nc_fid = nc.Dataset(preproc_file_eo,'r')
            try:
                this_time = nc_fid.variables['TIME'][:].data
            except:
                this_time = nc_fid.variables['time'][:].data

            this_lat = nc_fid.variables['LATITUDE_CORRECTED'][:].data
            this_lon = nc_fid.variables['LONGITUDE_CORRECTED'][:].data
            this_pres = nc_fid.variables['PRES_CORRECTED'][:].data
            this_depth = nc_fid.variables['DEPTH_CORRECTED'][:].data

            this_chla_corr = nc_fid.variables['CHLA_CORRECTED'][:].data
            this_mld = nc_fid.variables['MIXED_LAYER_DEPTH'][:].data
            this_zeu = nc_fid.variables['EUPHOTIC_DEPTH'][:].data
            this_zeu_flag = nc_fid.variables['EUPHOTIC_DEPTH_FLAG'][:].data

            this_dpar_corr_eo = nc_fid.variables['DOWNWELLING_PAR_CORRECTED'][:].data
            this_dpar_corr_eo_flag = nc_fid.variables['DOWNWELLING_PAR_CORRECTED_FLAG'][:].data
            nc_fid.close()

            # Add the insitu variables
            if os.path.exists(preproc_file):
                nc_fid = nc.Dataset(preproc_file,'r')
                this_dpar_corr = nc_fid.variables['DOWNWELLING_PAR_CORRECTED'][:].data
                this_dpar_corr_flag = nc_fid.variables['DOWNWELLING_PAR_CORRECTED_FLAG'][:].data
                nc_fid.close()
            else:
                this_dpar_corr = np.ones(len(this_dpar_corr_eo))*np.nan
                this_dpar_corr_flag = this_dpar_corr_eo_flag.copy()

            ACCUM_TIME.append(this_time)
            ACCUM_PNUM.append(np.ones(len(this_time))*profile_number) 
            ACCUM_LAT.append(this_lat)
            ACCUM_LON.append(this_lon)
            ACCUM_PRES.append(this_pres)
            ACCUM_DEPTH.append(this_depth)
            ACCUM_CHLA_CORR.append(this_chla_corr)
            ACCUM_MLD.append(this_mld)
            ACCUM_ZEU.append(this_zeu)
            ACCUM_ZEU_FLAG.append(this_zeu_flag)
            ACCUM_PAR_CORR.append(this_dpar_corr)
            ACCUM_PAR_CORR_FLAG.append(this_dpar_corr_flag)
            ACCUM_PAR_CORR_EO.append(this_dpar_corr_eo)
            ACCUM_PAR_CORR_EO_FLAG.append(this_dpar_corr_eo_flag)

            # Find the PP files
            profile_tag = os.path.basename(preproc_file).split('_')[-4]
            pp_file = os.path.join(pp_dir,'pp_profile_station_'+profile_tag+'_xing.split')
            pp_file_eo = os.path.join(pp_dir,'pp_profile_station_'+profile_tag+'_xing_eo.split')

            # ----------------- Add the PP -----------------
            if os.path.exists(pp_file):
                pp_int,pp_int_di = get_clean_pp(pp_file, this_depth)
            else:
                pp_int = np.ones(len(this_time))*np.nan
                pp_int_di = np.ones(len(this_time))*np.nan

            ACCUM_PP.append(pp_int)
            ACCUM_PP_DI.append(pp_int_di)

            # ---------------- Add the PP EO ----------------
            if os.path.exists(pp_file_eo):
                pp_int_eo,pp_int_di_eo = get_clean_pp(pp_file_eo, this_depth)
            else:
                pp_int_eo = np.ones(len(this_time))*np.nan
                pp_int_di_eo = np.ones(len(this_time))*np.nan

            ACCUM_PP_EO.append(pp_int_eo)
            ACCUM_PP_DI_EO.append(pp_int_di_eo)

        FINAL_TIME             = np.asarray([item for sublist in ACCUM_TIME for item in sublist])
        FINAL_PNUM             = np.asarray([item for sublist in ACCUM_PNUM for item in sublist])
        FINAL_LAT              = np.asarray([item for sublist in ACCUM_LAT for item in sublist])
        FINAL_LON              = np.asarray([item for sublist in ACCUM_LON for item in sublist])
        FINAL_PRES             = np.asarray([item for sublist in ACCUM_PRES for item in sublist])
        FINAL_DEPTH            = np.asarray([item for sublist in ACCUM_DEPTH for item in sublist])
        FINAL_CHLA_CORR        = np.asarray([item for sublist in ACCUM_CHLA_CORR for item in sublist])
        FINAL_MLD              = np.asarray([item for sublist in ACCUM_MLD for item in sublist])
        FINAL_ZEU              = np.asarray([item for sublist in ACCUM_ZEU for item in sublist])
        FINAL_ZEU_FLAG         = np.asarray([item for sublist in ACCUM_ZEU_FLAG for item in sublist])
        FINAL_PAR_CORR         = np.asarray([item for sublist in ACCUM_PAR_CORR for item in sublist])
        FINAL_PAR_CORR_FLAG    = np.asarray([item for sublist in ACCUM_PAR_CORR_FLAG for item in sublist])
        FINAL_PAR_CORR_EO      = np.asarray([item for sublist in ACCUM_PAR_CORR_EO for item in sublist])
        FINAL_PAR_CORR_EO_FLAG = np.asarray([item for sublist in ACCUM_PAR_CORR_EO_FLAG for item in sublist])
        FINAL_PP               = np.asarray([item for sublist in ACCUM_PP for item in sublist])
        FINAL_PP_EO            = np.asarray([item for sublist in ACCUM_PP_EO for item in sublist])
        FINAL_PP_DI            = np.asarray([item for sublist in ACCUM_PP_DI for item in sublist])
        FINAL_PP_DI_EO         = np.asarray([item for sublist in ACCUM_PP_DI_EO for item in sublist])

        print('Original record dimension: '+str(np.shape(ORIG_TIME)))
        print('New time dimension: '+str(np.shape(FINAL_TIME)))
        print('New pnum dimension: '+str(np.shape(FINAL_PNUM)))
        print('New lat dimension: '+str(np.shape(FINAL_LAT)))
        print('New lon dimension: '+str(np.shape(FINAL_LON)))
        print('New pres dimension: '+str(np.shape(FINAL_PRES)))
        print('New depth dimension: '+str(np.shape(FINAL_DEPTH)))
        print('New chla_corr dimension: '+str(np.shape(FINAL_CHLA_CORR)))
        print('New mld dimension: '+str(np.shape(FINAL_MLD)))
        print('New zeu dimension: '+str(np.shape(FINAL_ZEU)))
        print('New zeu_flag dimension: '+str(np.shape(FINAL_ZEU_FLAG)))
        print('New par_corr dimension: '+str(np.shape(FINAL_PAR_CORR)))
        print('New par_corr_flag dimension: '+str(np.shape(FINAL_PAR_CORR_FLAG)))
        print('New par_corr_eo dimension: '+str(np.shape(FINAL_PAR_CORR_EO)))
        print('New par_corr_eo_flag dimension: '+str(np.shape(FINAL_PAR_CORR_EO_FLAG)))
        print('New PP dimension: '+str(np.shape(FINAL_PP)))
        print('New PP_eo dimension: '+str(np.shape(FINAL_PP_EO)))
        print('New PP DI dimension: '+str(np.shape(FINAL_PP_DI)))
        print('New PP_DI_eo dimension: '+str(np.shape(FINAL_PP_DI_EO)))

        # small flag corrections:
        FINAL_PAR_CORR_FLAG[FINAL_PAR_CORR_FLAG == 0] = 3
        FINAL_PAR_CORR_EO_FLAG[FINAL_PAR_CORR_EO_FLAG == 0] = 3

        # correct matlab time in humpback
        if 'AE3_sg579' in glider_tag:
            python_datetime = []
            print(np.nanmin(FINAL_TIME),np.nanmax(FINAL_TIME))
            for matlab_datenum in FINAL_TIME:
                tmp_time = datetime.datetime.\
                                      fromordinal(int(matlab_datenum)\
                                      - 366) + \
                                      datetime.timedelta(days=matlab_datenum%1)
                python_datetime.append((tmp_time - datetime.datetime(1970,1,1,0,0,0)).total_seconds())
            FINAL_TIME = np.asarray(python_datetime)

        # vars are: var, vname, standard_name, description, unit, _FillValue
        time_dict = {'name':  'TIME',\
                     'var':   FINAL_TIME,\
                     'sname': 'time',\
                     'desc':  'glider time',\
                     'unit':  'seconds since 1970-01-01T00:00:00Z',\
                     'fill':  -99999}

        pnum_dict = {'name':  'PROFILE_NUMBER',\
                     'var':   FINAL_PNUM,\
                     'sname': 'profile number',\
                     'desc':  'profile number dervied from glider dive path',\
                     'unit':  'none',\
                     'fill':  -99999}

        lat_dict = {'name':  'LATITUDE',\
                     'var':   FINAL_LAT,\
                     'sname': 'latitude',\
                     'desc':  'Quality controlled, corrected latitude',\
                     'unit':  'degrees north',\
                     'fill':  -99999}

        lon_dict = {'name':  'LONGITUDE',\
                     'var':   FINAL_LON,\
                     'sname': 'longitude',\
                     'desc':  'Quality controlled, corrected longitude',\
                     'unit':  'degrees east',\
                     'fill':  -99999}

        pres_dict = {'name':  'PRESSURE',\
                     'var':   FINAL_PRES,\
                     'sname': 'sea_water_pressure',\
                     'desc':  'Quality controlled, corrected sea water pressure',\
                     'unit':  'decibar',\
                     'fill':  -99999}

        depth_dict = {'name':  'DEPTH',\
                     'var':   FINAL_DEPTH,\
                     'sname': 'depth below sea level',\
                     'desc':  'Quality controlled, corrected depth',\
                     'unit':  'm',\
                     'fill':  -99999}

        chla_dict = {'name':  'CHLA',\
                     'var':   FINAL_CHLA_CORR,\
                     'sname': 'chlorophyll_concentration_in_sea_water',\
                     'desc':  'Chlorophyll concentration in sea water as measured by glider underway fluorescence. Quenching corrected using Xing et al. (2012)',\
                     'unit':  'mg m-3',\
                     'fill':  -99999}

        mld_dict = {'name':  'MIXED_LAYER_DEPTH',\
                     'var':   FINAL_MLD,\
                     'sname': 'ocean mixed layer thickness',\
                     'desc':  'Mixed layer depth, derived using Holte and Talley (2009)',\
                     'unit':  'm',\
                     'fill':  -99999}

        zeu_dict = {'name':  'EUPHOTIC_DEPTH',\
                     'var':   FINAL_ZEU,\
                     'sname': 'Euphotic depth',\
                     'desc':  'Euphotic depth',\
                     'unit':  'm',\
                     'fill':  -99999}

        zeu_flag_dict = {'name':  'EUPHOTIC_DEPTH_FLAG',\
                     'var':   FINAL_ZEU_FLAG,\
                     'sname': 'Euphotic depth flag',\
                     'desc':  'Euphotic depth method flag. Zeu calculated using; (1): 0.01*uncorrected par surface level, (2):0.01*corrected par surface level , (3):Lee et al. (2007) for in situ glider surface CHL, (4):Lee at al. (2007) for contemporaneous satellite CHL',\
                     'unit':  'm',\
                     'fill':  -1}

        par_dict = {'name':  'DOWNWELLING_PAR',\
                     'var':   FINAL_PAR_CORR,\
                     'sname': 'downwelling photosynthetic radiative flux in seawater',\
                     'desc':  'Downwelling PAR profile derived from glider sensors',\
                     'unit':  'W m-2',\
                     'fill':  -99999}

        par_flag_dict = {'name':  'DOWNWELLING_PAR_FLAG',\
                     'var':   FINAL_PAR_CORR_FLAG,\
                     'sname': '',\
                     'desc':  'PAR flag. Par is derived from: (1): in situ glider sensor, (2): surface Modis PAR/KD490, (3): surface MODIS PAR and glider surface CHLA',\
                     'unit':  'm',\
                     'fill':  -1}

        par_eo_dict = {'name':  'DOWNWELLING_PAR_EO',\
                     'var':   FINAL_PAR_CORR_EO,\
                     'sname': 'downwelling photosynthetic radiative flux in seawater',\
                     'desc':  'Downwelling PAR profile derived from MODIS daily PAR',\
                     'unit':  'W m-2',\
                     'fill':  -99999}

        par_eo_flag_dict = {'name':  'DOWNWELLING_PAR_EO_FLAG',\
                     'var':   FINAL_PAR_CORR_EO_FLAG,\
                     'sname': '',\
                     'desc':  'PAR flag. Par is derived from: (1): in situ glider sensor, (2): surface Modis PAR/KD490, (3): surface MODIS PAR and glider surface CHLA',\
                     'unit':  'm',\
                     'fill':  -1}

        pp_dict = {'name':  'PRIMARY_PRODUCTION',\
                     'var':   FINAL_PP,\
                     'sname': 'net primary production of biomass expressed as carbon per unit volume in sea water',\
                     'desc':  'Primary production, derived from glider PAR, calculated using Morel (1991)',\
                     'unit':  'mg C m-3 d-1',\
                     'fill':  -99999}

        pp_di_dict = {'name':  'DEPTH_INTEGRATED_PRIMARY_PRODUCTION',\
                     'var':   FINAL_PP_DI,\
                     'sname': '',\
                     'desc':  'Depth integrated primary production to ZEU, derived from glider PAR.',\
                     'unit':  'mg C m-2 d-1',\
                     'fill':  -99999}

        pp_eo_dict = {'name':  'PRIMARY_PRODUCTION_EO',\
                     'var':   FINAL_PP_EO,\
                     'sname': 'net primary production of biomass expressed as carbon per unit volume in sea water',\
                     'desc':  'Primary production, derived from Earth observation based PAR, calculated using Morel (1991)',\
                     'unit':  'mg C m-3 d-1',\
                     'fill':  -99999}

        pp_di_eo_dict = {'name':  'DEPTH_INTEGRATED_PRIMARY_PRODUCTION_EO',\
                     'var':   FINAL_PP_DI_EO,\
                     'sname': '',\
                     'desc':  'Depth integrated primary production to ZEU, derived from Earth observation based PAR',\
                     'unit':  'mg C m-2 d-1',\
                     'fill':  -99999}

        all_vars = [time_dict,\
                    pnum_dict,\
                    lon_dict,\
                    lat_dict,\
                    pres_dict,\
                    depth_dict,\
                    chla_dict,\
                    mld_dict,\
                    zeu_dict,\
                    zeu_flag_dict,\
                    par_dict,\
                    par_flag_dict,\
                    par_eo_dict,\
                    par_eo_flag_dict,
                    pp_dict,\
                    pp_di_dict,\
                    pp_eo_dict,\
                    pp_di_eo_dict]

        create_netcdf_file(output_file, all_vars, metadata_desc)


 
        

        

