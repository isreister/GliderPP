#!/usr/bin/env python
'''
Description:    Fluorescence quenching correction methods

Version: 	v1.0 12/2017
	 	v1.1 08/2018

Ver. hist:      v1.1 is current

Author:		Ben Loveday, Plymouth Marine Laboratory

License:        MIT Licence -- Copyright 2017 Plymouth Marine Laboratory

		Permission is hereby granted, free of charge, to any person
                obtaining a copy of this software and associated documentation 
                files (the "Software"), to deal in the Software without 
                restriction, including without limitation the rights to use, 
                copy, modify, merge, publish, distribute, sublicense, and/or 
                sell copies of the Software, and to permit persons to whom the 
                Software is furnished to do so, subject to the following 
                conditions:

                The above copyright notice and this permission notice shall be 
                included in all copies or substantial portions of the Software.

                THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, 
                EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES 
                OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND 
                NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT 
                HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
                WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING 
                FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR 
                OTHER DEALINGS IN THE SOFTWARE.
'''
#-imports-----------------------------------------------------------------------
import os, sys, shutil
import datetime
import numpy as np
import scipy.stats as st
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import logging
import common_tools as ct
from netCDF4 import Dataset
import glider_tools as gt
import netCDF_tools as nct
import gsw
from scipy.interpolate import interp1d

#---
def fluor_correction_Hem(GLIDER_CONFIG,hem_regress_files,hem_correct_files,\
                         glider_tag, N_smooth=3, surface_depth=20, \
                         logging=False, verbose=False, Zthresh = 40):
    '''
    Corrects Chl profiles with nighttime backscattering profiles. 
    Now also corrects DCM profiles. Method ref: Hemsley et al., 2015      

    Steps:
    1. prep masks and quality control
    2. regress
    3. determine DCM and correct profiles without DCM

    Note: all other variables should be corrected by here, so read them in!
    '''

    debug = False

    all_CHLA = []
    all_SCATTER = []
    all_DEPTH = []
    all_PAR = []
    all_PROFILE_NUMBER = []

    # read processing config file
    CONFIG_DICT = gt.read_config_file(GLIDER_CONFIG,logging=logging)
    chl_var = CONFIG_DICT['allowed_vars'].split(',')[CONFIG_DICT['allowed_heads'].index('CHLA')]

    for hem_regress_file in hem_regress_files:
        # -get the variable names for comparison to config list
        nc_fid     = Dataset(hem_regress_file, 'r')
        PRES = nc_fid.variables['PRES_CORRECTED'][:]
        DEPTH = nc_fid.variables['DEPTH_CORRECTED'][:]
        CHLA = nc_fid.variables[chl_var][:]
        SCATTER = nc_fid.variables['BACKSCATTER_CORRECTED'][:]
        PAR = nc_fid.variables['DOWNWELLING_PAR_CORRECTED'][:]
        ZEU = nc_fid.variables['EUPHOTIC_DEPTH'][:]
        MLD = nc_fid.variables['MIXED_LAYER_DEPTH'][:]
        PROFILE_NUMBER = nc_fid.variables['PROFILE_NUMBER'][:]
        nc_fid.close()

        all_CHLA.append(CHLA)
        all_SCATTER.append(SCATTER)
        all_DEPTH.append(DEPTH)
        all_PAR.append(PAR)
        all_PROFILE_NUMBER.append(PROFILE_NUMBER)

    # flatten lists and make into arrays
    CHLA_array = np.asarray([item for sublist in all_CHLA for item in sublist]).astype(float)
    SCATTER_array = np.asarray([item for sublist in all_SCATTER for item in sublist]).astype(float)
    DEPTH_array = np.asarray([item for sublist in all_DEPTH for item in sublist]).astype(float)
    PAR_array = np.asarray([item for sublist in all_PAR for item in sublist]).astype(float)
    PROFILE_NUMBER_array = np.asarray([item for sublist in all_PROFILE_NUMBER for item in sublist]).astype(int)

    # begin filtering
    #remove deep values > Zthresh
    CHLA_array[DEPTH_array > Zthresh]    = np.nan
    SCATTER_array[DEPTH_array > Zthresh] = np.nan
    PAR_array[DEPTH_array > Zthresh]     = np.nan

    #remove nans
    ii = np.where((np.isfinite(CHLA_array)) & \
                  (np.isfinite(SCATTER_array)))[0]
    CHLA_array = CHLA_array[ii]
    SCATTER_array = SCATTER_array[ii]

    # regress
    slope, intercept, r_val, p_val, stderr = st.linregress(SCATTER_array,CHLA_array)
    r_val, p_val                           = st.spearmanr(SCATTER_array,CHLA_array)

    # make regression plot
    fig1 = plt.figure(figsize=(10,10), dpi=300)
    plt.scatter(SCATTER_array, CHLA_array)
    xvals = np.linspace(0,np.max(SCATTER_array),100)
    plt.plot(xvals,slope*xvals + intercept,'k--')
    plt.xlim([np.nanmin(SCATTER_array),np.nanmax(SCATTER_array)])
    plt.ylim([np.nanmin(CHLA_array),np.nanmax(CHLA_array)])
    plt.xlabel('Backscatter [m$^{-1}$]')
    plt.ylabel('Chlorophyll [mg.m$^{-3}$]')

    slope_format     = float(int(slope*100))/100
    intercept_format = float(int(intercept*100))/100
    r_val_format     = float(int(r_val*100))/100
    p_val_format     = float(int(p_val*100))/100

    if p_val_format == 0.0:
        p_val_format ='<0.001'
    else:
        p_val_format = str(p_val_format)

    maxvalx = np.nanmax([np.nanmax(SCATTER_array)])
    maxvaly = np.nanmax([np.nanmax(CHLA_array)])
    minval = 0.0

    if intercept >= 0:
        isign='+'
    else:
        isign='-'

    plt.text(maxvalx*0.05,maxvaly*1.025,'$Y$='+str(slope_format)\
            +'$X$'+isign+str(abs(intercept_format))\
            +' (r:'+str(r_val_format)\
            +', p:'+p_val_format+')',fontsize=10,color="0.5")

    fname = '/users/rsg/utils/web_visible_public_share/blo/files/AlterEco/PP_plots/'\
            + glider_tag + '_Hemsley_regression.png'

    if verbose or logging==None:
        print('Plotting to: '+fname)
    if logging:
        logging.info('Plotting to: '+fname)
    plt.savefig(fname)
    plt.close(fig1) 

    #-perform the corrections using regression----------------------------------
    # check for DCM profiles: day

    for hem_correct_file in hem_correct_files:
        print(hem_correct_file)

        # -get the variable names for comparison to config list
        nc_fid = Dataset(hem_correct_file, 'r')
        DEPTH = nc_fid.variables['DEPTH_CORRECTED'][:]
        CHLA = nc_fid.variables[chl_var][:]
        SCATTER = nc_fid.variables['BACKSCATTER_CORRECTED'][:]
        PAR = nc_fid.variables['DOWNWELLING_PAR_CORRECTED'][:]
        ZEU = nc_fid.variables['EUPHOTIC_DEPTH'][:]
        nc_fid.close()

        CORR_CHLA = CHLA.copy()

        print('Correcting profile')
        CHLA_chk = SCATTER*slope + intercept
        try:
            dd = np.where((DEPTH <= ZEU))[0]
            CORR_CHLA[dd] = np.maximum(CHLA_chk[dd],CORR_CHLA[dd])
            if logging:
                logging.info('Corrected profile: '+hem_correct_file)
            nct.write_corrected_to_file(hem_correct_file,CORR_CHLA,'CHLA_CORRECTED','TIME',define_var=False)
            print('Profile corrected!')
        except:
            print('Profile failed to corrrect')
            if logging:
                logging.info('Cannot correct profile: '+hem_correct_file)          

        if debug:
            fig = plt.figure(figsize=(10,20))
            plt.scatter((PAR-np.nanmin(PAR))/(np.nanmax(PAR)-np.nanmin(PAR)),DEPTH*-1,color='b')
            plt.plot([0,np.nanmax(CHLA)],[ZEU*-1,ZEU*-1],'k--')
            plt.scatter(CHLA,DEPTH*-1,s=300,color='g',zorder=1)
            plt.scatter(CHLA_chk,DEPTH*-1,s=200,color='0.5',zorder=2)
            plt.scatter(CORR_CHLA,DEPTH*-1,s=100,color='r',zorder=3)
            plt.ylim([np.nanmax(DEPTH)*-1.1, 0])
            plt.xlim([-0.05, max([1.1,np.nanmax(CHLA)])])
            plt.savefig('/users/rsg/utils/web_visible_public_share/blo/files/AlterEco/PP_plots/test_plots/test_'+os.path.basename(hem_correct_file).split('.')[-2])
            plt.close(fig)

#---
def fluor_correction_Bie(PROFILE,TIME,CHLA,ZEU,DEPTH,\
                         verbose=False,logging=None):
    '''
    fluor correction from Biermann et al., 2015.
    '''
    method_success = True
    CORR_CHLA = CHLA.copy()

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
        else:
            this_ZEU = ZEU
            this_DEPTH = DEPTH.copy()
            this_CORR_CHLA = CORR_CHLA.copy()

        if np.isnan(this_ZEU):
            method_success = False
            if logging == None or verbose:
                print('Cannot apply Biermann correction, no ZEU: '+str(ii))
            if logging:
                logging.info('Cannot apply Biermann correction, no ZEU: '+str(ii))
        else:
            try:
                kk = np.where(np.isnan(this_CORR_CHLA))
                dd = np.where((this_DEPTH <= this_ZEU))[0]
                max_fluor = np.nanmax(this_CORR_CHLA[dd])
                ee = np.where((this_CORR_CHLA == max_fluor))
                if this_DEPTH[np.isfinite(this_DEPTH)][0] > this_DEPTH[np.isfinite(this_DEPTH)][-1]:
                    this_CORR_CHLA[ee[0][-1]:] = max_fluor
                else:
                    this_CORR_CHLA[:ee[0][0]] = max_fluor
                this_CORR_CHLA[kk] = np.nan
            except:
                method_success = False
                if logging == None or verbose:
                    print('Cannot apply Biermann correction, NaN values: '+str(ii))
                if logging:
                    logging.info('Cannot apply Biermann correction, NaN values: '\
                             +str(ii))

        if len(np.shape(PROFILE)) == 2:
            CORR_CHLA[:,ii] = this_CORR_CHLA[:]
        else:
            CORR_CHLA = this_CORR_CHLA[:]

    return CORR_CHLA, method_success

#---
def fluor_correction_Xin(PROFILE, TIME, CHLA, MLD, DEPTH,\
                         verbose=False, logging=None):
    '''
     fluor correction from Xing et al., 2012.

     Ingests 1 or 2 dimensional profile data.
        - 1D data is a single profile.
        - 2D data is a series of contatenated profiles (usually used post 
            interpolationmonto regular depths)

     PROFILE (numpy array): the 1 or 2 dimensional dive number
     TIME (numpy array): the 1 or 2 dimensional dive time
     CHLA (numpy array): the 1 or 2 dimensional CHL
     DEPTHn(numpy array): the 1 or 2 dimensional depth record

     Returns:

     CHLA_CORR: quenching corrected CHL, dimensionally consistent with CHL
     method_success: flag to determine success. Only valid in 1D case.

     Notes:

     - Routine will accept 'downward' and 'upward' dives
     - NaNs are not replaced

    '''
    method_success = True
    CORR_CHLA = CHLA.copy()

    # make 1d variables
    if len(np.shape(PROFILE)) == 2:
        profile1d     = np.nanmean(PROFILE,axis=0)
        time1d        = np.nanmean(TIME,axis=0)
        dims          = len(time1d)
    else:
        profile1d     = PROFILE[:]
        time1d        = TIME[:]
        dims          = 1

    # loop to accommodate 2D data. 1D data only runs once.
    for ii in np.arange(0,dims):
        if verbose:
            print('profile: '+str(ii))

        if len(np.shape(PROFILE)) == 2:
            this_MLD = MLD[ii]
            this_DEPTH = DEPTH[:,ii]
            this_CORR_CHLA = CORR_CHLA[:,ii]
        else:
            this_MLD = MLD
            this_DEPTH = DEPTH.copy()
            this_CORR_CHLA = CORR_CHLA.copy()

        if np.isnan(this_MLD):
            method_success = False
            if logging == None or verbose:
                print('Cannot apply Xing correction, no MLD: '+str(ii))
            if logging:
                logging.info('Cannot apply Xing correction, no MLD: '+str(ii))
        else:
            try:
                kk = np.where(np.isnan(this_CORR_CHLA))            
                dd = np.where((this_DEPTH <= this_MLD))[0]
                max_fluor = np.nanmax(this_CORR_CHLA[dd])
                ee = np.where((this_CORR_CHLA == max_fluor))
                if this_DEPTH[np.isfinite(this_DEPTH)][0] > this_DEPTH[np.isfinite(this_DEPTH)][-1]:
                    this_CORR_CHLA[ee[0][-1]:] = max_fluor
                else:
                    this_CORR_CHLA[:ee[0][0]] = max_fluor
                this_CORR_CHLA[kk] = np.nan
            except:
                method_success = False
                if logging == None or verbose:
                     print('Cannot apply Xing correction, NaN values: '+str(ii))
                if logging:
                     logging.info('Cannot apply Xing correction, NaN values: '\
                             +str(ii))

        if len(np.shape(PROFILE)) == 2:
            CORR_CHLA[:,ii] = this_CORR_CHLA[:]
        else:
            CORR_CHLA = this_CORR_CHLA[:]

    return CORR_CHLA, method_success

#---
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
                this_CORR_CHLA[dd] = np.nanmax(tmp_CHLA[dd]/tmp_SCA[dd])*this_SCATTER_corr[dd]
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

        #if np.mod(PROFILE[0],10) == 0.0:
        #    print(PROFILE[0])
        #    plt.scatter(tmp_CHLA, this_DEPTH, s=5, c='k')            
        #    plt.scatter(this_CORR_CHLA, this_DEPTH, s=2, c='g')
        #    plt.savefig(f'test{PROFILE[0]}.png')
        #    plt.close()

    return CORR_CHLA, method_success

#-EOF---
