#!/usr/bin/env python

import glob
import os, shutil
import netCDF4 as nc
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from scipy import integrate
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
    pp[pp>1e5] = np.nan
    pp[pp<0.0] = np.nan

    # check for empties
    if np.all(np.isnan(pp)):
        pp_int_di = np.nan
        pp_int = Z_DEPTHS*np.nan
    else:
        # interpolate
        pp_int = interp1d(pp_depth, pp, bounds_error=False)(Z_DEPTHS)

        # integrated (prior to interpolation)
        pp_int_di = integrate.simpson(pp[np.isfinite(pp)], abs(pp_depth)[np.isfinite(pp)])
        pp_int_di = np.asarray(abs(pp_int_di)).astype(float)

        # integrated (post interpolation)
        pp_tmp_di = integrate.simpson(pp_int[np.isfinite(pp_int)], abs(Z_DEPTHS)[np.isfinite(pp_int)])
        pp_tmp_di = np.asarray(abs(pp_tmp_di)).astype(float)

        # scale up to match integral values
        pp_int = pp_int * pp_int_di / pp_tmp_di

    pp_int_di = np.ones(len(pp_int))*pp_int_di

    return pp_int, pp_int_di

#----------------------
if __name__ == "__main__":

    # pp_dirs
    pp_dir1 = os.path.join('/Volumes/PML_BACKUP/Linux_desktop//data/datasets/Projects/AlterEco/Glider_data/BODC_pp_data/EGO/EGO_454_Cabot')
    pp_dir2 = os.path.join('/Volumes/PML_BACKUP/Linux_desktop//data/datasets/Projects/AlterEco/Glider_data/BODC_pp_data/EGO/Cabot_20190312/EGO_517_Cabot')
    pp_dir3 = os.path.join('/Volumes/PML_BACKUP/Linux_desktop//data/datasets/Projects/AlterEco/Glider_data/BODC_pp_data/EGO/Cook_20171115/EGO_441_Cook')
    pp_dir4 = os.path.join('/Volumes/PML_BACKUP/Linux_desktop//data/datasets/Projects/AlterEco/Glider_data/BODC_pp_data/EGO/Coprolite_20181202/EGO_500_Coprolite')
    pp_dir5 = os.path.join('/Volumes/PML_BACKUP/Linux_desktop//data/datasets/Projects/AlterEco/Glider_data/BODC_pp_data/EGO/EGO_477_Dolomite')
    pp_dir6 = os.path.join('/Volumes/PML_BACKUP/Linux_desktop//data/datasets/Projects/AlterEco/Glider_data/BODC_pp_data/EGO/Dolomite_20181202/EGO_499_Dolomite')
    pp_dir7 = os.path.join('/Volumes/PML_BACKUP/Linux_desktop//data/datasets/Projects/AlterEco/Glider_update_run/BODC_pp_data/EGO/EGO_478_Eltanin')
    pp_dir8 = os.path.join('/Volumes/PML_BACKUP/Linux_desktop//data/datasets/Projects/AlterEco/Glider_update_run/BODC_pp_data/humpback_UEA/UEA_579_humpback')
    pp_dir9 = os.path.join('/Volumes/PML_BACKUP/Linux_desktop//data/datasets/Projects/AlterEco/Glider_data/BODC_pp_data/EGO/EGO_481_Kelvin')
    pp_dir10 = os.path.join('/Volumes/PML_BACKUP/Linux_desktop//data/datasets/Projects/AlterEco/Glider_update_run/BODC_pp_data/EGO/EGO_496_Melonhead')
    pp_dir11 = os.path.join('/Volumes/PML_BACKUP/Linux_desktop//data/datasets/Projects/AlterEco/Glider_update_run/BODC_pp_data/EGO/EGO_455_Orca')
    pp_dir12 = os.path.join('/Volumes/PML_BACKUP/Linux_desktop//data/datasets/Projects/AlterEco/Glider_update_run/BODC_pp_data/EGO/EGO_493_Orca')
    pp_dir13 = os.path.join('/Volumes/PML_BACKUP/Linux_desktop//data/datasets/Projects/AlterEco/Glider_data/BODC_pp_data/EGO/Stella_20180207/EGO_494_Stella')

    pp_dirs = [pp_dir1, pp_dir2, pp_dir3, pp_dir4, pp_dir5, pp_dir6, pp_dir7, pp_dir8, pp_dir9, pp_dir10, pp_dir11, pp_dir12, pp_dir13]

    # get nc files
    input_files = glob.glob("/Users/benloveday/Documents/Projects/Altereco/AlterEco_primary_production_dataset_ESSD_v0/Figure_code/FINAL_DATA/*PP_R*.nc")

    # loop
    for input_file, pp_dir in zip(sorted(input_files), pp_dirs):
        print(f"Input: {input_file}")
        output_file = input_file.replace("FINAL_DATA","FINAL_DATA_v2")
        print(f"Output: {output_file}")
        shutil.copy(input_file, output_file)

        nc_fid = nc.Dataset(input_file)
        profile_numbers = nc_fid.variables["PROFILE_NUMBER"][:].data
        DEPTHS = nc_fid.variables["DEPTH"][:].data
        TIME = nc_fid.variables["TIME"][:].data
        PP_DI = nc_fid.variables["DEPTH_INTEGRATED_PRIMARY_PRODUCTION"][:].data
        PP = nc_fid.variables["PRIMARY_PRODUCTION"][:].data
        PP_DI_EO = nc_fid.variables["DEPTH_INTEGRATED_PRIMARY_PRODUCTION_EO"][:].data
        PP_EO = nc_fid.variables["PRIMARY_PRODUCTION_EO"][:].data
        nc_fid.close()

        PP_DI_new = np.ones(len(PP_DI))*-99999.0
        PP_new = np.ones(len(PP_DI))*-99999.0
        PP_DI_EO_new = np.ones(len(PP_DI))*-99999.0
        PP_EO_new = np.ones(len(PP_DI))*-99999.0

        for profile_number in np.unique(profile_numbers):

            profile_tag = str(int(profile_number)).zfill(6)
            print(profile_tag)
            ii = [profile_number == profile_numbers]
            these_depths = DEPTHS[ii]
            pp_file = os.path.join(pp_dir,'pp_profile_station_'+profile_tag+'_xing.split')
            pp_file_eo = os.path.join(pp_dir,'pp_profile_station_'+profile_tag+'_xing_eo.split')

            if os.path.exists(pp_file):
                pp_int, pp_int_di = get_clean_pp(pp_file, these_depths)
                PP_DI_new[ii] = pp_int_di
                PP_new[ii] = pp_int

            if os.path.exists(pp_file_eo):
                pp_int_eo, pp_int_di_eo = get_clean_pp(pp_file_eo, these_depths)
                PP_DI_EO_new[ii] = pp_int_di_eo
                PP_EO_new[ii] = pp_int_eo

        '''
        PP_DI[PP_DI<0] = np.nan
        PP_DI_new[PP_DI_new<0] = np.nan

        plt.plot(TIME, PP_DI, 'k')
        plt.plot(TIME, PP_DI_new, 'b')
        plt.show()
        '''

        nc_fid = nc.Dataset(output_file, 'a')
        nc_fid.variables["DEPTH_INTEGRATED_PRIMARY_PRODUCTION"][:] = PP_DI_new
        nc_fid.variables["PRIMARY_PRODUCTION"][:] = PP_new
        nc_fid.variables["DEPTH_INTEGRATED_PRIMARY_PRODUCTION_EO"][:] = PP_DI_EO_new
        nc_fid.variables["PRIMARY_PRODUCTION_EO"][:] = PP_EO_new
        nc_fid.close()
