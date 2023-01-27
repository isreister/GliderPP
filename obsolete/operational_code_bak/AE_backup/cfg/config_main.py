#
# Main config file for AlterEco primary productivity processor
#
# Includes all required files paths, parameters and authentications
#
# database_NRT:	near real-time database
# database_DT:	delayed-time processing database
# host: 	sftp service
# username:	username
# password:	password
# product_dir:	remote data directory on sftp service
# download_dir:	local base directory for storage (actual structure will mirror
#		product dir)
# fmatch:	comma separated file pattern to match
# staged_dir:	local directory in which to store preprocessed data.
#		Sub-directory structure will be retained
# table_name:	name of the main database table
# ???_column:	names of each database column
#		Date & message columns key from these so are not explicitly
#		defined.
#
#-------------------------------------------------------------------------------
# Initialising
database_DT=/Users/benloveday/Code/Git_Reps/AE_backup/AlterEco_SQL_chain_database_DT.db
database_NRT=/Users/benloveday/Code/Git_Reps/AE_backup/AlterEco_SQL_chain_database_NRT.db
# All: database params -- must match AlterEco_SQL_chain_database_initialise.py
table_name=AlterEco_glider_processing_stages
file_name_column=file_downloaded
glider_type_column=glider_type
glider_prefix_column=glider_prefix
glider_number_column=glider_number
glider_name_column=glider_name
stage_column=staged
stage_dir_column=staged_dir
EO_column=EO_acquire
preproc_column=preproc
spectral_column=spectral
corrected_column=corrections
pp_column=primary_prod
postproc_column=postproc
# Downloading
host=livftp.noc.ac.uk
username=AlterEco
password=Spr!ngM00n
product_dir=/Users/benloveday/Desktop/Glider_data
download_dir=/Users/benloveday/Desktop/Glider_data/BODC_data
fmatch=.
fexclude=nonetoexclude
# Staging:
staged_dir=/Users/benloveday/Desktop/Glider_data/BODC_staged_data
# EO acquire:
EO_dir=/Users/benloveday/Desktop/Glider_data/BODC_EO_data
DAP_dir=/Users/benloveday/Desktop/Glider_data/DAP
O3_mol=47.9982
avogadro=6.022140857e23
Dobson_conversion=2.687e20
date_pad=5
# Variables must match config_EO_trajectory
variables=CHL,PAR,KD490,ATMOS,SST,ALTIM
# Preprocessing:
preproc_dir=/Users/benloveday/Desktop/Glider_data/BODC_preprocessed_data
# Plotting
pad=3.0
fsz=12
#-------------------------------------------------------------------------------

