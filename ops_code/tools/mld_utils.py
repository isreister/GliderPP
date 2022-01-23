from __future__ import division
import numpy as np
import scipy.io as sio
import datetime as dt
import netCDF4
import glob
import os
import re
import gsw
import linecache
import math
import numpy.ma as ma 
import matplotlib.pyplot as plt
import list_array_utils as la_utils

def findmld(pres, temp, sal, floatnumber, yesplot=False, rec_cut=10, pmax=20, \
            verbose=False, logging=None):
   '''
   Holte and Talley algorithm for finding muliple mixed layer depths

   inputs: 

      pres: pressure
      temp: potential temperature
      sal:  absolute salinity
      floatnumer: tag for the float
      yes plot: to plot?
      rec_cut: how many pressure records needed to proceed with calculation (prevents poorly constrained polynomials)
      pmax: how deep must the pressure record go?

   outputs:
      mld_var dictionary, containing:

      MIXED LATER OUTPUTS:
      mixedtp:        Algorithm MLD temp
      mixedsp:        Algorithm MLD sal
      mixeddp:        Algorithm MLD density
      mldepthptmpp:   Threshold MLD temp
      mldepthdensp:   Threshold MLD density
      gtmldp:         Gradient MLD temp
      gdmldp:         Gradient MLD temp

      TRACER OUTPUTS:
      mixedt_ta:      Mixed layer average temperature over different MLDs: Algorithm temp
      mixedd_ta:      Mixed layer average temperature over different MLDs: Algorithm density
      mldepthptmp_ta: Mixed layer average temperature over different MLDs: Threshold temp
      mldepthdens_ta: Mixed layer average temperature over different MLDs: Threshold density

      mixedt_sa:      Mixed layer average salinity over different MLDs: Algorithm temp
      mixedd_sa:      Mixed layer average salinity over different MLDs: Algorithm density
      mldepthptmp_sa: Mixed layer average salinity over different MLDs: Threshold temp
      mldepthdens_sa: Mixed layer average salinity over different MLDs: Threshold density

      mixedt_da:      Mixed layer average potential density over different MLDs: Algorithm temp
      mixedd_da:      Mixed layer average potential density over different MLDs: Algorithm temp
      mldepthptmp_da: Mixed layer average potential density over different MLDs: Threshold temp
      mldepthdens_da: Mixed layer average potential density over different MLDs: Threshold density

      INDEX OUTPUTS:
      tanalysis:      Recorded MLD step for the temperature
      sanalysis:      Recorded MLD step for the salinity
      danalysis:      Recorded MLD step for the potential density

   '''
   # The algorithm's parameters:          
   errortol = math.pow(10,-10) # Error tolerance for fitting a straight line to the mixed layer -- unitless
   max_clusters = 25           # Maximum separation for searching for clusters of possible MLDs -- dbar
   deltad = 100                # Maximum separation of temperature and temperature gradient maxima for identifying
                               # intrusions at the base of the mixed layer -- dbar
   tcutoffu = 0.5              # Upper temperature cutoff, used to initially classify profiles as winter or summer profiles -- degrees C
   tcutoffl = -0.25            # Lower temperature cutoff, used to initially classify profiles as winter or summer profiles -- degrees C
   dcutoff = -0.06             # Density cutoff, used to initially classify profiles as winter or summer profiles -- kg/m^3

   tthresh = 0.1
   sthresh = 20
   #########################################################################
   # init dict:
   mld_var = {'mixedtp'        : np.nan,
              'mixedsp'        : np.nan,
              'mixeddp'        : np.nan,
              'mldepthptmpp'   : np.nan,
              'mldepthdensp'   : np.nan,
              'gtmldp'         : np.nan,
              'gdmldp'         : np.nan,
              'mixedt_ta'      : np.nan,
              'mixedd_ta'      : np.nan,
              'mldepthptmp_ta' : np.nan,
              'mldepthdens_ta' : np.nan,
              'mixedt_sa'      : np.nan,
              'mixedd_sa'      : np.nan,
              'mldepthptmp_sa' : np.nan,
              'mldepthdens_sa' : np.nan,
              'mixedt_da'      : np.nan,
              'mixedd_da'      : np.nan,
              'mldepthptmp_da' : np.nan,
              'mldepthdens_da' : np.nan,
              'tanalysis'      : np.nan,
              'sanalysis'      : np.nan,
              'danalysis'      : np.nan}

   #########################################################################
   # consistency checks
   if np.all(np.isnan(sal)):
      if logging == None or verbose:
         print('Empty tracers, cannot make MLD calculation')
      if logging:
         logging.info('Empty tracers, cannot make MLD calculation')
      return mld_var

   if np.all(np.isnan(pres)):
      if logging == None or verbose:  
         print('Empty pressure record, cannot make MLD calculation')
      if logging:
         logging.info('Empty pressure record, cannot make MLD calculation')
      return mld_var

   if la_utils.good_vals(pres)<rec_cut:  
      if logging == None or verbose:
         print('Pressure record too short, cannot make MLD calculation')
      if logging:
         logging.info('Pressure record too short, cannot make MLD calculation')
      return mld_var

   if np.nanmax(pres)<pmax:  
      if logging == None or verbose:
         print('Pres. record too shallow, cannot make MLD calculation')
      if logging:
         logging.info('Pres. record too shallow, cannot make MLD calculation')
      return mld_var

   # remove probably bad values
   mask = np.where(  np.isfinite(pres) & (pres>0)         \
                   & np.isfinite(temp) & (temp>=tthresh)  \
                   & np.isfinite(sal)  & (sal>=sthresh)   )
 
   if mask:
      if np.shape(sal)[0] != np.shape(mask)[1]:
         if logging == None or verbose:
            print('Ignoring nan and bad values (T<'+str(tthresh)+\
                   ', S<'+str(sthresh)+')for MLD calculation')
         if logging:
            logging.info('Ignoring nan and bad values (T<'+str(tthresh)+\
                        ', S<'+str(sthresh)+')for MLD calculation')

      sal  = sal[mask]
      temp = temp[mask]
      pres = pres[mask]

   if la_utils.good_vals(pres)<rec_cut:
      if logging == None or verbose:
         print('Pressure record too short, cannot make MLD calculation')
      if logging:
         logging.info('Pressure record too short, cannot make MLD calculation')
      return mld_var  

   # check no identitical pressures: will cause /diff to fail
   _pres = np.unique(pres)
   utemp = np.zeros(np.shape(_pres))*np.nan
   usal  = np.zeros(np.shape(_pres))*np.nan
   upres = np.zeros(np.shape(_pres))*np.nan
   count = 0
   for val in _pres:
      utemp[count]=np.mean(temp[pres==val])
      usal[count] =np.mean(sal[pres==val])
      upres[count]=np.mean(pres[pres==val])
      count = count+1

   pres = np.copy(upres)
   sal  = np.copy(usal)
   temp = np.copy(utemp)

   if la_utils.good_vals(pres)<rec_cut:
      if logging == None or verbose: 
         print('Pressure record too short, cannot make MLD calculation')
      if logging:
         logging.info('Pressure record too short, cannot make MLD calculation')
      return mld_var  

   try:
      #########################################################################
      # Calculate the MLD using a threshold method with de Boyer Montegut et al's
      # criteria a density difference of .03 kg/m^3 or a temperature difference
      # of .2 degrees C.  The measurement closest to 10 dbar is used as the 
      # reference value.  The threshold MLDs are interpolated to exactly match 
      # the threshold criteria.

      # Calculate the index of the reference value
      m      = len(sal) 
      starti = np.where(np.power(pres-10, 2) == np.min(np.power(pres-10, 2)))[0][0]  
      pres   = pres[starti:m]
      sal    = sal[starti:m]
      temp   = temp[starti:m]
      starti = 0
      m      = len(sal) 

      #########################################################################
      # Calculate the potential density anomaly, with a reference pressure of 0 
      # CALL gsw.rho_CT
      pd = gsw.density.rho(sal,temp,0) - 1000
   
      #########################################################################

      # Search for the first level that exceeds the potential density threshold

      mldepthdens = m - 1
      for j in range(starti,m):
         if abs(pd[starti] - pd[j]) > 0.03: 
            mldepthdens = j
            break

      # Interpolate to exactly match the potential density threshold

      presseg = [pres[mldepthdens-1], pres[mldepthdens]]
      pdenseg = [pd[starti]- pd[mldepthdens-1], pd[starti] - pd[mldepthdens]]
      P = np.polyfit(presseg,pdenseg,1)
      presinterp = np.arange(presseg[0], presseg[1] + 0.5 ,0.5)
      pdenthreshold = np.polyval(P,presinterp)

      # The potential density threshold MLD value:
      if len(np.where(abs(pdenthreshold)<0.03)[0])== 0:
         mldepthdens = presinterp[0]
      else:
         mldepthdens = presinterp[np.where(abs(pdenthreshold)<0.03)[0][-1]]

      # Search for the first level that exceeds the temperature threshold
      mldepthptmp = m - 1
      for j in range(starti,m):
         if abs(temp[starti]-temp[j]) > 0.2: 
            mldepthptmp = j
            break

      # Interpolate to exactly match the temperature threshold
      presseg = [pres[mldepthptmp-1], pres[mldepthptmp]]
      tempseg = [temp[starti]-temp[mldepthptmp-1], temp[starti] - temp[mldepthptmp]]
      P = np.polyfit(presseg,tempseg,1)
      presinterp =  np.arange(presseg[0], presseg[1] + 0.5 ,0.5)
      tempthreshold = np.polyval(P,presinterp)

      #print presinterp, tempthreshold,np.where(abs(tempthreshold)<0.2)
      # The temperature threshold MLD value:
      if len(np.where(abs(tempthreshold)<0.2)[0]) == 0:
         mldepthptmp = presinterp[0]
      else:
         mldepthptmp = presinterp[np.where(abs(tempthreshold)<0.2)[0][-1]] 

      #########################################################################
      # Calculate the finite difference slope of the temperature, salinity and
      # density profiles

      tslope = np.diff(temp)/np.diff(pres)
      sslope = np.diff(sal)/np.diff(pres)
      dslope = np.diff(pd)/np.diff(pres)
  
      # smoothed the slope with a simple three point average using two 
      # neighboring points
      tslope_s = (tslope[:-2] + tslope[1:-1] + tslope[2:])/3
      sslope_s = (sslope[:-2] + sslope[1:-1] + sslope[2:])/3
      dslope_s = (dslope[:-2] + dslope[1:-1] + dslope[2:])/3
      ms = len(tslope_s)

      #########################################################################

      # Calculate the MLD using a gradient method.  Following Dong et al., the gradient 
      # criteria are .0005 kg/m^3/dbar and .005 degrees C/dbar.  If the criteria 
      # are not met, the algorithm uses the temperature or density gradient extreme.
      k = np.where(np.abs(dslope) > 0.0005)[0] 
      if len(k) > 0:
         gdmld = k[0] + 1
      else:
         gdmld = np.where(abs(dslope)==max(abs(dslope)))[0][0] + 1
   
      l = np.where(np.abs(tslope) > 0.005)[0]
      if len(l) > 0:
         gtmld = l[0] + 1
      else:
         gtmld = np.where(abs(tslope)==max(abs(tslope)))[0][0] + 1

      ######################################################################### 
      # Fit a straight line to the profile's mixed layer. Starting at the depth 
      # closest to 10 dbar, use the first two points of the profile to calculate 
      # a straight-line least-squares fit to the mixed layer.  Increase the depth
      # and the number of points used in the fit until the bottom of the 
      # profile. For each fit the error is calculated by summing the squared 
      # difference between the fit and the profile over the depth of the fit.
      # This step aims to accurately capture the slope of the mixed layer, and
      # not its depth.  

      errort = list([0])
      errors = list([0])
      errord = list([0])
      for j in range(starti+2, m+1):
         # Fit line to temperature and calculate error
         P = np.polyfit(pres[starti:j], temp[starti:j], 1)
         ltempfit = np.polyval(P, pres[starti:j])
         errort.append(np.dot((temp[starti:j] - ltempfit).T, (temp[starti:j] - ltempfit)))

         # Fit line to salinity and calculate error
         P = np.polyfit(pres[starti:j], sal[starti:j], 1)
         lsalfit = np.polyval(P, pres[starti:j])
         # print "%+2.40f\n" % lsalfit[0]
      
         errors.append(np.dot((sal[starti:j] - lsalfit).T, (sal[starti:j] - lsalfit)))

         # Fit line to potential density and calculate error
         P = np.polyfit(pres[starti:j], pd[starti:j], 1)
         ldenfit = np.polyval(P, pres[starti:j])
         errord.append(np.dot((pd[starti:j] - ldenfit).T, (pd[starti:j] - ldenfit)))

      errort = np.asarray(errort)
      errors = np.asarray(errors)
      errord = np.asarray(errord)

      #########################################################################

      # Normalize the errors
      errort = errort/np.sum(errort) 
      errors = errors/np.sum(errors)
      errord = errord/np.sum(errord)

      # Find deepest index with allowable error
      upperlayert = np.where(errort < errortol)[0][-1]      
      upperlayers = np.where(errors < errortol)[0][-1]
      upperlayerd = np.where(errord < errortol)[0][-1]

      #########################################################################
      # Ext the mixed layer fit to the depth of the profile

      P = np.polyfit(pres[starti:upperlayert+1], temp[starti:upperlayert+1], 1)
      ltempfit = np.polyval(P, pres)

      P = np.polyfit(pres[starti:upperlayers+1], sal[starti:upperlayers+1], 1);
      lsalfit = np.polyval(P, pres)

      P = np.polyfit(pres[starti:upperlayerd+1], pd[starti:upperlayerd+1], 1);
      ldenfit = np.polyval(P, pres)

      #########################################################################   
      # Fit a straight line to the thermocline and ext the fit to the depth 
      # of the profile.  The extreme value of each profile's smoothed gradient 
      # (calculated in lines 82-84) is used to find the center of the 
      # thermocline.

      dtdzmax = np.where(np.abs(tslope_s) == np.max(np.abs(tslope_s)))[0][-1] + 1
      P = np.polyfit(pres[dtdzmax-1:dtdzmax+2], temp[dtdzmax-1:dtdzmax+2], 1)
      dtminfit = np.polyval(P, pres)

      dsdzmax = np.where(np.abs(sslope_s) == np.max(np.abs(sslope_s)))[0][-1] + 1
      P = np.polyfit(pres[dsdzmax-1:dsdzmax+2], sal[dsdzmax-1:dsdzmax+2], 1)
      dsmaxfit = np.polyval(P,pres)

      dddzmax = np.where(abs(dslope_s) == np.max(np.abs(dslope_s)))[0][-1] + 1
      P = np.polyfit(pres[dddzmax-1:dddzmax+2], pd[dddzmax-1:dddzmax+2], 1)
      ddmaxfit = np.polyval(P, pres)

      ######################################################################### 
      # Calculate one set of possible MLD values by finding the intersection 
      # points of the mixed layer and thermocline fits.  If the fits do not
      # intersect, the MLD value is set to 0.

      upperdtmin = np.where(np.abs(dtminfit-ltempfit) == np.min(np.abs(dtminfit-ltempfit)))[0][-1]
      if np.all(dtminfit-ltempfit > 0):
         upperdtmin = -1
  
      if np.all(-dtminfit+ltempfit > 0):
         upperdtmin = -1

      upperdsmax = np.where(np.abs(dsmaxfit-lsalfit) == np.min(np.abs(dsmaxfit-lsalfit)))[0][-1]
      if np.all(-dsmaxfit+lsalfit > 0):
         upperdsmax = -1
   
      if np.all(dsmaxfit-lsalfit > 0):
         upperdsmax = -1

      upperddmax = np.where(np.abs(ddmaxfit-ldenfit) == np.min(np.abs(ddmaxfit-ldenfit)))[0][-1]
      if np.all(ddmaxfit-ldenfit > 0):
         upperddmax = -1
   
      if np.all(-ddmaxfit+ldenfit > 0):
         upperddmax = -1

      #########################################################################
      # Calculate the remaining possible MLD values:  

      # The maxima or minima of the temperature, salinity, and potential density
      # profiles
      tmax = np.where(temp == max(temp))[0][-1]
      smin = np.where(sal == min(sal))[0][-1]
      dmin = np.where(pd == min(pd))[0][-1]

      # The gradient MLD values
      dtmax = gtmld
      dsmin = np.where(np.abs(sslope_s) == np.max(np.abs(sslope_s)))[0][-1] + 1
      ddmin = gdmld

      # Sometimes subsurface temperature or salinity intrusions exist at the base 
      # of the mixed layer.  For temperature, these intrusions are 
      # characterized by subsurface temperature maxima located near temperature 
      # gradient maxima. If the two maxima are separated by less than deltad, 
      # the possible MLD value is recorded in dtandtmax.
      dtmax2 = np.where(tslope_s == max(tslope_s))[0][-1] + 1
      if np.abs(pres[dtmax2] - pres[tmax]) < deltad:
         dtandtmax = min(dtmax2, tmax)
      else:
         dtandtmax = -1
   
      dsmin2 = np.where(sslope_s == min(sslope_s))[0][-1] + 1
      if np.abs(pres[dsmin2]-pres[smin]) < deltad:
         dsandsmin = min(dsmin2, smin)
      else:
         dsandsmin = -1

      #########################################################################
      # To determine if the profile resembles a typical winter or summer profile,
      # the temperature change across the thermocline, tdiff, is calculated and
      # compared to the temperature cutoff. tdiff is calculated as the 
      # temperature change between the intersection of the mixed layer and thermocline fits and a 
      # point two depth indexes deeper.  If upperdtmin is set to 0 or at the
      # bottom of the profile, the points from the thermocline fit are used
      # to evaluate tdiff.  
      if upperdtmin > -1 and upperdtmin < m-3:
         tdiff = temp[upperdtmin] - temp[upperdtmin+2]
      else:
         tdiff = temp[dtdzmax-1] - temp[dtdzmax+1]
   
      # tdiff is compared to the temperature cutoffs
      if tdiff > tcutoffl and tdiff < tcutoffu:
         testt = 1 # winter
      else:
         testt = 0 # summer

      # For salinity and potential density profiles, the potential density 
      # change across the pycnocline is calculated in a similar manner and 
      # compared to a potential density cutoff.    
      if upperddmax > -1 and upperddmax < m-3:
         ddiff = pd[upperddmax] - pd[upperddmax+2]
      else:
         ddiff = pd[dddzmax-1] - pd[dddzmax+1]
   
      testd = testt
      if ddiff > dcutoff and tdiff > tcutoffu:
         testd = 1 # winter
      if ddiff > dcutoff and tdiff < tcutoffl:
         testd = 0 # summer
    
      #########################################################################
      # Temperature Algorithm
   
      # Convert the possible temperature MLDs from index to pressure
      if upperdtmin > -1:
         upperdtmin = pres[upperdtmin]
   
      tmax = pres[tmax]

      if dtandtmax > -1:
         dtandtmax = pres[dtandtmax]
      else:
         dtandtmax = -1
   
      dtmax = pres[dtmax]

      #TODO: until here
      #########################################################################

      # Select the temperature MLD.  See the paper for a description of the
      # steps.
      if testt == 0: 
         mixedt = upperdtmin
         analysis_t = 1
         if tdiff < 0 and mixedt > mldepthptmp:
            mixedt = mldepthptmp
            analysis_t = 2  

         if mixedt > mldepthptmp:
            if tmax < mldepthptmp and tmax > max_clusters: 
               mixedt = tmax
               analysis_t = 3
            else:
               mixedt = mldepthptmp
               analysis_t = 4      
      else:
         if abs(upperdtmin-mldepthptmp) < max_clusters and abs(dtandtmax-mldepthptmp) > max_clusters and upperdtmin<dtandtmax:
            mixedt = upperdtmin
            analysis_t = 5
         else:
            if dtandtmax > pres[0] + max_clusters:
               mixedt = dtandtmax
               analysis_t = 6 
               a = np.asarray([abs(dtmax-upperdtmin), abs(dtmax-mldepthptmp), abs(mldepthptmp-upperdtmin)])
               if sum(a < max_clusters) > 1:
                  mixedt = upperdtmin
                  analysis_t = 7                
               if mixedt > mldepthptmp:
                  mixedt = mldepthptmp
                  analysis_t = 8
            else:
               if upperdtmin-mldepthptmp < max_clusters:
                  mixedt = upperdtmin
                  analysis_t = 9
               else:
                  mixedt = dtmax
                  analysis_t = 10
                  if mixedt > mldepthptmp:
                     mixedt = mldepthptmp
                     analysis_t = 11
         if mixedt == 0 and abs(mixedt-mldepthptmp)>max_clusters:
            mixedt = tmax 
            analysis_t = 12
            if tmax == pres[0]:
               mixedt = mldepthptmp
               analysis_t = 13
            if tmax > mldepthptmp:
               mixedt = mldepthptmp
               analysis_t = 14

      ##########################################################################
      # Salinity Algorithm  

      # Convert the possible salinity MLDs from index to pressure
      if upperdsmax > -1:
         upperdsmax = pres[upperdsmax]
   
      dsmin = pres[dsmin]
      if dsandsmin > -1:
         dsandsmin = pres[dsandsmin]
      else:
         dsandsmin = -1

      # Select the salinity MLD
      if testd == 0:
         mixeds = upperdsmax  
         analysis_s = 1
         if mixeds - mldepthdens > max_clusters:
            mixeds = mldepthdens
            analysis_s = 2
         if upperdsmax-dsmin < 0 and mldepthdens-dsmin > 0:
            mixeds = dsmin
            analysis_s = 3
         if upperdsmax-dsandsmin < max_clusters and dsandsmin > max_clusters:
            mixeds = dsandsmin
            analysis_s = 4
         if abs(mldepthdens-dsandsmin) < max_clusters and dsandsmin > max_clusters:
            mixeds = dsandsmin
            analysis_s = 5
         if mixedt-mldepthdens<0 and abs(mixedt-mldepthdens) < max_clusters:
            mixeds = mixedt  
            analysis_s = 6
            if abs(mixedt-upperdsmax) < max_clusters and upperdsmax-mldepthdens < 0:
               mixeds = upperdsmax 
               analysis_s = 7
         if abs(mixedt-mldepthdens) < abs(mixeds-mldepthdens):
            if mixedt > mldepthdens:
               mixeds = mldepthdens
               analysis_s = 8
      else:
         if dsandsmin > max_clusters:
            mixeds = dsandsmin
            analysis_s = 9
            if mixeds > mldepthdens:
               mixeds = mldepthdens
               analysis_s = 10
         else:
            if dsmin < mldepthdens:
               mixeds = dsmin
               analysis_s = 11
               if upperdsmax < mixeds:
                  mixeds = upperdsmax
                  analysis_s = 12
            else:
               mixeds = mldepthdens  
               analysis_s = 13
               if upperdsmax < mixeds:
                  mixeds = upperdsmax
                  analysis_s = 14
               if mixeds == 1: 
                  mixeds = dsmin
                  analysis_s = 15
               if dsmin > mldepthdens:
                  mixeds = mldepthdens
                  analysis_s = 16

      #########################################################################
      # Potential Density Algorithm.

      # Convert the possible potential density MLDs from index to pressure
      if upperddmax > -1:
         upperddmax = pres[upperddmax] 
      dmin = pres[dmin]
      ddmin = pres[ddmin]
    
      # Select the potential density MLD
      if testd == 0:
         mixedd = upperddmax    
         analysis_d = 1
         if mixedd > mldepthdens:
            mixedd = mldepthdens
            analysis_d = 2
         aa = np.asarray([abs(mixeds-mixedt), abs(upperddmax-mixedt), abs(mixeds-upperddmax)])
         if sum(aa < max_clusters) > 1:
            mixedd = upperddmax
            analysis_d = 3                
         if abs(mixeds - mldepthdens) < max_clusters and mixeds != mldepthdens:
            if mldepthdens < mixeds:
               mixedd = mldepthdens
               analysis_d = 4            
            else:
               mixedd = mixeds
               analysis_d = 5
            if upperddmax == mldepthdens:
               mixedd =  upperddmax
               analysis_d = 6
         if mixedd > ddmin and abs(ddmin-mixedt) < abs(mixedd-mixedt):
            mixedd = ddmin
            analysis_d = 7
      else:
         mixedd = mldepthdens
         analysis_d = 8
         if mldepthptmp < mixedd:
            mixedd = mldepthptmp
            analysis_d = 9
         if upperddmax < mldepthdens and upperddmax > max_clusters:
            mixedd =  upperddmax
            analysis_d = 10
         if dtandtmax > max_clusters and dtandtmax < mldepthdens:
            mixedd = dtandtmax
            analysis_d = 11
            if abs(tmax-upperddmax) < abs(dtandtmax-upperddmax):
               mixedd = tmax
               analysis_d = 12
            if abs(mixeds - mldepthdens) < max_clusters and mixeds < mldepthdens:
               mixedd = min(mldepthdens,mixeds)
               analysis_d = 13
         if abs(mixedt-mixeds) < max_clusters:
            if abs(min(mixedt,mixeds)-mixedd) > max_clusters:
               mixedd = min(mixedt,mixeds)
               analysis_d = 14
         if mixedd>ddmin and abs(ddmin-mixedt) < abs(mixedd-mixedt):
            mixedd = ddmin
            analysis_d = 15
         if upperddmax == upperdsmax and abs(upperdsmax-mldepthdens) < max_clusters:
            mixedd = upperddmax
            analysis_d = 16
         if mixedt == dmin: 
            mixedd = dmin
            analysis_d = 17
       
      #########################################################################
      # Output variables

      # Algorithm mlds
      mixedtp = mixedt
      mixedsp = mixeds
      mixeddp = mixedd

      # Theshold method mlds
      mldepthdensp = mldepthdens
      mldepthptmpp = mldepthptmp

      # Gradient method mlds
      gtmldp = pres[gtmld]
      gdmldp = pres[gdmld]

      # Find the various methods' MLD indices for computing mixed layer average 
      # properties

      pres = np.ma.masked_array(pres, np.isnan(pres))
      temp = np.ma.masked_array(temp, np.isnan(temp))
      pd = np.ma.masked_array(pd, np.isnan(pd))

      ta = np.where(pres<mixedt)[0]
      da = np.where(pres<mixedd)[0]
      tt = np.where(pres<mldepthptmp)[0]
      dt = np.where(pres<mldepthdens)[0]

      if len(da) == 0:
         mixedd_ta = 9999
         mixedd_sa = 9999
         mixedd_da = 9999
      else:
         mixedd_ta = np.mean(temp[da])
         mixedd_sa = np.mean(sal[da])
         mixedd_da = np.mean(pd[da])
           
      mixedt_ta = np.mean(temp[ta])   
      mldepthdens_ta = np.mean(temp[dt])
      mldepthptmp_ta = np.mean(temp[tt])

      # Mixed layer average salinity over different MLDs
      mixedt_sa = np.mean(sal[ta])

      mldepthdens_sa = np.mean(sal[dt])
      mldepthptmp_sa = np.mean(sal[tt])

      # Mixed layer average potential density over different MLDs
      mixedt_da = np.mean(pd[ta])

      mldepthdens_da = np.mean(pd[dt])
      mldepthptmp_da = np.mean(pd[tt])

      # Record which step selected the MLD for the temperature, salinity, and
      # potential density profiles
      tanalysis = analysis_t
      sanalysis = analysis_s
      danalysis = analysis_d

      ###########################################################################
      # Plot the individual temperature, salinity, and potential density profiles, 
      # as well as the mixed layer and thermocline fits and the various possible 
      # MLD measures.  Turn this feature on in the 'EDIT' section of get_mld.m
      if yesplot:
         mintemp = min(temp)
         maxtemp = max(temp)
         minsal = min(sal)
         maxsal = max(sal)
         minpden = min(pd)
         maxpden = max(pd)  

         ta = max(ta)
         da = max(da)
         tt = max(tt)
         dt = max(dt)
         tmaxi = np.where(pres==tmax)[0]
         dtmaxi = np.where(pres==dtmax)[0]
         if upperdtmin > 0:
            upperdtmini = np.where(pres==upperdtmin)[0]
         else:
            upperdtmini = len(pres)

         f, axarr = plt.subplots(1, 3)
         axarr[0].plot(temp, pres, 'ko', markersize=6)
         #plot(temp(:),pres(:),'ko','MarkerFaceColor','k','MarkerSize',6)
         #hold on 
         tempchoice = np.arange(0, 50.5, 0.5)
         preschoice = mixedtp * np.ones(len(tempchoice))
         axarr[0].plot(tempchoice, preschoice, 'k',  linewidth = 4)
         axarr[0].plot(ltempfit, pres, 'k', dtminfit, pres, '--k', linewidth = 2)
         axarr[0].plot(temp[tt], mldepthptmp, 's', markerfacecolor = 'g', markeredgecolor ='k', markersize=16)           #markerfacecolor = 'g', markeredgecolor ='k',
         axarr[0].plot(temp[gtmld], pres[gtmld], '>', markerfacecolor = 'g', markeredgecolor ='k', markersize=16)              
         axarr[0].plot(temp[tmaxi],tmax,'o', markerfacecolor = 'c', markeredgecolor ='k',markersize=12)
         axarr[0].plot(temp[dtmax2], pres[dtmax2], 's', markerfacecolor = 'c', markeredgecolor ='k',markersize=12)
         axarr[0].plot(temp[dtmaxi], dtmax, 'o', markerfacecolor = 'y', markeredgecolor ='k',markersize=12)
         axarr[0].plot(temp[upperdtmini], upperdtmin, 'o', markerfacecolor = 'b', markeredgecolor ='k', markersize=12)
         #set(gca, 'YDir','reverse','XAxisLocation','top')
         axarr[0].invert_yaxis()
         axarr[0].xaxis.tick_top()
         axarr[0].set_xlabel('Temperature (^oC)', fontsize = 14)
         axarr[0].set_ylabel('Pressure (dbar)', fontsize = 14)
         axarr[0].axis([mintemp, maxtemp, 0, 500])
         axarr[0].grid()

         if upperdsmax > 0:
            upperdsmaxi = np.where(pres==upperdsmax)[0]
         else:
            upperdsmaxi = len(pres)
         dsmini = np.where(pres==dsmin)[0]

         axarr[1].plot(sal,pres,'ko', markerfacecolor = 'k',markersize=6)
         preschoice = mixedsp * np.ones(len(tempchoice))
         axarr[1].plot(tempchoice, preschoice, 'k', linewidth = 4)
         axarr[1].plot(lsalfit, pres, 'k', dsmaxfit, pres, '--k', linewidth = 2)
         axarr[1].plot(sal[tt], mldepthptmp, 's', markerfacecolor = 'g', markeredgecolor ='k',markersize=16)
         axarr[1].plot(sal[dt], mldepthdens, 's', markerfacecolor = 'r', markeredgecolor ='k',markersize=16)       
         axarr[1].plot(sal[gtmld], pres[gtmld], '>', markerfacecolor = 'g', markeredgecolor ='k',markersize=16)              
         axarr[1].plot(sal[gdmld], pres[gdmld], '>', markerfacecolor = 'r', markeredgecolor ='k',markersize=16)                 
         axarr[1].plot(sal[upperdsmaxi], upperdsmax, 'o', markerfacecolor = 'b', markeredgecolor ='k',markersize=12)
         axarr[1].plot(sal[smin], pres[smin],'o', markerfacecolor = 'c', markeredgecolor ='k',markersize=12)
         axarr[1].plot(sal[dsmini], dsmin, 'o',markerfacecolor = 'y', markeredgecolor ='k', markersize=12)
         axarr[1].plot(temp[dsmin2], pres[dsmin2], 's', markerfacecolor = 'c', markeredgecolor ='k',markersize=12)    
         #axarr[1].set(gca, 'YDir','reverse','XAxisLocation','top') 
         axarr[1].invert_yaxis()
         axarr[1].xaxis.tick_top()
         axarr[1].grid()
     
         axarr[1].set_xlabel('Salinity (PSU)', fontsize = 14)
         axarr[1].axis([minsal, maxsal, 0, 500])
         #hold off

         if upperddmax > 0:
            upperddmaxi = np.where(pres==upperddmax)[0]
         else:
            upperddmaxi = len(pres)
             
         dmini = np.where(pres==dmin)[0]
         ddmini = np.where(pres==ddmin)[0]

         axarr[2].plot(pd,pres,'ko', markerfacecolor = 'k',markersize=6)
         #hold on
         preschoice = mixeddp * np.ones(len(tempchoice))
         axarr[2].plot(tempchoice, preschoice, 'k', linewidth = 4)
         axarr[2].plot(ldenfit, pres, 'k', ddmaxfit, pres, '--k', linewidth = 2)
         axarr[2].plot(pd[tt], mldepthptmp, 's', markerfacecolor = 'g', markeredgecolor ='k',markersize=16)
         axarr[2].plot(pd[dt], mldepthdens, 's', markerfacecolor = 'r', markeredgecolor ='k',markersize=16)
         axarr[2].plot(pd[gtmld], pres[gtmld], '>', markerfacecolor = 'g', markeredgecolor ='k',markersize=16)      
         axarr[2].plot(pd[gdmld], pres[gdmld], '>', markerfacecolor = 'r', markeredgecolor ='k',markersize=16)           
         axarr[2].plot(pd[upperddmaxi], upperddmax, 'o', markerfacecolor = 'b', markeredgecolor ='k',markersize=12)
         axarr[2].plot(pd[dmini], dmin, 'o', markerfacecolor = 'c', markeredgecolor ='k',markersize=12)
         axarr[2].plot(pd[ddmini], ddmin, 'o', markerfacecolor = 'y', markeredgecolor ='k',markersize=12)
         #axarr[2].set(gca, 'YDir','reverse','XAxisLocation','top')
         axarr[2].invert_yaxis()
         axarr[2].xaxis.tick_top()
         axarr[2].grid()
         axarr[2].set_xlabel('Density (sigma_theta)', fontsize = 14)
         axarr[2].axis([minpden, maxpden, 0, 500])
   
         titlename = ' profile  of float ' + str(floatnumber)
         f.suptitle(titlename, fontsize=20)
         plt.show()                  #TODO

      mld_var = {'mixedtp'        : mixedtp,
                 'mixedsp'        : mixedsp,
                 'mixeddp'        : mixeddp,
                 'mldepthptmpp'   : mldepthptmpp,
                 'mldepthdensp'   : mldepthdensp,
                 'gtmldp'         : gtmldp,
                 'gdmldp'         : gdmldp,
                 'mixedt_ta'      : mixedt_ta,
                 'mixedd_ta'      : mixedd_ta,
                 'mldepthptmp_ta' : mldepthptmp_ta,
                 'mldepthdens_ta' : mldepthdens_ta,
                 'mixedt_sa'      : mixedt_sa,
                 'mixedd_sa'      : mixedd_sa,
                 'mldepthptmp_sa' : mldepthptmp_sa,
                 'mldepthdens_sa' : mldepthdens_sa,
                 'mixedt_da'      : mixedt_da,
                 'mixedd_da'      : mixedd_da,
                 'mldepthptmp_da' : mldepthptmp_da,
                 'mldepthdens_da' : mldepthdens_da,
                 'tanalysis'      : tanalysis,
                 'sanalysis'      : sanalysis,
                 'danalysis'      : danalysis}
      return mld_var

   except:
      if logging == None or verbose:
         print('Failed to calulate MLD; bailing with nan values')
      if logging:
         logging.info('Failed to calulate MLD; bailing with nan values')

      mld_var = {'mixedtp'        : np.nan,
                 'mixedsp'        : np.nan,
                 'mixeddp'        : np.nan,
                 'mldepthptmpp'   : np.nan,
                 'mldepthdensp'   : np.nan,
                 'gtmldp'         : np.nan,
                 'gdmldp'         : np.nan,
                 'mixedt_ta'      : np.nan,
                 'mixedd_ta'      : np.nan,
                 'mldepthptmp_ta' : np.nan,
                 'mldepthdens_ta' : np.nan,
                 'mixedt_sa'      : np.nan,
                 'mixedd_sa'      : np.nan,
                 'mldepthptmp_sa' : np.nan,
                 'mldepthdens_sa' : np.nan,
                 'mixedt_da'      : np.nan,
                 'mixedd_da'      : np.nan,
                 'mldepthptmp_da' : np.nan,
                 'mldepthdens_da' : np.nan,
                 'tanalysis'      : np.nan,
                 'sanalysis'      : np.nan,
                 'danalysis'      : np.nan}
      return mld_var

