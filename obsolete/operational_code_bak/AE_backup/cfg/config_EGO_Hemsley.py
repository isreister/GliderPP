#
# INPUT Config File for EGO variables
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
depth_var=PRES
depth_pol=positive
depth_min=0
depth_max=1000
depth_bin=5
record_var=TIME
lon_var=LONGITUDE
lat_var=LATITUDE
t_var=TIME
profile_var=PROFILE_NUMBER
profile_var_read=profile_num
t_ref=1970-01-01 00:00:00
t_base=seconds
nc_tag=_hemsley.nc
lon_var_backup=LONGITUDE_GPS
lat_var_backup=LATITUDE_GPS
# values tested on Dolomite; very messy
sgolay_win=151
sgolay_smooth=5
allowed_vars=CHLA,CDOM,BBP700,MOLAR_DOXY,DOWNWELLING_PAR,TEMP,CNDC,PRES,TIME,LATITUDE,LONGITUDE,PROFILE_NUMBER
allowed_heads=CHLA,CDOM,SCATTER,DOXY,PAR,TEMP,CNDC,PRES,TIME,LATITUDE,LONGITUDE,PROFILE_NUMBER
allowed_exact=1,1,1,1,1,1,1,1,1,1,1,1
#quench_methods=Xing,Biermann,Hemsley,Swart
quench_methods=Hemsley
correction_file_suffix=_hemsley.txt
#accommodate units of mol/m2/s - assumed
PAR_conversion=1000000
#-------------------------
# sensitivity test choices
#-------------------------
force_use_quench_method=1
force_use_EO_par=0
#-------------------------------------------------------------------------------

