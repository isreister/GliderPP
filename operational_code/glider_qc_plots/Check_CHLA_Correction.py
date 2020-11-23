#!/usr/bin/env python

import glob
import os, shutil
import netCDF4 as nc
import numpy as np
import datetime
import matplotlib.pyplot as plt
from matplotlib import gridspec
import argparse

#-ARGS--------------------------------------------------------------------------
DEFAULT_INPUT_DIR = '/data/datasets/Projects/AlterEco/Glider_data/BODC_preprocessed_data/EGO/'

parser = argparse.ArgumentParser()
parser.add_argument('-i', '--input_dir', type=str,\
                    default=DEFAULT_INPUT_DIR,\
                    help='Input directory')
parser.add_argument('-m', '--match_pattern', type=str,\
                    default='*Cabot*.nc',\
                    help='Match pattern')
parser.add_argument('-dmin', '--dmin', type=float,nargs='+',\
                    default=[0], help='depth minima')
parser.add_argument('-dmax', '--dmax', type=float,nargs='+',\
                    default=[10], help='depth maxima')
parser.add_argument('-t', '--truncate', type=float,\
                    default=30000, help='depth maxima')
args = parser.parse_args()

#-main--------------------------------------------------------------------------
if __name__ == "__main__":

    fsz = 16

    ncfiles = glob.glob(os.path.join(args.input_dir,args.match_pattern))
    
    # set up array of lists
    total_col = -1
    count = -1
    for ii in args.dmax:
        count = count + 1
        total_col = total_col + 1
        exec("%s=[]" % ('CHLA_all_'+str(count)))
        exec("%s=[]" % ('CHLA_corr_all_'+str(count)))

    glider_hour_all = []

    ncount = -1
    for ncfile in sorted(ncfiles):
        ncount= ncount + 1
        if ncount > args.truncate:
            continue
        print('Processing: '+ncfile)
        nc_fid = nc.Dataset(ncfile,'r')
        DEPTH = nc_fid.variables['DEPTH_CORRECTED'][:]
        CHLA = nc_fid.variables['CHLA'][:]
        CHLA_CORRECTED = nc_fid.variables['CHLA_CORRECTED'][:]
        TIME = nc_fid.variables['TIME'][:]
        nc_fid.close()
        
        glider_HOUR = int((datetime.datetime(1970,1,1) + datetime.timedelta(seconds=int(np.nanmean(TIME)))).hour)
        glider_hour_all.append(int(glider_HOUR))

        count = -1
        for ii in args.dmax:
            count = count + 1
            exec("%s.append(np.nanmean(CHLA[(DEPTH > %s) & (DEPTH < %s)]))" % ('CHLA_all_'+str(count),str(args.dmin[count]),str(args.dmax[count])))
            exec("%s.append(np.nanmean(CHLA_CORRECTED[(DEPTH > %s) & (DEPTH < %s)]))" % ('CHLA_corr_all_'+str(count),str(args.dmin[count]),str(args.dmax[count])))

    glider_HOURS = np.asarray(glider_hour_all).astype(int)

    fig = plt.figure(figsize=(10,total_col*10))
    gs = gridspec.GridSpec(len(args.dmax),1)
    plt.rcParams.update({'font.size': fsz})

    x_vals = range(24)
    max_val = 0
    axes = []
    count = -1
    for ii in args.dmax:
        count = count + 1       
        ax = plt.subplot(gs[count, 0])
        axes.append(ax)
        hist_val = np.zeros(24)
        hist_val_corr = np.zeros(24)
        exec("this_CHLA = np.asarray(%s).astype(float)" % ('CHLA_all_'+str(count)))
        exec("this_CHLA_corr = np.asarray(%s).astype(float)" % ('CHLA_corr_all_'+str(count)))
        for jj in range(24):
            hist_val[jj] = np.nanmean(this_CHLA[glider_HOURS == jj])
            hist_val_corr[jj] = np.nanmean(this_CHLA_corr[glider_HOURS == jj])

        max_val = np.max([np.max(hist_val),np.max(hist_val_corr),max_val])
        print(max_val)
        cmap = plt.cm.Blues
        plt.bar(x_vals,hist_val,color=cmap(float(count+1)/float(total_col + 1)))
        plt.plot(x_vals,hist_val_corr,'k--')
        plt.xlabel('Hour')
        plt.ylabel('Average chlorophyll [mg.m$^{-3}$]')
        plt.xlim([0,24])
        plt.title('Depth limits: '+str(args.dmin[count]) +' to ' + str(args.dmax[count]))

    for axis in axes:
        axis.set_ylim([0,max_val])

    plt.savefig('CHL_quenching_correction')
