#!/usr/bin/env python

import numpy as np
import netCDF4 as nc
import glob
import glider_tools as gt

def fluor_correction_Swa(PROFILE,TIME,CHLA,ZEU,DEPTH,SCATTER,\
                         verbose=False,logging=None):
    '''
    fluor correction from Swart et al., 2015.
    '''
    method_success = True
    CORR_CHLA = CHLA.copy()
    SCATTER_corr = SCATTER.copy()

    # make 1d variables
    if len(np.shape(PROFILE)) == 2:
        profile1d     = np.nanmean(PROFILE,axis=0)
        time1d        = np.nanmean(TIME,axis=0)
        dims          = len(time1d)
    else:
        profile1d     = PROFILE[:]
        time1d        = TIME[:]
        dims          = 1


    for ii in np.arange(0,dims):
        if verbose:
            print('profile: '+str(ii))

        if len(np.shape(PROFILE)) == 2:
            this_ZEU = ZEU[ii]
            this_DEPTH = DEPTH[:,ii]
            this_CORR_CHLA = CORR_CHLA[:,ii]
            this_SCATTER_corr = SCATTER_corr[:,ii]
        else:
            this_ZEU = ZEU
            this_DEPTH = DEPTH.copy()
            this_CORR_CHLA = CORR_CHLA.copy()
            this_SCATTER_corr = SCATTER_corr.copy()

        if np.isnan(this_ZEU):
            method_success = False
            if logging == None or verbose:
                print('Cannot apply Swart correction, no Zeu: '+str(ii))
            if logging:
                logging.info('Cannot apply Swart correction, no Zeu: '+str(ii))

        else:
            try:
                kk = np.where(np.isnan(this_CORR_CHLA))
                dd = np.where((this_DEPTH <= this_ZEU))[0]
                tmp_CHLA = this_CORR_CHLA.copy()
                tmp_SCA = this_SCATTER_corr.copy()
                tmp_CHLA[~dd] = np.nan
                tmp_SCA[~dd] = np.nan
                ratio = tmp_CHLA/tmp_SCA
                max_ratio = np.nanmax(ratio)
                ee = np.where((ratio == max_ratio))
                if this_DEPTH[np.isfinite(this_DEPTH)][0] > this_DEPTH[np.isfinite(this_DEPTH)][-1]:
                    this_CORR_CHLA[ee[0][-1]:] = max_ratio*this_SCATTER_corr[ee:]
                else:
                    this_CORR_CHLA[:ee[0][0]] = max_ratio*this_SCATTER_corr[0:ee]
                this_CORR_CHLA[kk] = np.nan
            except:
                method_success = False
                if logging == None or verbose:
                    print('Cannot apply Swart correction, NaN ratio: '+str(ii))
                if logging:
                    logging.info('Cannot apply Swart correction, NaN ratio: '\
                             +str(ii))

        if len(np.shape(PROFILE)) == 2:
            CORR_CHLA[:,ii] = this_CORR_CHLA[:]
        else:
            CORR_CHLA = this_CORR_CHLA[:]

    return CORR_CHLA, method_success

if __name__ == '__main__':
    print('Running')
    input_files = glob.glob("/Users/benloveday/Desktop/Glider_data/BODC_staged_data/EGO/*.nc")

    for file in input_files:
        
        print(file)