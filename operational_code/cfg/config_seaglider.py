#
# INPUT Config File for Seaglider variables
#
# Includes all required files paths, parameters and authentications
#
# depth_var:	variables used to determine glider depth
# depth_pol:    increasing depth is positive of negative value?
# depth_min:	minimum depth ot use in interpolation
# depth_max:	maximum depth to use in interpolation
# depth_bin:	dZ to use in interpolation
# record_var:	seaglider data record variable (usually sg_data_point)
# lon_var:	longitude variable
# lat_var:	latitude variable
# t_var:	time variable
# t_ref:	glider reference time
# t_base:	glider time unit
# allowed:	variables to process
#-------------------------------------------------------------------------------
depth_var=depth
depth_pol=positive
depth_min=0
depth_max=1000
depth_bin=5
record_var=sg_data_point
alt_record_var=time
lon_var=longitude
lat_var=latitude
profile_var=PROFILE_NUMBER
profile_var_read=profile_num
t_var=time
profile_var=profile_number
t_ref=1970-01-01 00:00:00
t_base=seconds
lon_var_backup=log_gps_lon
lat_var_backup=log_gps_lat
sgolay_win=51
sgolay_smooth=9
#allowed_vars=vert_speed_gsm,vert_speed,time,theta,temperature,temperature_rawqqq,speed_gsm,speed,salinity_raw,salinity,pressure,horz_speed_gsm,horz_speed,glide_angle_gsm,glide_angle,depth,ctd_time,ctd_depth,ctd_pressure,conductivity,conductivity_raw,buoyancy,density,density_insitu,east_displacement_gsm,east_displacement,north_displacement_gsm,north_displacement,dissolved_oxygen_sat,sound_velocity,sigma_theta,sigma_t,longitude_gsm,longitude,latitude_gsm,latitude,eng_wlbbfl2_temp,eng_wlbbfl2_FL2sig,eng_wlbbfl2_FL2ref,eng_wlbbfl2_FL1sig,eng_wlbbfl2_FL1ref,eng_wlbbfl2_BB1sig,eng_wlbbfl2_BB1ref,eng_wlbbfl2_BB2sig,eng_wlbbfl2_BB2ref,eng_vbdCC,eng_sbect_tempFreq,eng_sbect_condFreq,eng_rollCtl,eng_rollAng,eng_rec,eng_qsp_PARuV,eng_pitchCtl,eng_pitchAng,eng_head,eng_elaps_t_0000,eng_elaps_t,eng_depth,eng_aa4330_Temp,eng_aa4330_TCPhase,eng_aa4330_O2,eng_aa4330_CalPhase,eng_aa4330_AirSat,eng_GC_phase,aanderaa4330_results_time,aanderaa4330_instrument_dissolved_oxygen,aanderaa4330_dissolved_oxygen
allowed_vars=_FL1SIG,_FL2SIG,_BB1SIG,_BB2SIG,ENG_AA4330F_O2,_PARUV,TEMP,CNDC,PRES,TIME,LONGITUDE,LATITUDE
allowed_heads=CHLA,CDOM,SCATTER,SCATTER,DOXY,PAR,TEMP,CNDC,PRES,TIME,LONGITUDE,LATITUDE
allowed_exact=0,0,0,0,0,0,1,1,1,1,1,1
#-------------------------------------------------------------------------------,

