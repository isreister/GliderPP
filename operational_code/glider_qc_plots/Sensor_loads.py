#!/usr/bin/python

"""
Description:    Check for sensor data on gliders; netCDF only

Author:         Ben Loveday
Date:           02/2019
Version:        v1.0

Expected Seagliders:
['humpback','Scapa','Orca','Melonhead','Fin']
Expected non-Seagliders
['Coprolite','Dolomite','Cook','Cabot','Scapa','Eltanin','Kelvin']
"""
#-------------------------------------------------------------------------------
#-modules----
from __future__ import print_function
import shutil
import os
import sys
import numpy as np
import argparse
import datetime
import logging
import fnmatch
import netCDF4 as nc
import warnings
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import gridspec
from mpl_toolkits.basemap import Basemap

sys.path.append("tools")

import processing_tools as pt

# -messages----------------------------------------------------------------------
print("RUNNING: WARNINGS ARE SUPPRESSED")
warnings.filterwarnings('ignore')

def get_var(nc_fid, variable):
    VAR_FOUND = True
    VAR = nc_fid.variables[variable][:]
    if np.ma.is_masked(VAR):
        VAR = VAR.data
        fillval = nc_fid.variables[variable]._FillValue
        try:
            VAR[VAR==fillval]=np.nan
        except:
            pass
    return VAR, VAR_FOUND

def plot_bar(ax, time, var, mycol, yoffset, ylabel, xmin, xmax):
    ax.plot([xmin, xmax],[yoffset, yoffset], 'k--', linewidth=1.0, zorder=1)
    ax.plot(time[np.isfinite(var)],var[np.isfinite(var)]*0+yoffset,color=mycol,linewidth=20, zorder=2, alpha=0.75)

def plot_trace(ax, time, var, mycol, ylabel, xmin, xmax, xticks, xlabels, ymin=0, ymax=1, log=False):

    time[time > 1e20] = np.nan

    ax.plot(time[np.isfinite(var)],var[np.isfinite(var)], marker='o', markersize=2, markerfacecolor=mycol, markeredgecolor=mycol, linewidth=0, zorder=10, alpha=0.5)

    ax.set_ylabel(ylabel)
    ax.set_xticks(xticks)
    ax.set_xticklabels(xlabels,rotation=90)
    ax.set_xlim([np.nanmin(time), np.nanmax(time)])
    ax.set_ylim([ymin, ymax])
    if log == True:
        ax.set_yticks(np.arange(ymin,ymax))
        ticks = np.arange(ymin,ymax)
        logticks = [] 
        for ii in range(len(ticks)):
            logticks.append(10.**ticks[ii])
        ax.set_yticklabels(logticks)

    # add monthly shading and year markers
    for ii in np.arange(2010, 2020):
        ystart = (datetime.datetime(ii,1,1) - datetime.datetime(1970,1,1)).total_seconds()
        ax.plot([ystart, ystart],[ymin, ymax],'k', linestyle='--', linewidth=1.0, zorder=2)
        for jj in range(12):
            tstart = (datetime.datetime(ii,jj+1,1) - datetime.datetime(1970,1,1)).total_seconds()
            if jj+2>12:
                tend = (datetime.datetime(ii+1,1,1) - datetime.datetime(1970,1,1)).total_seconds()-1.0
            else:
                tend = (datetime.datetime(ii,jj+2,1) - datetime.datetime(1970,1,1)).total_seconds()-1.0
            if np.mod(jj,2) == 0:
                ax.fill_between([tstart, tend],[ymin, ymin],[ymax, ymax], color='0.85', zorder=1)

def print_statuses(var, var_qc, vname):
    if var and var_qc:
        print('>>>> '+vname+' found with QC flags')
    elif var and not var_qc:
        print('>>>> '+vname+' found without QC flags')
    elif not var:
        print('>>>> '+vname+' not found')

#-------------------------------------------------------------------------------
parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input_dir",\
                    type=str, \
                    default="/data/datasets/Projects/AlterEco/Glider_data/BODC_data/")
parser.add_argument("-s", "--sensors",\
                    type=str, nargs='+', \
                    default=None)
parser.add_argument("-sub", "--subsample",\
                type=int, default=10)
parser.add_argument("-ego", "--EGO_only",\
                type=int, default=0)
parser.add_argument("-sg", "--SG_only",\
                type=int, default=0)
args = parser.parse_args()
#-------------------------------------------------------------------------------

if __name__ == "__main__":

    CHLA_COL = '#458B74'
    BBP_COL = '#DC143C'
    CDOM_COL = '#CD950C'
    PAR_COL =  '#6495ED'
    DOXY_COL = 	'#68228B'

    # for plotting glider track
    lonmin = -2
    lonmax = 4
    latmin = 53
    latmax = 59

    lattix = 1
    lontix = 1
    zordcoast = 0
    msize = 1
    fsz = 16

    #universal plot
    figA = plt.figure(figsize=(20,10), dpi=300)
    gsA = gridspec.GridSpec(1, 1)
    plt.rcParams.update({'font.size': fsz})
    axesA = plt.subplot(gsA[0, 0])

    xmin = (datetime.datetime(2017,10,1) - datetime.datetime(1970,1,1)).total_seconds()
    xmax = (datetime.datetime.now() - datetime.datetime(1970,1,1)).total_seconds()
    yticks=[0.1, 0.2, 0.3, 0.4, 0.5]
    ylabels = ['DOXY','PAR','CDOM','BACKSCATTER','CHLA']

    xticks = []
    xlabels = []
    for YY in np.arange(1970,2020):
        for MM in np.arange(1,13):
            xlabels.append(str(MM).zfill(2)+'-'+str(YY))
            xticks.append((datetime.datetime(YY,MM,1) - datetime.datetime(1970,1,1)).total_seconds())

    # --------------------------------------------------------------------------    
    # --------------------------------------------------------------------------
    # find glider EGO netcdf files
    glider_EGO_files = []
    for root, _, filenames in os.walk(args.input_dir+'/EGO'):
        for filename in fnmatch.filter(filenames,"*.nc"):
            glider_EGO_files.append(os.path.join(root, filename))

    print('')
    print('---------------------')
    print('EGO data')
    print('---------------------')
    for glider_EGO_file in np.unique(glider_EGO_files):
        print(os.path.basename(glider_EGO_file))

    # --------------------------------------------------------------------------
    # --------------------------------------------------------------------------
    # find SeaGlider netcdf data directories
    Seaglider_dirs = []
    for root, _, filenames in os.walk(args.input_dir):
        for filename in fnmatch.filter(filenames,"*.nc"):
            if 'sg' in os.path.basename(root):
                Seaglider_dirs.append(os.path.join(root))

    # accommodate Scapa
    for root, _, filenames in os.walk(args.input_dir):
        for filename in fnmatch.filter(filenames,"p*.nc"):
            if 'Scapa' in os.path.basename(root):
                Seaglider_dirs.append(os.path.join(root))

    # accommodate Eltanin
    for root, _, filenames in os.walk(args.input_dir):
        for filename in fnmatch.filter(filenames,"p*.nc"):
            if 'Eltanin' in os.path.basename(root):
                Seaglider_dirs.append(os.path.join(root))

    Seaglider_tags = []
    for Seaglider_dir in Seaglider_dirs:
        Seaglider_tags.append(os.path.basename(Seaglider_dir))

    print('')
    print('---------------------')
    print('Seaglider data')
    print('---------------------')
    for Seaglider_tag in np.unique(Seaglider_tags):
        print(Seaglider_tag)
    print('')
    print('')
 
    print('')
    print('---------------------')
    print('Processing Seaglider data')
    print('---------------------')
    # sea glider routine.....horrible
    for Seaglider_tag in np.unique(Seaglider_tags):
        if args.EGO_only == 1:
            continue
        Seaglider_files = []
        for Seaglider_dir in np.unique(Seaglider_dirs):
            if Seaglider_tag in Seaglider_dir:
                print('Processing '+Seaglider_tag+' data from: '+Seaglider_dir)
                for root, _, filenames in os.walk(Seaglider_dir):
                    for filename in fnmatch.filter(filenames,"p*.nc"):
                        if 'Deployment' not in root:
                            Seaglider_files.append(os.path.join(root, filename))

        LON_FOUND = False ; ALL_LON = []
        LAT_FOUND = False ; ALL_LAT = []
        TIME_FOUND = False ; ALL_TIME = []
        CHLA_FOUND = False ; ALL_CHLA = []
        CDOM_FOUND = False ; ALL_CDOM = []
        DOXY_FOUND = False ; ALL_DOXY = []
        BBP_FOUND = False ; ALL_BBP = []
        PAR_FOUND = False ; ALL_PAR = []
  
        for Seaglider_file in Seaglider_files:
            nc_fid = nc.Dataset(Seaglider_file,'r')
            variables = nc_fid.variables

            LAT = []
            LON = []
            TIME = []
            BBP = []
            CHLA = []
            DOXY = []
            PAR = []

            for variable in variables:
                if variable.upper() == 'LATITUDE':
                    LAT, LAT_FOUND = get_var(nc_fid, variable)
                if variable.upper() == 'LONGITUDE':
                    LON, LON_FOUND = get_var(nc_fid, variable)
                if variable.upper() == 'TIME':
                    TIME, TIME_FOUND = get_var(nc_fid, variable)

                if '_FL1SIG' in variable.upper():
                    CHLA, CHLA_FOUND = get_var(nc_fid, variable)

                if '_FL2SIG' in variable.upper():
                    CDOM, CDOM_FOUND = get_var(nc_fid, variable)

                if '_BB1SIG' in variable.upper() or '_BB2SIG' in variable.upper():
                    BBP, BBP_FOUND = get_var(nc_fid, variable)

                if variable.upper() == 'ENG_AA4330F_O2' or variable.upper() == 'ENG_AA4330_O2':
                    DOXY, DOXY_FOUND = get_var(nc_fid, variable)

                if '_PARUV' in variable.upper():
                    PAR, PAR_FOUND = get_var(nc_fid, variable)

            nc_fid.close()

            if len(LON) == len(TIME) and len(LAT) == len(TIME):
                ALL_LAT.append(LAT)
                ALL_LON.append(LON)
                ALL_TIME.append(TIME)
            else:
                print('Coordinates are dicey! Skipping')
                continue

            if CHLA_FOUND:
                if len(CHLA) == len(TIME):
                    ALL_CHLA.append(CHLA)
                else:
                    print(Seaglider_file +': CHLA is problematic; zeroing')
                    ALL_CHLA.append(TIME*0)

            if BBP_FOUND:
                if len(BBP) == len(TIME):
                    ALL_BBP.append(BBP)
                else:
                    print(Seaglider_file+': BBP is problematic; zeroing')
                    ALL_BBP.append(TIME*0)

            if DOXY_FOUND:
                if len(DOXY) == len(TIME):
                    ALL_DOXY.append(DOXY)
                else:
                    print(Seaglider_file+': DOXY is problematic; zeroing')
                    ALL_DOXY.append(TIME*0)

            if CDOM_FOUND:
                if len(CDOM) == len(TIME):
                    ALL_CDOM.append(CDOM)
                else:
                    print(Seaglider_file+': DOXY is problematic; zeroing')
                    ALL_DOXY.append(TIME*0)

            if PAR_FOUND:
                if len(PAR) == len(TIME):
                    ALL_PAR.append(PAR)
                else:
                    print(Seaglider_file+': PAR is problematic; zeroing')
                    ALL_PAR.append(TIME*0)

        print_statuses(LON_FOUND, False, 'Longitude')
        print_statuses(LAT_FOUND, False, 'Latitude')
        print_statuses(TIME_FOUND, False, 'Time')
        print_statuses(CHLA_FOUND, False, 'Chlorophyll-a')
        print_statuses(BBP_FOUND, False, 'Backscattering')
        print_statuses(PAR_FOUND, False, 'PAR')
        print_statuses(CDOM_FOUND, False, 'CDOM')
        print_statuses(DOXY_FOUND, False, 'DOXY')

        TIME = np.asarray([item for sublist in ALL_TIME for item in sublist])
        LON = np.asarray([item for sublist in ALL_LON for item in sublist])
        LAT = np.asarray([item for sublist in ALL_LAT for item in sublist])

        sort_vals=np.argsort(TIME)
        TIME = TIME[sort_vals]
        LON = LON[sort_vals]
        LAT = LAT[sort_vals]

        if CHLA_FOUND:
            CHLA = np.asarray([item for sublist in ALL_CHLA for item in sublist])
            CHLA = CHLA[sort_vals]
        if BBP_FOUND:
            BBP = np.asarray([item for sublist in ALL_BBP for item in sublist])
            BBP = BBP[sort_vals]
        if CDOM_FOUND:
            CDOM = np.asarray([item for sublist in ALL_CDOM for item in sublist])
            CDOM = CDOM[sort_vals]
        if DOXY_FOUND:
            DOXY = np.asarray([item for sublist in ALL_DOXY for item in sublist])
            DOXY = DOXY[sort_vals]
        if PAR_FOUND:
            PAR = np.asarray([item for sublist in ALL_PAR for item in sublist])
            PAR = PAR[sort_vals]

        # apply QC vals
        ii = np.where((np.isfinite(LON)) & (np.isfinite(LAT)))
        LAT = LAT[ii]
        LON = LON[ii]

        if Seaglider_tag == 'sg510blahblah':
            LON_stripped, LAT_stripped, TIME_stripped = pt.fix_bad_points(LON,LAT,TIME/86400, threshold=100)
        else:
            LON_stripped = LON.copy()
            LAT_stripped = LAT.copy()

        #plots
        fig1 = plt.figure(figsize=(20,20), dpi=300)
        gs = gridspec.GridSpec(2, 1, height_ratios=[1,5])
        gs.update(wspace=0.01, hspace=0.25)
        plt.rcParams.update({'font.size': fsz})

        # plot sensor loads
        axes1 = plt.subplot(gs[0, 0])

        if CHLA_FOUND:
            plot_bar(axes1, TIME, CHLA, CHLA_COL, 0.5, 'CHLA', xmin, xmax)
        if BBP_FOUND:
            plot_bar(axes1, TIME, BBP, BBP_COL, 0.4, 'BBP', xmin, xmax)
        if CDOM_FOUND:
            plot_bar(axes1, TIME, CDOM, CDOM_COL, 0.3, 'CDOM', xmin, xmax)
        if PAR_FOUND:
            plot_bar(axes1, TIME, PAR, PAR_COL, 0.2, 'PAR', xmin, xmax)
        if DOXY_FOUND:
            plot_bar(axes1, TIME, DOXY, DOXY_COL, 0.1, 'DOXY', xmin, xmax)

        axes1.set_yticks(yticks)
        axes1.set_yticklabels(ylabels)
        axes1.set_xticks(xticks)
        axes1.set_xticklabels(xlabels,rotation=90)
        axes1.set_xlim([xmin, xmax])
        axes1.set_ylim([0.0, 0.6])

        # plot glider track
        axes2 = plt.subplot(gs[1, 0])

	m = Basemap(llcrnrlon=lonmin, llcrnrlat=latmin, urcrnrlon=lonmax, \
		urcrnrlat=latmax, resolution='h', projection='cyl')

	xx, yy = m(LON_stripped[::args.subsample], LAT_stripped[::args.subsample])
	m.plot(xx, yy, 'r', linewidth=1.0, zorder = 100)

	m.fillcontinents(color=[0.4, 0.4, 0.4], zorder=zordcoast)
	m.drawcoastlines(color='k', linewidth=0.25, zorder=zordcoast + 1)
	m.drawcountries(color='k', linewidth=0.15, zorder=zordcoast + 2)

	m.drawparallels(np.arange(-80, 90, lattix), labels=[1, 0, 0, 0], linewidth=0.25, zorder=zordcoast + 3)
	m.drawmeridians(np.arange(-180, 180, lontix), labels=[0, 0, 0, 1], linewidth=0.25, zorder=zordcoast + 3)
        plt.savefig('/users/rsg/utils/web_visible_public_share/blo/files/AlterEco/PP_plots/' + Seaglider_tag + '_sensor_coverage', bbox_inches='tight')
        plt.close(fig1)

        # plot sensor loads
        if CHLA_FOUND:
            plot_bar(axesA, TIME, CHLA, CHLA_COL, 0.5, 'CHLA', xmin, xmax)
        if BBP_FOUND:
            plot_bar(axesA, TIME, BBP, BBP_COL, 0.4, 'BBP', xmin, xmax)
        if CDOM_FOUND:
            plot_bar(axesA, TIME, CDOM, CDOM_COL, 0.3, 'CDOM', xmin, xmax)
        if PAR_FOUND:
            plot_bar(axesA, TIME, PAR, PAR_COL, 0.2, 'PAR', xmin, xmax)
        if DOXY_FOUND:
            plot_bar(axesA, TIME, DOXY, DOXY_COL, 0.1, 'DOXY', xmin, xmax)

        #plots
        fig2 = plt.figure(figsize=(10,20), dpi=300)
        gs = gridspec.GridSpec(5, 1)
        gs.update(wspace=0.01, hspace=0.5)
        plt.rcParams.update({'font.size': fsz})

        # plot sensor loads
        if CHLA_FOUND:
            axes1 = plt.subplot(gs[0, 0])
            ymin = -3
            ymax = 1
            plot_trace(axes1, TIME, np.log10(CHLA), CHLA_COL, 'CHLA [mg.l$^{-1}$]', xmin, xmax, xticks, xlabels, ymin, ymax, log=True)

        # plot sensor loads
        if BBP_FOUND:
            axes2 = plt.subplot(gs[1, 0])
            ymin = -4
            ymax = -2
            plot_trace(axes2, TIME, np.log10(BBP), BBP_COL, 'BBP [m$^{-1}$]', xmin, xmax, xticks, xlabels, ymin, ymax, log=True)

        # plot sensor loads
        if CDOM_FOUND:
            axes3 = plt.subplot(gs[2, 0])
            ymin = 0
            ymax = 1
            plot_trace(axes3, TIME, np.log10(CDOM), CDOM_COL, 'CDOM [ppb]', xmin, xmax, xticks, xlabels, ymin, ymax, log=True)

        # plot sensor loads
        if PAR_FOUND:
            axes4 = plt.subplot(gs[3, 0])
            ymin = 0.
            ymax = np.nanmean(PAR) + 3*np.nanstd(PAR)
            plot_trace(axes4, TIME, PAR, PAR_COL, 'PAR [$\mu$mol.m$^{-2}$.s]', xmin, xmax, xticks, xlabels, ymin, ymax)

        # plot sensor loads
        if DOXY_FOUND:
            axes5 = plt.subplot(gs[4, 0])
            ymin = 0.
            ymax = np.nanmean(DOXY) + 3*np.nanstd(DOXY)
            plot_trace(axes5, TIME, DOXY, DOXY_COL, 'DOXY [$\mu$mol.l$^{-1}$]', xmin, xmax, xticks, xlabels, ymin, ymax)

        if CHLA_FOUND or BBP_FOUND or CDOM_FOUND or PAR_FOUND or DOXY_FOUND:
            plt.savefig('/users/rsg/utils/web_visible_public_share/blo/files/AlterEco/PP_plots/' + Seaglider_tag + '_sensor_QC', bbox_inches='tight')
            plt.close(fig2)
        else:
            print('No sensor data to plot')

    print('')
    print('---------------------')
    print('Processing EGO data')
    print('---------------------')
    # EGO glider routine.....ok!
    for glider_EGO_file in np.unique(glider_EGO_files):
        bad_flag = False
        if args.SG_only == 1:
            continue
        print('---------------------')
        print('Extracting timelines for:\t'+glider_EGO_file)
        nc_fid = nc.Dataset(glider_EGO_file,'r')
        variables = nc_fid.variables

        LON_FOUND = False ; LON_QC_FOUND = False
        LAT_FOUND = False ; LAT_QC_FOUND = False
        TIME_FOUND = False ; TIME_QC_FOUND = False
        CHLA_FOUND = False ; CHLA_QC_FOUND = False
        CDOM_FOUND = False ; CDOM_QC_FOUND = False
        DOXY_FOUND = False ; DOXY_QC_FOUND = False
        BBP_FOUND = False ; BBP_QC_FOUND = False
        PAR_FOUND = False ; PAR_QC_FOUND = False

        try:
            for variable in variables:
                if variable.upper() == 'LATITUDE':
                    LAT, LAT_FOUND = get_var(nc_fid, variable)
                if variable.upper() == 'LATITUDE_QC':
                    LAT_QC, LAT_QC_FOUND = get_var(nc_fid, variable)

                if variable.upper() == 'LONGITUDE':
                    LON, LON_FOUND = get_var(nc_fid, variable)
                if variable.upper() == 'LONGITUDE_QC':
                    LON_QC, LON_QC_FOUND = get_var(nc_fid, variable)

                if variable.upper() == 'TIME':
                    TIME, TIME_FOUND = get_var(nc_fid, variable)
                if variable.upper() == 'TIME_QC':
                    TIME_QC, TIME_QC_FOUND = get_var(nc_fid, variable)

                if variable.upper() == 'CHLA' or variable == 'FLUORESCENCE_CHLA':
                    CHLA, CHLA_FOUND = get_var(nc_fid, variable)
                if variable.upper() == 'CHLA_QC' or variable == 'FLUORESCENCE_CHLA_QC':
                    CHLA_QC, CHLA_QC_FOUND = get_var(nc_fid, variable)

                if variable.upper() == 'CDOM' or variable == 'FLUORESCENCE_CDOM':
                    CDOM, CDOM_FOUND = get_var(nc_fid, variable)
                if variable.upper() == 'CDOM_QC' or variable == 'FLUORESCENCE_CDOM_QC':
                    CDOM_QC, CDOM_QC_FOUND = get_var(nc_fid, variable)

                if variable.upper() == 'MOLAR_DOXY':
                    DOXY, DOXY_FOUND = get_var(nc_fid, variable)
                if variable.upper() == 'MOLAR_DOXY_QC':
                    DOXY_QC, DOXY_QC_FOUND = get_var(nc_fid, variable)

                if variable.upper() == 'BBP700':
                    BBP, BBP_FOUND = get_var(nc_fid, variable)
                if variable.upper() == 'BBP700_QC':
                    BBP_QC, BBP_QC_FOUND = get_var(nc_fid, variable)

                if variable.upper() == 'DOWNWELLING_PAR':
                    PAR, PAR_FOUND = get_var(nc_fid, variable)
                if variable.upper() == 'DOWNWELLING_PAR_QC':
                    PAR_QC, PAR_QC_FOUND = get_var(nc_fid, variable)
        except:
            bad_flag = True
            print('Something wrong with this data')

        try:
            nc_fid.close()
        except:
            print('File already closed')

        if bad_flag:
            continue

        print_statuses(LON_FOUND, LON_QC_FOUND, 'Longitude')
        print_statuses(LAT_FOUND, LAT_QC_FOUND, 'Latitude')
        print_statuses(TIME_FOUND, TIME_QC_FOUND, 'Time')
        print_statuses(CHLA_FOUND, CHLA_QC_FOUND, 'Chlorophyll-a')
        print_statuses(BBP_FOUND, BBP_QC_FOUND, 'Backscattering')
        print_statuses(PAR_FOUND, PAR_QC_FOUND, 'PAR')
        print_statuses(CDOM_FOUND, CDOM_QC_FOUND, 'CDOM')
        print_statuses(DOXY_FOUND, DOXY_QC_FOUND, 'DOXY')

        # apply QC vals
        try:
            ii = np.where((np.isfinite(LON)) & (np.isfinite(LAT)))
            LAT = LAT[ii]
            LON = LON[ii]
        except:
            print('Something wrong with coords')
            continue

        #plots
        fig1 = plt.figure(figsize=(20,20), dpi=300)
        gs = gridspec.GridSpec(2, 1, height_ratios=[1,5])
        gs.update(wspace=0.01, hspace=0.25)
        plt.rcParams.update({'font.size': fsz})

        # plot sensor loads
        axes1 = plt.subplot(gs[0, 0])

        if CHLA_FOUND:
            plot_bar(axes1, TIME, CHLA, CHLA_COL, 0.5, 'CHLA', xmin, xmax)
        if BBP_FOUND:
            plot_bar(axes1, TIME, BBP, BBP_COL, 0.4, 'BBP', xmin, xmax)
        if CDOM_FOUND:
            plot_bar(axes1, TIME, CDOM, CDOM_COL, 0.3, 'CDOM', xmin, xmax)
        if PAR_FOUND:
            plot_bar(axes1, TIME, PAR, PAR_COL, 0.2, 'PAR', xmin, xmax)
        if DOXY_FOUND:
            plot_bar(axes1, TIME, DOXY, DOXY_COL, 0.1, 'DOXY', xmin, xmax)

        axes1.set_yticks(yticks)
        axes1.set_yticklabels(ylabels)
        axes1.set_xticks(xticks)
        axes1.set_xticklabels(xlabels,rotation=90)
        axes1.set_xlim([xmin, xmax])
        axes1.set_ylim([0.0, 0.6])

        # plot sensor loads
        if CHLA_FOUND:
            plot_bar(axesA, TIME, CHLA, CHLA_COL, 0.5, 'CHLA', xmin, xmax)
        if BBP_FOUND:
            plot_bar(axesA, TIME, BBP, BBP_COL, 0.4, 'BBP', xmin, xmax)
        if CDOM_FOUND:
            plot_bar(axesA, TIME, CDOM, CDOM_COL, 0.3, 'CDOM', xmin, xmax)
        if PAR_FOUND:
            plot_bar(axesA, TIME, PAR, PAR_COL, 0.2, 'PAR', xmin, xmax)
        if DOXY_FOUND:
            plot_bar(axesA, TIME, DOXY, DOXY_COL, 0.1, 'DOXY', xmin, xmax)

        # plot glider track
        axes2 = plt.subplot(gs[1, 0])

	m = Basemap(llcrnrlon=lonmin, llcrnrlat=latmin, urcrnrlon=lonmax, \
		urcrnrlat=latmax, resolution='h', projection='cyl')

	xx, yy = m(LON[::args.subsample], LAT[::args.subsample])
	m.plot(xx, yy, 'r', linewidth=1.0, zorder = 100)

	m.fillcontinents(color=[0.4, 0.4, 0.4], zorder=zordcoast)
	m.drawcoastlines(color='k', linewidth=0.25, zorder=zordcoast + 1)
	m.drawcountries(color='k', linewidth=0.15, zorder=zordcoast + 2)

	m.drawparallels(np.arange(-80, 90, lattix), labels=[1, 0, 0, 0], linewidth=0.25, zorder=zordcoast + 3)
	m.drawmeridians(np.arange(-180, 180, lontix), labels=[0, 0, 0, 1], linewidth=0.25, zorder=zordcoast + 3)
        plt.savefig('/users/rsg/utils/web_visible_public_share/blo/files/AlterEco/PP_plots/' + os.path.basename(glider_EGO_file).replace('.nc','_sensor_coverage'), bbox_inches='tight')
        plt.close(fig1)

        #plots
        fig2 = plt.figure(figsize=(20,20), dpi=300)
        gs = gridspec.GridSpec(5, 1)
        gs.update(wspace=0.01, hspace=0.5)
        plt.rcParams.update({'font.size': fsz})

        # plot sensor loads
        if CHLA_FOUND:
            axes1 = plt.subplot(gs[0, 0])
            ymin = -3
            ymax = 1
            plot_trace(axes1, TIME, np.log10(CHLA), CHLA_COL, 'CHLA [mg.l$^{-1}$]', xmin, xmax, xticks, xlabels, ymin, ymax, log=True)        

        # plot sensor loads
        if BBP_FOUND:
            axes2 = plt.subplot(gs[1, 0])
            ymin = -4
            ymax = -2
            plot_trace(axes2, TIME, np.log10(BBP), BBP_COL, 'BBP [m$^{-1}$]', xmin, xmax, xticks, xlabels, ymin, ymax, log=True)

        # plot sensor loads
        if CDOM_FOUND:
            axes3 = plt.subplot(gs[2, 0])
            ymin = -1
            ymax = 1
            plot_trace(axes3, TIME, np.log10(CDOM), CDOM_COL, 'CDOM [ppb]', xmin, xmax, xticks, xlabels, ymin, ymax, log=True)

        # plot sensor loads
        if PAR_FOUND:
            axes4 = plt.subplot(gs[3, 0])
            ymin = 0
            ymax = np.nanmean(PAR) + 3*np.nanstd(PAR)
            plot_trace(axes4, TIME, PAR, PAR_COL, 'PAR [$\mu$mol.m$^{-2}$.s]', xmin, xmax, xticks, xlabels, ymin, ymax)

        # plot sensor loads
        if DOXY_FOUND:
            axes5 = plt.subplot(gs[4, 0])
            ymin = 0
            ymax = np.nanmean(DOXY) + 3*np.nanstd(DOXY)
            plot_trace(axes5, TIME, DOXY, DOXY_COL, 'DOXY [$\mu$mol.l$^{-1}$]', xmin, xmax, xticks, xlabels, ymin, ymax)

        if CHLA_FOUND or BBP_FOUND or CDOM_FOUND or PAR_FOUND or DOXY_FOUND:
            plt.savefig('/users/rsg/utils/web_visible_public_share/blo/files/AlterEco/PP_plots/' + os.path.basename(glider_EGO_file).replace('.nc','_sensor_QC'), bbox_inches='tight')
            plt.close(fig2)
        else:
            print('No sensor data to plot')

    axesA.set_yticks(yticks)
    axesA.set_yticklabels(ylabels)
    axesA.set_xticks(xticks)
    axesA.set_xticklabels(xlabels,rotation=90)
    axesA.set_xlim([xmin, xmax])
    axesA.set_ylim([0.0, 0.6])
    figA.savefig('/users/rsg/utils/web_visible_public_share/blo/files/AlterEco/PP_plots/Sensor_loads.png')
    plt.close(figA)
#-EOF---
