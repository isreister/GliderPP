#!/usr/bin/env python
'''
Description:    Common tools

Version: 	v1.0 12/2017
	 	v1.1 08/2018
                v2.0 05/2019

Ver. hist:      v2.0 is current

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
import datetime
import numpy as np
import ephem
import pysolar
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
import os
import pytz

#---
def running_mean(values, window):
    weights = np.repeat(1.0, window)/window
    sma = np.convolve(values, weights, 'valid')
    return sma

#---
def  ref_index(S,T,lam):
    '''
    refractive index of seawater; Quan and Fry, 1995
    '''
    n0 = 1.31405
    n1 = 1.779e-4
    n2 = -1.05e-6
    n3 = 1.6e-8
    n4 = -2.02e-6
    n5 = 15.868
    n6 = 0.01155
    n7 = -0.00423
    n8 = -4382
    n9 = 1.1455e6

    n = n0 + (n1 +n2*T +n3*T**2)*S + n4*T**2 + (n5 + n6*S + n7*T)/lam + \
        n8/lam**2 +n9/lam**3

    return n

#---
def glider_times(lat, lon, tref, time, to_UTC=0, correct_time=True):
                           
    glider_ephem = ephem.Observer()
    glider_ephem.horizon = '0' # actual sunrise
    glider_ephem.lat = str(lat)
    glider_ephem.lon = str(lon)

    if correct_time:
        python_UTC_datetime = datetime.datetime.strptime(tref,'%Y-%m-%d %H:%M:%S') \
                              + datetime.timedelta(seconds=int(time)) \
                              - datetime.timedelta(hours=to_UTC)
    else:
        python_UTC_datetime = datetime.datetime.fromordinal(int(time)\
                              - 366) + datetime.timedelta(days=time%1)\
                              - datetime.timedelta(hours=to_UTC)
    
    glider_ephem.date = python_UTC_datetime
    last_sunrise = glider_ephem.previous_rising(ephem.Sun()).datetime()
    last_sunset = glider_ephem.previous_setting(ephem.Sun()).datetime()
    next_sunset = glider_ephem.next_setting(ephem.Sun()).datetime()

    if glider_ephem.date.datetime() > last_sunrise and \
      glider_ephem.date.datetime() < next_sunset and \
      last_sunset < last_sunrise:
        is_day = 1
        is_night = 0
    else:
        is_day = 0
        is_night = 1
    
    return is_night, is_day, last_sunrise, next_sunset

def check_remask_var(var,vmin,vmax):
    if 'Masked' in str(type(var)):
        nvar = var.data
        nvar[var.mask] = np.nan
        nvar[nvar>vmax] = np.nan
        nvar[nvar<vmin] = np.nan
    else:
        nvar = var
    return nvar

def profile_specifics(TIME,TREF,LAT,LON,DEPTH,glider_bathy,\
                      CHLA,PAR,N_smooth=3,surface_depth=20,\
                      gbath_lim=10,to_UTC=0,correct_time=True,\
                      skip_chl=False):

    # is_night:		night time profile
    # is_day:		day time profile
    # is_bad:		profile probably no good (weak)
    # is_good:		profile probably ok (weak)
    # is_no_DCM_night:	night time, no DCM
    # is_day_good_PAR:	good PAR daytime profiles, no increase with depth

    is_night        = 0
    is_day          = 0
    is_bad          = 0
    is_good         = 0
    is_no_DCM_night = 0
    is_day_good_PAR = 0

    if np.isnan(TIME) or np.isnan(LON) or np.isnan(LAT):
       print('Bad coordinate data')
       return is_night, is_day, is_bad, is_good, is_no_DCM_night, \
              is_day_good_PAR

    is_night, is_day, last_sunrise, next_sunset = \
      glider_times(LAT, LON, TREF, TIME, to_UTC=to_UTC, correct_time=correct_time)

    # short cut if we don't have CHL data
    if skip_chl:
        is_day_good_PAR = is_day
        return is_night, is_day, is_bad, is_good, is_no_DCM_night, \
           is_day_good_PAR

    if np.sum(np.isfinite(CHLA)) < 2*N_smooth+1 or glider_bathy < gbath_lim:
        is_bad = 1
    else:
        is_good = 1

    if is_night == 1:
        try:
            fn = interp1d(DEPTH[np.isfinite(CHLA) & np.isfinite(DEPTH)],\
                          CHLA[np.isfinite(CHLA) & np.isfinite(DEPTH)], \
                 kind='cubic',fill_value="extrapolate")

            CHLA_interp = fn(DEPTH[np.isfinite(DEPTH)])
            CHLA_smooth  = np.concatenate((CHLA_interp[0:N_smooth],\
                                     running_mean(CHLA_interp,2*N_smooth+1),\
                                     CHLA_interp[-N_smooth-1:-1]))

            dcheck = DEPTH[np.isfinite(DEPTH)]
            if np.nanmax(dcheck) < surface_depth:
                is_no_DCM_night = 0
            else:
                ii = np.where((dcheck < surface_depth))[0]
                jj = np.where((dcheck > surface_depth))[0]
                if np.nanmax(CHLA_smooth[ii]) >= np.nanmax(CHLA_smooth[jj]):
                    is_no_DCM_night = 1
        except:
            pass
    else:
        is_day_good_PAR = 1

    return is_night, is_day, is_bad, is_good, is_no_DCM_night, \
           is_day_good_PAR

def fresnel_refl(lat,lon,time,tref,depth,PAR,is_day_good_PAR,WS,SST,SSS,to_UTC=0,\
                 correct_time=True):

    deg2rad = np.pi/180
    rho_a   = 1.2e-3
    r_tot = 0.0
    theta_a = np.nan

    # ignore night time and bad PAR profiles
    if is_day_good_PAR == 0.0 or np.isnan(lat) or np.isnan(lon)\
      or np.isnan(time):
        print('Cannot correct Fresnel, reflectance set to 0')
    else:      
        if correct_time:
            python_UTC_datetime = datetime.datetime.strptime(tref,'%Y-%m-%d %H:%M:%S') \
                                  + datetime.timedelta(seconds=int(time)) \
                                  - datetime.timedelta(hours=to_UTC)
        else:
            python_UTC_datetime = datetime.datetime.fromordinal(int(time)\
                                  - 366) + datetime.timedelta(days=time%1)\
                                  - datetime.timedelta(hours=to_UTC)

        python_UTC_datetime = pytz.utc.localize(python_UTC_datetime)

        # get solar zenith
        theta_a = deg2rad*(90.0 - pysolar.solar.get_altitude_fast(lat, lon,\
                  python_UTC_datetime))

        # get refractive indices (using average of 450/700 for sea-water)

        n_a     = 1.000277
        n_w1    = ref_index(SSS,SST,450.0)
        n_w2    = ref_index(SSS,SST,700.0)
        n_w     = (n_w1 + n_w2)/2.0

        # get theta_w
        theta_w = np.arcsin(n_a/n_w * np.sin(theta_a))

        # calculate fresnel reflectance
        rr = 0.5*(np.sin(theta_a-theta_w))**2 \
                 / (np.sin(theta_a+theta_w))**2 \
                 + 0.5*(np.tan(theta_a-theta_w))**2 \
                 / (np.tan(theta_a+theta_w))**2

        # calculate foam effects
        if WS < 7.0:
            c_n = (6.2e-4 + 1.56e-3)/WS
            r_f = rho_a*c_n*2.2e-5*WS**2-4.0e-4
        else:
            c_n = 0.49-3 + 0.065*WS
            r_f = (rho_a*c_n*4.5e-5 - 4.0e-5)*WS**2

        if r_f == 0.0:
            r_diff = 0.066
        else:
            r_diff = r_f + 0.057

        # get total reflectance
        r_tot = r_diff + rr

    return r_tot, theta_a

def get_E0(E_0_minus,r_tot):
    '''
    Calculate broadband PAR above water
    '''
    # temporary measure: contacted Victoria about this
    R = 0.04
    # Hemsley 2015
    r_bar   = 0.48
    # cross the air/water interface
    if np.isnan(r_tot):
        E_0_plus = E_0_minus.copy()
    else:
        E_0_plus = E_0_minus*(1-R*r_bar)/(1-r_tot)
    return E_0_plus

def findZEU(depth,par,verbose=False, logging=None):
    '''
    finds 1% light level from surface value
    '''
    ii = np.where(np.isfinite(depth) & np.isfinite(par))
    par = par[ii]
    depth = depth[ii]
    if depth[0] > depth[-1]:
        depth = depth[::-1]
        par = par[::-1]

    ii = np.where((par >= np.nanmax(par[0])/100.))[0]
    if np.shape(ii)[0] == 0:
        Zeu = np.nan
    else:
        Zeu = depth[ii[-1]]
    return Zeu

def output_text(station_number,times,tref,depths,chl,par,
                wspd,\
                rh,\
                tcwv,\
                o3,\
                mslp,\
                cloud,\
                chl_traj,\
                zeu_traj,\
                E_0_plus,\
                MLD,\
                ZEU,\
                lon,lat,\
                temperature,outdir,chlname,parname,is_day,verbose=False, logging=None,
                correct_time=True,outfile_suffix='.txt'):
    '''
    Outputs Chl & PAR profiles in text format compatible with Morel19 PP model.
    Also produces telemetry files for use in PAR model.
    '''

    nrows=0
    # chl file
    this_chl_file = outdir+'/'+chlname+'_station_'\
                    +str(int(station_number)).zfill(6)+outfile_suffix
    this_par_file = outdir+'/'+parname+'_station_'\
                    +str(int(station_number)).zfill(6)+outfile_suffix

    if os.path.exists(this_chl_file):
        os.chmod(this_chl_file, 0o777)
        os.remove(this_chl_file)

    if os.path.exists(this_par_file):
        os.chmod(this_par_file, 0o777)
        os.remove(this_par_file)
    
    with open(this_chl_file,"a") as chl_file:
        with open(this_par_file,"a") as par_file:
            print('Writing: '+this_chl_file)
            print('Writing: '+this_par_file)
            if logging:
                logging.info('Writing: '+this_chl_file)
                logging.info('Writing: '+this_par_file)

            for iter_val in np.arange(0,len(times)):
                # skip nan value rows: bit dangerous as CHL and PAR are linked
                if np.isnan(chl[iter_val]) or np.isnan(par[iter_val]) or np.isnan(depths[iter_val]):
                    continue

                nrows = nrows+1
                if correct_time:
                    if 'numpy.ma.core.MaskedArray' in str(type(times)):
                        times = times.data
                        times = np.ma.filled(times.astype(float), np.nan)

                    python_datetime = datetime.datetime.strptime(tref,'%Y-%m-%d %H:%M:%S') +\
                                      datetime.timedelta(seconds=int(np.nanmean(times)))
                else:
                    matlab_datenum  = np.nanmean(times)
                    python_datetime = datetime.datetime.\
                                      fromordinal(int(matlab_datenum)\
                                      - 366) + \
                                      datetime.timedelta(days=matlab_datenum%1)

                formatted_time  = python_datetime.strftime("%H:%M")
                #formatted_depth = str(abs(int(depths[iter_val])))
                formatted_depth = str(abs(depths[iter_val]))
                formatted_chl   = str(chl[iter_val])
                formatted_par   = str(par[iter_val])
                chl_file.write(formatted_time  + ' ' +\
                                  formatted_depth + ' ' +\
                                  formatted_chl   + '\n')
                par_file.write(formatted_time  + ' ' +\
                                  formatted_depth + ' ' +\
                                  formatted_par   + '\n')

    os.chmod(this_chl_file, 0o777)
    os.chmod(this_par_file, 0o777)

    if nrows==0:
        print('Empty (deleting): '+this_chl_file)
        print('Empty (deleting): '+this_par_file)
        if logging:
            logging.info('Empty (deleting): '+this_chl_file)
            logging.info('Empty (deleting): '+this_par_file)
        os.remove(this_chl_file)
        os.remove(this_par_file)
      
    else:
        this_file = outdir+'/telemetry' + '_station_'\
                    +str(int(station_number)).zfill(6)+outfile_suffix

        if os.path.exists(this_file):
            os.chmod(this_file, 0o777)
            os.remove(this_file)
         
        with open(this_file,"a") as telemetry_file:
            print('Writing: '+this_file)
            if logging:
                logging.info('Writing: '+this_file)

            formatted_lon  = str(np.nanmean(lon))
            formatted_lat  = str(np.nanmean(lat))
            formatted_temp = str(np.nanmean(temperature))
            formatted_WSPD  = str(wspd)
            formatted_RH    = str(rh)
            formatted_TCWV  = str(tcwv)
            formatted_O3    = str(o3)
            formatted_MSLP  = str(mslp)
            formatted_CLOUD = str(cloud)
            formatted_E0p   = str(E_0_plus)
            formatted_MLD   = str(MLD)
            formatted_ZEU   = str(ZEU)
            formatted_CHLt  = str(chl_traj)
            formatted_ZEUt  = str(zeu_traj)
            formatted_dayt  = str(is_day)

            if correct_time:
                python_datetime = datetime.datetime(1970,1,1)+\
                                  datetime.timedelta(seconds=int(np.nanmean(times)))
            else:
                matlab_datenum  = np.nanmean(times)
                python_datetime = datetime.datetime.\
                                  fromordinal(int(matlab_datenum)\
                                  - 366) + \
                                  datetime.timedelta(days=matlab_datenum%1)

            formatted_year  = python_datetime.strftime("%Y")
            formatted_month = python_datetime.strftime("%m")
            formatted_day   = python_datetime.strftime("%d")
            formatted_jday  = python_datetime.strftime("%j")

            telemetry_file.write('time '+formatted_time + '\n')
            telemetry_file.write('longitude '+formatted_lon + '\n')
            telemetry_file.write('latitude '+formatted_lat + '\n')
            telemetry_file.write('year '+formatted_year + '\n')
            telemetry_file.write('month '+formatted_month + '\n')
            telemetry_file.write('day '+formatted_day + '\n')
            telemetry_file.write('jday '+formatted_jday + '\n')
            telemetry_file.write('temp '+formatted_temp + '\n')
            telemetry_file.write('wspd '+formatted_WSPD + '\n')
            telemetry_file.write('rh '+formatted_RH + '\n')
            telemetry_file.write('tcwv '+formatted_TCWV + '\n')
            telemetry_file.write('o3 '+formatted_O3 + '\n')
            telemetry_file.write('mslp '+formatted_MSLP + '\n')
            telemetry_file.write('cloud '+formatted_CLOUD + '\n')
            telemetry_file.write('E0p '+formatted_E0p + '\n')
            telemetry_file.write('MLD '+formatted_MLD + '\n')
            telemetry_file.write('ZEU '+formatted_ZEU + '\n')
            telemetry_file.write('CHL_traj '+formatted_CHLt + '\n')
            telemetry_file.write('ZEU_traj '+formatted_ZEUt + '\n')
            telemetry_file.write('is_day '+formatted_dayt)

        os.chmod(this_file, 0o777)

#-EOF--
