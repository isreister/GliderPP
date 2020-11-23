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
record_var=time
lon_var=lon
lat_var=lat
t_var=time
profile_var=PROFILE_NUMBER
profile_var_read=profile_num
t_ref=0001-01-01 00:00:00
t_base=matlab
nc_tag=_xing_eo.nc
lon_var_backup=log_gps_lon
lat_var_backup=log_gps_lat
# values tested on Dolomite; very messy
sgolay_win=51
sgolay_smooth=9
allowed_vars=Chlorophyll,CDOM,Scatter_650,Scatter_650,ENG_AA4330F_O2,PAR,temp,salinity,pressure,time,lon,lat,PROFILE_NUMBER
allowed_heads=CHLA,CDOM,SCATTER,SCATTER,DOXY,PAR,TEMP,SAL,PRES,TIME,LONGITUDE,LATITUDE,PROFILE_NUMBER
allowed_exact=1,1,1,1,1,1,1,1,1,1,1,1,1
#quench_methods=Xing,Biermann,Hemsley,Swart
quench_methods=Xing
correction_file_suffix=_xing_eo.txt
#assume in umol/m2/sec: odd conversion
PAR_conversion=10.0
#-------------------------
# sensitivity test choices
#-------------------------
force_use_quench_method=1
force_use_EO_par=1
#-------------------------------------------------------------------------------
