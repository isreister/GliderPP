#!/usr/bin/env python
'''
Description:    Subsets Ed file, and applies Chl and Ed scaling factors to 
                pp input files

Version: 	v1.0 01/2018

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

#-default parameters------------------------------------------------------------
DEFAULT_ROOT_DIR   = '/data/datasets/Projects/AlterEco/Glider_data/Oman/'
DEFAULT_OUT_DIR    = './'
DEFAULT_LOG_PATH   = '/home/ben/shared/Linux_desktop/local1/data/scratch/blo/AlterEco/operational_code/logs/'
DEFAULT_GTAG       = 'SG510'
#-args--------------------------------------------------------------------------
parser = argparse.ArgumentParser()
#-input vars--------------------------------------------------------------------
parser.add_argument('-d', '--root_dir', type=str,\
                    default = DEFAULT_ROOT_DIR,\
                    help = 'Glider root directory')
parser.add_argument('-o', '--out_dir', type=str,\
                    default = DEFAULT_OUT_DIR,\
                    help = 'Plot output directory')
parser.add_argument('-g', '--gtag', type=str,\
                    default = DEFAULT_GTAG,\
                    help = 'Glider tag')
parser.add_argument('-l', '--log_path', type=str,\
                    default = DEFAULT_LOG_PATH,\
                    help = 'log file output path')
parser.add_argument('-v', '--verbose',\
                    action = 'store_true')
parser.add_argument('-nochl', '--no_chl_correction',\
                    action = 'store_true')
parser.add_argument('-s', '--suffix', type=str,\
                    default = '.txt',\
                    help = 'scale file suffix')

#-input vars end----------------------------------------------------------------
args   = parser.parse_args()

#-main--------------------------------------------------------------------------
if __name__ == "__main__":
   # -preliminary stuff---------------------------------------------------------
   debug    = 0
   verbose  = args.verbose
   logfile  = args.log_path+"apply_Chl_Ed_corrections_"+\
              datetime.datetime.now().strftime('%Y%m%d_%H%M')+".log"
   Med_win  = 10
   fsz      = 12
 
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
   logging.warning('RUNNING: WARNINGS ARE SUPPRESSED')

   # -get the files-------------------------------------------------------------
   scale_files=[]
   for root, _, filenames in os.walk(args.root_dir):
       for filename in fnmatch.filter(filenames,'scale_station_??????'+args.suffix):
           scale_files.append(os.path.join(root, filename))
           if verbose:
              print('Found: '+filename)
           logging.info('Found: '+os.path.join(root, filename))

   CHL_scaling   = np.ones(len(scale_files))*np.nan
   CHL_sc_smooth = np.ones(len(scale_files))*np.nan
   std_sc_smooth = np.ones(len(scale_files))*np.nan
   Ed_scaling    = np.ones(len(scale_files))*np.nan
   ord_dates     = np.ones(len(scale_files))*np.nan
   prof_num      = np.ones(len(scale_files))*np.nan

   count = -1
   for scale_file in sorted(scale_files):
      count = count + 1
      index = os.path.basename(scale_file)
      index = index.split('.')[0]
      prof_num[count]= float(index.split('_')[2])
   
      with open(scale_file,"r") as the_file:
         for line in the_file:
            if 'CHL_scale' in line:
               CHL_scaling[count]=float(line.split(' ')[1].replace('\n',''))
            if 'Ed_scale' in line:
               Ed_scaling[count]=float(line.split(' ')[1].replace('\n',''))
   
      telemetry_file = scale_file.replace('scale','telemetry')
      with open(telemetry_file,"r") as the_file:
         for line in the_file:
            if 'year' in line:
               year=line.split(' ')[1].replace('\n','')
            if 'jday' in line:
               jday=line.split(' ')[1].replace('\n','')

      if count == 0:
         start_date = datetime.datetime.strptime(jday+year,"%j%Y")
      ord_dates[count] = datetime.datetime.strptime(jday+year,"%j%Y").toordinal()
   
   print('Read scale files...')
   # read CHL scaling and date
   # no need to smooth the Ed_scaling, but CHL scale is smoothed using median 
   # 10 day window

   for ii in np.arange(0,len(CHL_scaling)):
      min_date = ord_dates[ii]-Med_win/2
      max_date = ord_dates[ii]+Med_win/2
      in_scope = np.where((ord_dates>=min_date) & (ord_dates<=max_date))
      tmpCHL   = CHL_scaling[in_scope]
      CHL_sc_smooth[ii] = np.mean(tmpCHL[tmpCHL != 1.0])
      std_sc_smooth[ii] = np.std(tmpCHL[tmpCHL != 1.0])

   if args.no_chl_correction:
      print('Skipping CHL correction')
      CHL_sc_smooth = np.ones(len(CHL_sc_smooth))

   count = -1
   # output new scaled CHL
   for scale_file in sorted(scale_files):
      count = count + 1
      index = os.path.basename(scale_file)
      index = index.split('.')[0]
      prof_num[count]= float(index.split('_')[2])

      chl_file       = scale_file.replace('scale','chl_profile')
      chl_out_file   = chl_file.replace('.txt','.corr')

      if os.path.exists(chl_out_file):
        os.chmod(chl_out_file, 0o777)
        os.remove(chl_out_file)

      with open(chl_file,"r") as in_file:
         with open(chl_out_file,"w") as out_file:
            for line in in_file:
               line_parts = line.split(' ')
               out_file.write(line_parts[0]+' '+\
                              line_parts[1]+' '+\
                              str(float(line_parts[-1])*CHL_sc_smooth[count]) +\
                              '\n')

      os.chmod(chl_out_file, 0o777)

   count = -1
   # output new scaled and subset Ed
   for scale_file in sorted(scale_files):
      count = count + 1

      telemetry_file = scale_file.replace('scale','telemetry')
      with open(telemetry_file,"r") as the_file:
         for line in the_file:
            if 'is_day' in line:
               is_day=line.split(' ')[1].replace('\n','')
            if 'time' in line:
               time=line.split(' ')[1].replace('\n','')

      index = os.path.basename(scale_file)
      index = index.split('.')[0]
      prof_num[count]= float(index.split('_')[2])

      ed_file = scale_file.replace('scale','ed_profile')
      ed_subset_file = ed_file.replace('ed_profile','eds_profile')
      ed_subset_corr_file   = ed_subset_file.replace('.txt','.corr')

      if os.path.exists(ed_subset_file):
        os.chmod(ed_subset_file, 0o777)
        os.remove(ed_subset_file)

      if os.path.exists(ed_subset_corr_file):
        os.chmod(ed_subset_corr_file, 0o777)
        os.remove(ed_subset_corr_file)

      file_values = np.genfromtxt(ed_file, dtype=("|S10", float, float, float))
      T_off = np.ones(np.shape(file_values))*np.nan
      wv = np.ones(np.shape(file_values))*np.nan
      Ed = np.ones(np.shape(file_values))*np.nan  #W.m-2.nm-1
      mu0 = np.ones(np.shape(file_values))*np.nan
      times = []

      hour_glider,minute_glider = time.split(':')
      T_glider = datetime.datetime(2000,1,1,int(hour_glider),int(minute_glider))
      
      # read values
      for ii in np.arange(0,len(file_values)):
         hour, minute  = file_values[ii][0].decode("utf-8").split(':')
         T_profile     = datetime.datetime(2000,1,1,int(hour),int(minute))
         T_off[ii]     = abs(float((T_profile-T_glider).total_seconds()))
         wv[ii]        = file_values[ii][1]
         Ed[ii]        = file_values[ii][2]        
         mu0[ii]       = file_values[ii][3]
         times.append(hour + ':' + minute)

      times = np.asarray(times)
      # select nearest profile in time
      tt = np.where((T_off == np.nanmin(T_off)))
      wv_selected = wv[tt]
      if float(is_day) == 0.0:
         Ed_selected = Ed[tt]*0.0
      else:
         Ed_selected = Ed[tt]
      mu0_selected = mu0[tt]
      times_selected = times[tt]

      with open(ed_subset_file,"w") as in_file:
         for ii in np.arange(len(mu0_selected)):
            in_file.write(str(times_selected[ii]) + '\t' \
                          + str(int(wv_selected[ii])) + '\t' \
                          + str(Ed_selected[ii]) + '\t' \
                          + str(mu0[ii]))
            if ii < len(mu0_selected):
               in_file.write('\n')

      os.chmod(ed_subset_file, 0o777)

      with open(ed_subset_file,"r") as in_file:
         with open(ed_subset_corr_file,"w") as out_file:
            for line in in_file:
               line_parts = line.split('\t')
               out_file.write(line_parts[0]+'\t'+\
                              line_parts[1]+'\t'+\
                              str(float(line_parts[-2])*Ed_scaling[count])+'\t'+\
                              line_parts[-1])

      os.chmod(ed_subset_file, 0o777)
      os.chmod(ed_subset_corr_file, 0o777)

   if debug:
      #CHL_scaling[CHL_scaling == 1.0] = np.nan
      plot_dates = ord_dates-np.nanmin(ord_dates)
      plt.scatter(plot_dates,CHL_scaling, 20, c='k', alpha=0.5, marker='x')
      plt.scatter(plot_dates,CHL_sc_smooth,'r')
      plt.plot(plot_dates,CHL_sc_smooth+std_sc_smooth,'r--')
      plt.plot(plot_dates,CHL_sc_smooth-std_sc_smooth,'r--')
      plt.ylim([0.0,15.0])
      plt.xlim([0.0,np.nanmax(plot_dates)])
      plt.xlabel('Days since '+\
               datetime.datetime.strftime(start_date,"%d/%m/%Y"),fontsize=fsz)
      plt.ylabel('Scale Factor',fontsize=fsz)
      fname   = args.out_dir+'scale_factors_'+args.gtag+'.png'
      plt.savefig(fname)

