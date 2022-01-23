#!/usr/bin/env python
'''
Description:    Re-scales GC90 PAR by subsurface broadband glider integral and
                projects with depth

Version: 	v1.0 12/2017

Ver. hist:

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
import numpy as np
from netCDF4 import Dataset
import argparse
import glob
import warnings
warnings.filterwarnings("ignore")
import fnmatch
import logging
import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import gridspec
from mpl_toolkits.basemap import Basemap
from scipy.interpolate import interp1d
from scipy.integrate import simps

#- my functions
sys.path.append('/users/rsg/blo/Tools/Py_Tools/cmocean-master')
from cmocean import cm as ocm

#-functions---------------------------------------------------------------------
def RMSE(meas,mod):
   '''
    Calculate root mean squared error from good values
   '''
   good_vals = np.where((np.isfinite(meas)) \
                       & (np.isfinite(mod)))[0]
   good_meas = meas[good_vals]
   good_mod  = mod[good_vals]
   return (np.sum((good_meas-good_mod)**2)/len(good_meas))**0.5

def spectral_par_depth(E0_wv,wv,depths,CHL,scaling,Measured_PAR,\
                       a_wv,b_wv,e_wv,X_wv):

   # set up arrays for integral
   E_depth_wv    = np.ones([len(depths),len(wv)])*np.nan

   # calculate attenuation coefficient of water alone: not depth dependant
   Kw_wv = a_wv + 0.5*b_wv

   # calculate attentuation
   # FIXME: I HAVE CONCERNS HERE ABOUT IN WATER CONSTITUENTS!!!
   for zz in np.arange(0,len(depths)):
      # calculate attenuation coefficient of CHL: depth dependant
      Kc_wv = X_wv*(CHL[zz]*scaling)**e_wv
      K_tot = Kw_wv+Kc_wv
      if zz==0:
         E_depth_wv[zz,:] = E0_wv*\
                            np.exp(-K_tot*(depths[0]))
      else:
         E_depth_wv[zz,:] = E_depth_wv[zz-1,:]*\
                            np.exp(-K_tot*(depths[zz]-depths[zz-1]))

   # recalculate broadband par (integrate E_depth_wv across all wavelengths)
   wv_diff      = np.nanmean(wv[1:]-wv[0:-1])
   Modelled_PAR = np.nansum(E_depth_wv*wv_diff,axis=1)
   rmse         = RMSE(Measured_PAR,Modelled_PAR)
   return Modelled_PAR,rmse

def write_scale_factors(CHL_scale,Ed_scale,scale_file,logging,verbose=0):
   if verbose:
      print('Writing scale file: '+scale_file)
   logging.info('Writing scale file: '+scale_file)
   with open(scale_file,"w") as this_file:
      this_file.write('CHL_scale '+str(CHL_scale)+'\n')
      this_file.write('Ed_scale '+str(Ed_scale))
   logging.info('Written scale file')
   os.chmod(scale_file, 0o777)

#-default parameters------------------------------------------------------------
DEFAULT_ROOT_DIR   = '/data/datasets/Projects/AlterEco/Glider_data/Oman/'
DEFAULT_LOG_PATH   = '/home/ben/shared/Linux_desktop/local1/data/scratch/blo/AlterEco/operational_code/logs/'
DEFAULT_OUT_DIR    = '/home/ben/shared/Linux_desktop/local1/data/scratch/blo/AlterEco/operational_code/plots/'
DEFAULT_GTAG       = 'glider'
DEFAULT_FILE_MATCH = 'chl_Hem'

#-args--------------------------------------------------------------------------
parser = argparse.ArgumentParser()
#-input vars--------------------------------------------------------------------
parser.add_argument('-d', '--root_dir', type=str,\
                    default = DEFAULT_ROOT_DIR,\
                    help = 'Glider root directory')
parser.add_argument('-o', '--output_dir', type=str,\
                    default = DEFAULT_OUT_DIR,\
                    help = 'Plot output directory')
parser.add_argument('-ed', '--ed', type=str,\
                    help = 'Spectral GC90 PAR file')
parser.add_argument('-chl', '--chl', type=str,\
                    help = 'Chl file')
parser.add_argument('-par', '--par', type=str,\
                    help = 'PAR file')
parser.add_argument('-e0', '--e0', type=str,\
                    help = 'Broadband PAR E0_plus from glider')
parser.add_argument('-t', '--time', type=str,\
                    help = 'Glider dive time')
parser.add_argument('-l', '--log_path', type=str,\
                    default = DEFAULT_LOG_PATH,\
                    help = 'log file output path')
parser.add_argument('-g', '--glider_tag', type=str,\
                    default = DEFAULT_GTAG,\
                    help = 'Glider tag')
parser.add_argument('-v', '--verbose',\
                    action = 'store_true')
parser.add_argument('-m', '--match_str', type=str,\
                    default = DEFAULT_FILE_MATCH,\
                    help = 'Glider file match pattern')
parser.add_argument('-w', '--standard_wavs', type=int,\
                    default = 1)
#-input vars end----------------------------------------------------------------
args   = parser.parse_args()

#-main--------------------------------------------------------------------------
if __name__ == "__main__":
   # -preliminary stuff---------------------------------------------------------
   debug    = 0
   verbose  = args.verbose
   logfile  = args.log_path+"project_spectral_PAR_"+\
              datetime.datetime.now().strftime('%Y%m%d_%H%M')+".log"
   prof_num = args.ed.split('.')[0].split('_')[-1] 
   fsz      = 12

   OUT_DIR = os.path.join(args.output_dir,args.glider_tag,'corrections')
   sc_file = args.chl.replace(args.match_str,'scale')

   # -set file logger-----------------------------------------------------------
   try:
      if os.path.exists(logfile):
         os.chmod(logfile,0o777)
         os.remove(logfile)
      print("logging to: "+logfile)
      logging.basicConfig(filename=logfile,level=logging.DEBUG)
      os.chmod(logfile,0o777)
   except:
      print("Failed to set logger")
      sys.exit()

   if verbose:
      print("RUNNING: WARNINGS ARE SUPPRESSED")

   if not os.path.exists(OUT_DIR):
       os.makedirs(os.path.dirname(OUT_DIR))
       os.chmod(os.path.dirname(OUT_DIR),0o777)
       os.makedirs(OUT_DIR)
       os.chmod(OUT_DIR,0o777)

   # ensure files can be read
   os.chmod(args.chl, 0o777)
   os.chmod(args.par, 0o777)
   os.chmod(args.ed, 0o777)

   # get depths, Chl, PAR from files
   vals = np.genfromtxt(args.chl, dtype=float)
   if len(np.shape(vals)) == 1:
       depths = vals[1]
   else:
       depths = vals[:,1]

   if len(np.shape(vals)) == 1:
       CHL_uncorr = vals[2]
   else:
       CHL_uncorr = vals[:,2]

   vals = np.genfromtxt(args.par, dtype=float)
   if len(np.shape(vals)) == 1:
       PAR_meas = vals[2]
   else:
      PAR_meas = vals[:,2]
   
   # prepare to read values from Ed file
   file_values = np.genfromtxt(args.ed, dtype=("|S10", float, float, float))
   T_off       = np.ones(np.shape(file_values))*np.nan
   wv          = np.ones(np.shape(file_values))*np.nan
   Ed          = np.ones(np.shape(file_values))*np.nan  #W.m-2.nm-1

   hour_glider,minute_glider = args.time.split(':')
   T_glider      = datetime.datetime(2000,1,1,int(hour_glider),int(minute_glider))

   # read values
   for ii in np.arange(0,len(file_values)):
      hour, minute  = file_values[ii][0].decode("utf-8").split(':')
      hour_glider,minute_glider = args.time.split(':')
      T_profile     = datetime.datetime(2000,1,1,int(hour),int(minute))
      T_off[ii]     = abs(float((T_profile-T_glider).total_seconds()))
      wv[ii]        = file_values[ii][1]
      Ed[ii]        = file_values[ii][2]

   # select nearest profile in time
   tt = np.where((T_off == np.nanmin(T_off)))
   wv_selected = wv[tt]
   Ed_selected = Ed[tt]

   # calc integrated Ed for this time
   wv_diff     = np.nanmean(wv_selected[1:]-wv_selected[0:-1])
   Ed_total    = simps(Ed_selected,dx=5)
   
   # rescale 0- value; use modelled PAR where no in situ exists
   if float(args.e0) <= 0.0 or np.isnan(float(args.e0)):            
      if verbose:
         print('Bad glider PAR(=0), scale factor set to 1.0.')
      logging.info('Bad glider PAR(=0), scale factor set to 1.0.')
      Ed_scaling  = 1.0
   else:
      Ed_scaling  = float(args.e0)/Ed_total
   Ed_new      = Ed_selected*Ed_scaling
 
   # plot if debug
   if debug:
      fig0 = plt.figure(figsize=(10,10), dpi=300)
      p1, = plt.plot(wv_selected,Ed_selected,'k')
      p2, = plt.plot(wv_selected,Ed_new,'r--')

      plt.xlabel('Wavelength [nm]',fontsize=fsz)
      plt.ylabel('PAR [W.m$^{-2}$]',fontsize=fsz)
      plt.xlim([np.nanmin(wv_selected),np.nanmax(wv_selected)])

      plt.ylim([0.0,np.nanmax([np.nanmax(Ed_selected),np.nanmax(Ed_new)])])

      leg = plt.legend([p1,p2],['Ed spectral model', \
                    'Ed scaled to glider PAR: '+str(Ed_scaling)],\
                    fontsize=fsz, loc="lower right") 

      fname=OUT_DIR+'/'+args.glider_tag+'_scaled_Ed_'+prof_num+'.png'
      plt.savefig(fname)
      plt.close(fig0)

   #depth project....using Morel and Maritorena, 2001.
   rmse=1e20
   if debug:
      fig0 = plt.figure(figsize=(10,10), dpi=300)

   # flip records if shallowest depth is not first:
   good_depths = depths[np.isfinite(depths)]
   if abs(good_depths[0]) > abs(good_depths[-1]):
       PAR_meas = PAR_meas[::-1]
       CHL_uncorr = CHL_uncorr[::-1]
       depths = depths[::-1]

   good_PAR = PAR_meas[np.isfinite(PAR_meas)]

   try:
      if good_PAR[-1] >= good_PAR[0] or np.nanmax(PAR_meas) < 1 or args.e0 < 0.0:
         logging.info('PAR profile is bad/night, scale set to 1.0')
         if verbose:
            print('PAR profile is bad/night, scale set to 1.0')
         CHL_scaling_final = 1.0
         Ed_scaling = 1.0
         Mod_PAR_final     = PAR_meas.copy()
         if debug:
            p2,  = plt.plot(PAR_meas,depths*-1,'r',linewidth=0.25)
      else:
         if args.standard_wavs == 1:
            # uses interp values for 400-700 (saves time!)
            a_wv = np.asarray([0.0171, 0.01665, 0.0162, 0.01575, 0.0153, 0.01485, 0.0144, 0.01445, 0.0145, 0.0145, 0.0145, 0.01505, 0.0156, 0.0156, 0.0156, 0.0166, 0.0176, 0.0186, 0.0196, 0.02265, 0.0257, 0.0307, 0.0357, 0.0417, 0.0477, 0.0492, 0.0507, 0.05325, 0.0558, 0.0598, 0.0638, 0.0673, 0.0708, 0.07535, 0.0799, 0.09395, 0.108, 0.1325, 0.157, 0.2005, 0.244, 0.2665, 0.289, 0.299, 0.309, 0.314, 0.319, 0.324, 0.329, 0.339, 0.349, 0.3745, 0.4, 0.415, 0.43, 0.44, 0.45, 0.475, 0.5, 0.575, 0.65]).astype(float)
            b_wv = np.asarray([0.0076, 0.0072, 0.0068, 0.00645, 0.0061, 0.0058, 0.0055, 0.0052, 0.0049, 0.0047, 0.0045, 0.0043, 0.0041, 0.0039, 0.0037, 0.00355, 0.0034, 0.00325, 0.0031, 0.003, 0.0029, 0.00275, 0.0026, 0.0025, 0.0024, 0.0023, 0.0022, 0.00215, 0.0021, 0.002, 0.0019, 0.00185, 0.0018, 0.00175, 0.0017, 0.00165, 0.0016, 0.00155, 0.0015, 0.00145, 0.0014, 0.00135, 0.0013, 0.00125, 0.0012, 0.00115, 0.0011, 0.00105, 0.001, 0.001, 0.001, 0.0009, 0.0008, 0.0008, 0.0008, 0.00075, 0.0007, 0.0007, 0.0007, 0.0007, 0.0007]).astype(float)
            e_wv = np.asarray([0.64358, 0.647665, 0.65175, 0.65546, 0.65917, 0.6625, 0.66583, 0.66879, 0.67175, 0.674335, 0.67692, 0.67913, 0.68134, 0.683175, 0.68501, 0.686475, 0.68794, 0.688745, 0.68955, 0.689175, 0.6888, 0.687235, 0.68567, 0.68291, 0.68015, 0.676195, 0.67224, 0.667095, 0.66195, 0.65561, 0.64927, 0.644635, 0.64, 0.6315, 0.623, 0.6165, 0.61, 0.614, 0.618, 0.622, 0.626, 0.63, 0.634, 0.638, 0.642, 0.6475, 0.653, 0.658, 0.663, 0.6675, 0.672, 0.677, 0.682, 0.6885, 0.695, 0.694, 0.693, 0.6665, 0.64, 0.62, 0.6]).astype(float)
            X_wv = np.asarray([0.11748, 0.120035, 0.12259, 0.12264, 0.12269, 0.12024, 0.11779, 0.11371, 0.10963, 0.10564, 0.10165, 0.09779, 0.09393, 0.09021, 0.08649, 0.082905, 0.07932, 0.07587, 0.07242, 0.069105, 0.06579, 0.06261, 0.05943, 0.05642, 0.05341, 0.05085, 0.04829, 0.04624, 0.04419, 0.04265, 0.04111, 0.040055, 0.039, 0.0375, 0.036, 0.0345, 0.033, 0.03275, 0.0325, 0.03325, 0.034, 0.035, 0.036, 0.03725, 0.0385, 0.04025, 0.042, 0.043, 0.044, 0.0445, 0.045, 0.04625, 0.0475, 0.0495, 0.0515, 0.051, 0.0505, 0.04475, 0.039, 0.0345, 0.03]).astype(float)
 
         else:
            # get pure seawater absorbance and backscattering coeffs
            coeff_path = os.patj.join(os.getcwd(),'coeffs')
            coeff_file = 'pure_sea_water_abs_bs_coefficients.txt'
            coeffs     = np.genfromtxt(os.path.join(coeff_path, coeff_file),\
                         skip_header=1,delimiter=',',dtype=float)

            coeff_wv  = coeffs[:,0]
            coeff_a_w = coeffs[:,2]
            coeff_b_w = coeffs[:,3]
            coeff_e   = coeffs[:,4]
            coeff_Xc  = coeffs[:,5]

            #interpolate coeffs onto required wavelengths
            a_wv      = interp1d(coeff_wv,coeff_a_w)(wv_selected)
            b_wv      = interp1d(coeff_wv,coeff_b_w)(wv_selected)
            e_wv      = interp1d(coeff_wv,coeff_e)(wv_selected)
            X_wv      = interp1d(coeff_wv,coeff_Xc)(wv_selected)   

         for CHL_scaling in np.arange(0.2,25,0.2):
            Modelled_PAR,new_rmse = spectral_par_depth(Ed_new,wv_selected,\
                                      depths,CHL_uncorr,CHL_scaling,\
                                      PAR_meas, a_wv, b_wv, e_wv, X_wv)
            if new_rmse < rmse:
               rmse = new_rmse
               Mod_PAR_final     = Modelled_PAR.copy()
               CHL_scaling_final = CHL_scaling.copy()

            if debug:
               p2,  = plt.plot(Modelled_PAR,depths*-1,'r',linewidth=0.25)
   except:
      logging.info('PAR profile is NaN, scale set to 1.0')
      if verbose:
         print('PAR profile is NaN, scale set to 1.0')
      CHL_scaling_final = 1.0
      Mod_PAR_final     = PAR_meas.copy()
      if debug:
          p2,  = plt.plot(PAR_meas,depths*-1,'r',linewidth=0.25)

   if debug:
      p1,  = plt.plot(PAR_meas,     depths*-1,'k',linewidth=1)
      p3,  = plt.plot(Mod_PAR_final,depths*-1,'b',linewidth=1)
      plt.xlabel('PAR [W.m$^{-2}$]',fontsize=fsz)
      plt.ylabel('depth [m]',fontsize=fsz)
      plt.ylim([np.nanmin(depths*-1),0.0])
      leg = plt.legend([p1,p2,p3],['PAR measured', 'PAR modelled',\
                    'PAR mod. optimum, CHL scale:'+str(CHL_scaling_final)],\
                    fontsize=fsz, loc="lower right") 
      fname=OUT_DIR+'/'+args.glider_tag+'_scaled_PAR_'+prof_num+'.png'
      plt.savefig(fname)
      logging.info('plotted '+fname)
      plt.close(fig0)

   print('Chl scaling: '+str(CHL_scaling_final))
   print('Ed scaling: '+str(Ed_scaling))
   # write corrected CHL and Ed scaling values into scale file
   write_scale_factors(CHL_scaling_final,Ed_scaling,sc_file,logging,verbose)
