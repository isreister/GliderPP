#!/usr/bin/env python

import glob
import os, shutil
import netCDF4 as nc
import numpy as np
import datetime
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
from matplotlib import gridspec
import argparse
from matplotlib.colors import LinearSegmentedColormap
from mpl_toolkits.basemap import Basemap

#-func--------------------------------------------------------------------------
def running_mean(values, window):
    weights = np.repeat(1.0, window)/window
    sma = np.convolve(values, weights, 'valid')
    return sma

def add_date_bars(ax,year_min,year_max,ymin_val,ymax_val,yref=datetime.datetime(1970,1,1)):

    tags=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    for YY in range(year_min,year_max+1):
    	for MM in range(1,13):
    		tmin = (datetime.datetime(YY,MM,1)-yref).total_seconds()/86400
    		if MM==12:
    		    tmax = (datetime.datetime(YY+1,1,1)-yref).total_seconds()/86400
    		else:
    		    tmax = (datetime.datetime(YY,MM+1,1)-yref-datetime.timedelta(days=1)).total_seconds()/86400
    		if np.mod(MM,2) == 0:
    			plt.fill_between([tmin,tmax],[ymin_val,ymin_val],[ymax_val,ymax_val],color='0.75',zorder=1)
    			plt.text(tmin,ymax_val*0.95,tags[MM-1],color='k',fontsize=24,zorder=20, clip_on=True)
    		else:
    			plt.text(tmin,ymax_val*0.95,tags[MM-1],color='k',fontsize=24,zorder=20, clip_on=True)

#-args--------------------------------------------------------------------------
parser = argparse.ArgumentParser()
#-input vars--------------------------------------------------------------------
parser.add_argument('-r', '--runtype', type=str,\
                    default = '.txt')
parser.add_argument('-m', '--method', type=str,\
                    default = '')
#-input vars end----------------------------------------------------------------
args   = parser.parse_args()
        
#-main--------------------------------------------------------------------------
if __name__ == "__main__":

    pp_dir1 = os.path.join('/data/datasets/Projects/AlterEco/Glider_data/BODC_pp_data/EGO/Cabot_20190312/EGO_517_Cabot')
    pp_dir2 = os.path.join('/data/datasets/Projects/AlterEco/Glider_data/BODC_pp_data/EGO/Cook_20171115/EGO_441_Cook')
    pp_dir3 = os.path.join('/data/datasets/Projects/AlterEco/Glider_data/BODC_pp_data/EGO/Coprolite_20181202/EGO_500_Coprolite')
    pp_dir4 = os.path.join('/data/datasets/Projects/AlterEco/Glider_data/BODC_pp_data/EGO/Dolomite_20181202/EGO_499_Dolomite')
    pp_dir5 = os.path.join('/data/datasets/Projects/AlterEco/Glider_data/BODC_pp_data/EGO/EGO_454_Cabot')
    pp_dir6 = os.path.join('/data/datasets/Projects/AlterEco/Glider_data/BODC_pp_data/EGO/EGO_477_Dolomite')
    pp_dir7 = os.path.join('/data/datasets/Projects/AlterEco/Glider_data/BODC_pp_data/EGO/EGO_478_Eltanin')
    pp_dir8 = os.path.join('/data/datasets/Projects/AlterEco/Glider_data/BODC_pp_data/EGO/EGO_481_Kelvin')
    pp_dir9 = os.path.join('/data/datasets/Projects/AlterEco/Glider_data/BODC_pp_data/EGO/Stella_20180207/EGO_494_Stella')
    pp_dir10 = os.path.join('/data/datasets/Projects/AlterEco/Glider_data/BODC_pp_data/humpback_UEA/UEA_579_humpback')

    pp_dirs = [pp_dir1, pp_dir2, pp_dir3, pp_dir4, pp_dir5, pp_dir6, pp_dir7, pp_dir8, pp_dir9, pp_dir10]
   
    fsz = 24
    smooth_win = 100
    runtype = args.runtype
    method = args.method
    date_zero = datetime.datetime(2017,11,1)

    aggregate_months = []
    aggregate_years = []
    aggregate_PP = []
    aggregate_tags = []

    aggregate_times_smooth = []
    aggregate_PP_smooth = []

    for pp_dir in pp_dirs:
        glider_tag = os.path.basename(pp_dir)
        aggregate_tags.append(glider_tag)
        pp_files = glob.glob(os.path.join(pp_dir,'pp_profile_station_??????'+method+runtype))
        print('Found: '+str(len(pp_files))+' files')
        pp_int = []
        ZEU = []
        days_since_deployment = []
        months = []
        years = []
        lons = []
        lats = []

        pp_array = np.ones((200,len(pp_files)))*np.nan

        count = -1
        for pp_file in sorted(pp_files):
            count = count + 1
            telemetry_file = pp_file.replace('pp_profile','telemetry').replace(args.runtype,'.txt')

            if np.mod(count,100) == 0:
                print(pp_file)
                print(telemetry_file)

            pp_vars =  np.genfromtxt(pp_file,dtype=str,delimiter='\t')
            depth = np.asarray(pp_vars[1:,0]).astype(float)
            par = np.asarray(pp_vars[1:,6]).astype(float)

            if sum(np.isfinite(par)) == 0:
                ZEU.append(np.nan)
                pp_int.append(np.nan)
            else:
                ZEU.append(depth[par<0.01*par[0]][0])
                pp = np.asarray(pp_vars[1:,1]).astype(float)*1000.00
        
                # scrape impossible results
                pp[pp>1e5] = np.nan
                pp[pp<0] = 0
                pp_int.append(np.nansum(pp*abs(np.nanmean(depth[0:-1]-depth[1:]))))
                pp_array[0:int(np.nanmax(depth))+1,count] = pp

            telemetry_vars =  np.genfromtxt(telemetry_file,dtype=str,delimiter=' ')

            lons.append(float(telemetry_vars[1,1]))
            lats.append(float(telemetry_vars[2,1]))

            year = int(telemetry_vars[3,1])
            month = int(telemetry_vars[4,1])
            day = int(telemetry_vars[5,1])
            hours = int(telemetry_vars[0,1].split(':')[0])
            minutes = int(telemetry_vars[0,1].split(':')[1])
            if count == 0:
                date_max = (datetime.datetime(2019,07,31) - date_zero).total_seconds()/86400
            days_since_deployment.append((datetime.datetime(year,month,day,hours,minutes,0)-date_zero).total_seconds()/86400)
            months.append(month)
            years.append(year)

        months = np.asarray(months)
        years = np.asarray(years)
        days_since_deployment = np.asarray(days_since_deployment).astype(float)
        pp_int = np.asarray(pp_int).astype(float)
        pp_int[pp_int <= 1.0] = np.nan
        ZEU = np.asarray(ZEU).astype(float)*-1
        smooth_ZEU = running_mean(ZEU[np.isfinite(ZEU)],smooth_win)

        lons = np.asarray(lons).astype(float)
        lats = np.asarray(lats).astype(float)
   
        # daily smoothing
        days_smooth = []
        smooth_ZEU2 = []
        smooth_PP2 = []
        for ii in np.unique(days_since_deployment.astype(int)):
            days_smooth.append(ii)
            smooth_ZEU2.append(np.nanmean(ZEU[(days_since_deployment > ii) & (days_since_deployment < ii+1)]))
            smooth_PP2.append(np.nanmean(pp_int[(days_since_deployment > ii) & (days_since_deployment < ii+1)]))

        days_smooth = np.asarray(days_smooth).astype(float)
        smooth_ZEU2 = np.asarray(smooth_ZEU2).astype(float)
        smooth_PP2 = np.asarray(smooth_PP2).astype(float)
        
        print('Plotting....')
        
        fig = plt.figure(figsize=(30,20))
        plt.rcParams.update({'font.size': fsz})
        gs = gridspec.GridSpec(3, 1, height_ratios=[10,10,1])
        axes1 = plt.subplot(gs[0, 0])

        ymin_val = 0.0
        ymax_val = 1750.0

        plt.scatter(days_since_deployment,pp_int,s=20,color=plt.cm.Greens(1.0),alpha=0.5,edgecolors='face',zorder=5)
        p1 = plt.plot(days_smooth+0.5, smooth_PP2,'k', linewidth=3,zorder=6)
        plt.plot(days_since_deployment,np.ones(np.shape(days_since_deployment))*np.nanmean(pp_int),'b--',alpha=0.5, zorder=4, linewidth=2)
        add_date_bars(axes1,2016,2019,ymin_val,ymax_val,yref=date_zero)

        # add to aggregates: smooth
        aggregate_times_smooth.append(days_smooth+0.5)
        aggregate_PP_smooth.append(smooth_PP2)
        # add to aggregates
        if 'HUMPBACK' in glider_tag.upper():
            print('Skipping bad glider')
        else:
            aggregate_months.append(months)
            aggregate_years.append(years)
            aggregate_PP.append(pp_int)

        leg = plt.legend(p1,['Daily averaged primary production'], loc="upper center",\
            bbox_to_anchor=(0.25, -0.04), ncol=1, fontsize=20)
        leg.get_frame().set_linewidth(0.0)

        t_deploy =datetime.datetime.strftime(date_zero,'%d-%m-%Y')
        plt.ylabel('Primary production [mgC.m$^{-2}$.d$^{-1}$]')
 
        #plt.xlim([0,date_max])
        plt.xlim([np.nanmin(days_since_deployment),np.nanmax(days_since_deployment)])
        plt.ylim([ymin_val,ymax_val])

        if '441' in glider_tag or '477' in glider_tag or '478' in glider_tag or '481' in glider_tag \
          or '494' in glider_tag or '499' in glider_tag or '500'in glider_tag:
            glider_tag = glider_tag +'*'

        plt.title('Primary production: '+glider_tag)

        axes2 = plt.subplot(gs[1, 0])

        pp_max = np.nanmean(pp_array)+3*np.nanstd(pp_array)
        pp_array[pp_array > pp_max] = pp_max
        [pp_array < 0.0] = 0.0
        plot1 = plt.pcolormesh(days_since_deployment,np.arange(200)*-1,pp_array, cmap=plt.cm.Greens, vmin=0.0, vmax=pp_max)

        p1 = plt.plot(days_smooth+0.5, smooth_ZEU2,'m', linewidth=3,zorder=6)

        leg = plt.legend(p1,['Daily averaged euphotic depth'], loc="upper center",\
           bbox_to_anchor=(0.75, 1.1), ncol=1, fontsize=20)
        leg.get_frame().set_linewidth(0.0)

        #plt.xlim([0,date_max])
        plt.xlim([np.nanmin(days_since_deployment),np.nanmax(days_since_deployment)])
        plt.ylim([np.nanmin(smooth_ZEU)*1.2,0])
        plt.xlabel('Days since '+t_deploy)
        plt.ylabel('Depth [m]')

        axes3 = plt.subplot(gs[2, 0])
        cbar = plt.colorbar(plot1, cax=axes3, orientation='horizontal')
        cbar.set_label('Primary production by depth [mgC.m$^{-3}$.d$^{-1}$]', fontsize=fsz)

        plot_map = False
        if plot_map:
            axes4 = plt.subplot(gs[:, 1])
        
            pad = 1
            lonmin = np.nanmin(lons)-pad
            lonmax = np.nanmax(lons)+pad
            latmin = np.nanmin(lats)-pad
            latmax = np.nanmax(lats)+pad
            lattix = 1
            lontix = 1
            zordcoast = 1

            m = Basemap(llcrnrlon=lonmin, llcrnrlat=latmin, urcrnrlon=lonmax,\
		urcrnrlat=latmax, resolution='h', projection='cyl')

            xx, yy = m(lons,lats)
            m.plot(xx, yy, 'r', linewidth=1.0, zorder = 100)

            m.fillcontinents(color=[0.4, 0.4, 0.4], zorder=zordcoast)
            m.drawcoastlines(color='k', linewidth=0.25, zorder=zordcoast + 1)
            m.drawcountries(color='k', linewidth=0.15, zorder=zordcoast + 2)

            m.drawparallels(np.arange(-80, 90, lattix), labels=[1, 0, 0, 0], linewidth=0.25, zorder=zordcoast + 3)
            m.drawmeridians(np.arange(-180, 180, lontix), labels=[0, 0, 0, 1], linewidth=0.25, zorder=zordcoast + 3)
    
        plt.savefig('/users/rsg/utils/web_visible_public_share/blo/files/AlterEco/PP_plots/'+glider_tag+method+'_'+runtype+'_PP.png')
    print('Aggregate plotting...')

    fig = plt.figure(figsize=(30,20))
    plt.rcParams.update({'font.size': fsz})
    gs = gridspec.GridSpec(2, 1, height_ratios=[5,10])
    axes1 = plt.subplot(gs[0, 0])
    axes2 = plt.subplot(gs[1, 0])

    flat_months = np.asarray([item for sublist in aggregate_months for item in sublist])
    flat_years = np.asarray([item for sublist in aggregate_years for item in sublist])
    flat_pp = np.asarray([item for sublist in aggregate_PP for item in sublist])

    mm_mins = []
    mm_maxs = []
    mm_aves = []
    mm_std_devs = []

    ym_mins = []
    ym_maxs = []
    ym_aves = []
    ym_std_devs = []

    for mm in np.arange(1,13):
        ii = np.where((flat_months == mm))[0]
        if len(ii) == 0:
            print('Nothing for month '+str(mm))
            mm_mins.append('Nan')
            mm_maxs.append('Nan')
            mm_aves.append('Nan')
            mm_std_devs.append('Nan')
        else:
            print('Processing month '+str(mm))
            mm_mins.append(str(np.nanmin(flat_pp[ii])))
            mm_maxs.append(str(np.nanmax(flat_pp[ii])))
            mm_aves.append(str(np.nanmean(flat_pp[ii])))
            mm_std_devs.append(str(np.nanstd(flat_pp[ii])))

    print('-------------------------')

    for yy in np.arange(2017,2020):
        for mm in np.arange(1,13):
            ii = np.where((flat_months == mm) & (flat_years == yy))[0]
            if len(ii) == 0:
                print('Nothing for month '+str(yy)+':'+str(mm))
                ym_mins.append('Nan')
                ym_maxs.append('Nan')
                ym_aves.append('Nan')
                ym_std_devs.append('Nan')
            else:
                print('Processing month '+str(yy)+':'+str(mm))
                ym_mins.append(str(np.nanmin(flat_pp[ii])))
                ym_maxs.append(str(np.nanmax(flat_pp[ii])))
                ym_aves.append(str(np.nanmean(flat_pp[ii])))
                ym_std_devs.append(str(np.nanstd(flat_pp[ii])))

    with open('/users/rsg/utils/web_visible_public_share/blo/files/AlterEco/PP_plots/aggregate_PP_clim'+runtype+'.txt','w') as the_file:
        the_file.write('Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec'+'\n')
        the_file.write(','.join(mm_mins)+'\n')
        the_file.write(','.join(mm_maxs)+'\n')
        the_file.write(','.join(mm_aves)+'\n')
        the_file.write(','.join(mm_std_devs)+'\n')

    with open('/users/rsg/utils/web_visible_public_share/blo/files/AlterEco/PP_plots/aggregate_PP_mons'+runtype+'.txt','w') as the_file:
        the_file.write('Jan17, Feb17, Mar17, Apr17, May17, Jun17, Jul17, Aug17, Sep17, Oct17, Nov17, Dec17'\
                      +', Jan18, Feb18, Mar18, Apr18, May18, Jun18, Jul18, Aug18, Sep18, Oct18, Nov18, Dec18'\
                      +', Jan19, Feb19, Mar19, Apr19, May19, Jun19, Jul19, Aug19, Sep19, Oct19, Nov19, Dec19' + '\n')
        the_file.write(','.join(ym_mins)+'\n')
        the_file.write(','.join(ym_maxs)+'\n')
        the_file.write(','.join(ym_aves)+'\n')
        the_file.write(','.join(ym_std_devs)+'\n')


    count = -1
    for time, trace, tag in zip(aggregate_times_smooth, aggregate_PP_smooth, aggregate_tags):
        count = count + 1
        if '441' in tag or '477' in tag or '478' in tag or '481' in tag  or '494' in tag or '499' in tag or '500'in tag:
            tag = tag +'*'
        
        plot_col = plt.cm.Set1(float(count)/float(len(pp_dirs)))

        axes1.plot(time,np.ones(len(time))*count+1, color=plot_col, linewidth=2)
        axes1.annotate(tag, (time[0], count+1.25), xycoords='data', color=plot_col)
        axes2.plot(time, trace , color=plot_col, linewidth=2)

    axes1.tick_params(axis='y', which='both', left=False, right=False, labelleft=False)

    plt.sca(axes1)
    plt.xlim([0,date_max])
    plt.ylim([0.5, 12])

    plt.sca(axes2)

    add_date_bars(axes2,2016,2019,0,2400,yref=date_zero)
    plt.title('Primary production across all gliders')
    plt.ylabel('Primary production [mgC.m$^{-2}$.d$^{-1}$]')
    plt.xlabel('Days since '+t_deploy)
    plt.xlim([0,date_max])
    plt.ylim([0, 1200])
    plt.savefig('/users/rsg/utils/web_visible_public_share/blo/files/AlterEco/PP_plots/aggregate_PP_v3'+method+'_'+runtype+'.png')

#-EOF--
