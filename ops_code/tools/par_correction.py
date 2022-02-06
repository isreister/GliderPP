#!/usr/bin/env python
'''
Description:    PAR correction

Version: 	v1.0 12/2017

Ver. hist:      v1.0 is current

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
import matplotlib.pyplot as plt
import logging
from . import common_tools as ct

#---
def par_correction(PROFILE,TIME,LAT,LON,DEPTH,CHL,SCATTER,PAR,TEMP,SALT,WS,\
                   glider_bathy,foutdir,gtag,to_UTC=0.0,Zthresh=-60,\
                   twilight_offset=1.0,verbose=False,logging=None,\
                   surface_depth=-20,N_smooth=2,debug=0,fsz=12,\
                   WL=np.arange(450,701),correct_time=True):
   '''
    Corrects broadband PAR to provide corrected spectral PAR
    Method ref: Hemsley et al., 2015
    
    Steps:
    1. prep variables
    2. find night and day profiles
    3. calculate Fresnel reflectances
    4. calculate E0+, boradband
   '''
   # make 1d variables
   time1d        = np.nanmean(TIME,axis=0)
   lat1d         = np.nanmean(LAT,axis=0)
   lon1d         = np.nanmean(LON,axis=0)
   
   # find necessary profile indices
   nights, days, bad, good, no_DCM_nights, day_good_PAR, shallows, deeps = \
               ct.profile_specifics(time1d,lat1d,lon1d,DEPTH[:,0],glider_bathy,\
                                    CHL,PAR,SCATTER,N_smooth,to_UTC,\
                                    twilight_offset,surface_depth,\
                                    correct_time=correct_time)

   SST = TEMP[0,:]
   SSS = SALT[0,:]

   # get Fresnel reflectances: Hemsley et al., 2015
   r_tot,solzen = ct.fresnel_refl(lat1d,lon1d,time1d,DEPTH[:,0],PAR,day_good_PAR,WS,\
                           SST,SSS,to_UTC,correct_time=correct_time)

   # take PAR from first sub-surface depth level if not available for surface
   E_0_minus = PAR[0,:]
   E_0_minus[np.isnan(E_0_minus)] = PAR[1,np.isnan(E_0_minus)]
   # get above surface (E0) irradiance: Hemsley et al., 2015
   E_0_plus = ct.get_E0(E_0_minus,r_tot)

   return E_0_plus
