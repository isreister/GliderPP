#!/usr/bin/env python
'''
Purpose:	Defaults for glider trajectory extraction

Version: 	v1.0 02/2018

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
import sys

EO_username='bloveday'
EO_password='V$nu$tu23'

'''
CCI: local DT
{'source':'ESACCI_1KM',\
                       'local_path_root':'/data/datasets/CCI/v4.0-release/geographic/netcdf/daily/chlor_a/',\
                       'path_suffix':None,\
                       'url_root':None,\
                       'url_template':None,\
                       'lat_var':'lat',\
                       'lon_var':'lon',\
                       't_var':'time',\
                       't_ref':'1970-01-01 00:00:00',\
                       't_base':'days',\
                       'vars':['chlor_a'],\
                       'calc_vars':['CHL','ZEU'],\
                       'include' : True,\
                       'NRT_clim' : False,\
                       'clim_file' : '/data/datasets/Projects/AlterEco/Climatologies/ESA_OCCCI_CHL/ESACCI-OC-L3S-CHLOR_A-MERGED-CLIM_4km_CLIM.nc'},
'''
# Vstep is ignored for log values
TRA_CONFIG = {'CHL' : {'source':'CMEMS',\
                       'local_path_root':None,\
                       'product_id':'dataset-oc-glo-bio-multi-l3-chl_4km_daily-rt',\
                       'alt_product_id':'dataset-oc-glo-bio-multi-l3-chl_4km_daily-rep',\
                       'service_id':'OCEANCOLOUR_GLO_CHL_L3_NRT_OBSERVATIONS_009_032-TDS',\
                       'alt_service_id':'OCEANCOLOUR_GLO_CHL_L3_REP_OBSERVATIONS_009_085-TDS',\
                       'url_root':'http://nrt.cmems-du.eu/motu-web/Motu',\
                       'alt_url_root':'http://my.cmems-du.eu/motu-web/Motu',\
                       'url_template':None,\
                       'depth_range':[0.493,0.4942],\
                       'lat_var':'lat',\
                       'lon_var':'lon',\
                       't_var':'time',\
                       't_ref':'1900-01-01 00:00:00',\
                       't_base':'days',\
                       'EO_username':EO_username,\
                       'EO_password':EO_password,\
                       'vars':['CHL'],\
                       'calc_vars':['CHL','ZEU'],\
                       'include' : True,\
                       'NRT_clim' : False,\
                       'clim_file' : None},

              'ADG443' : {'source':'CMEMS',\
                       'local_path_root':None,\
                       'product_id':'dataset-oc-atl-opt-modis_a-l3-adg443_1km_daily-rt-v02',\
                       'service_id':'OCEANCOLOUR_ATL_OPTICS_L3_NRT_OBSERVATIONS_009_034-TDS',\
                       'url_root':'http://nrt.cmems-du.eu/motu-web/Motu',\
                       'url_template':None,\
                       'depth_range':[0.493,0.4942],\
                       'lat_var':'lat',\
                       'lon_var':'lon',\
                       't_var':'time',\
                       't_ref':'1900-01-01 00:00:00',\
                       't_base':'days',\
                       'EO_username':EO_username,\
                       'EO_password':EO_password,\
                       'vars':['ADG443'],\
                       'calc_vars':['ADG443'],\
                       'include' : False,\
                       'NRT_clim' : False,\
                       'clim_file' : None},

              'APH443' : {'source':'CMEMS',\
                       'local_path_root':None,\
                       'product_id':'dataset-oc-atl-opt-modis_a-l3-aph443_1km_daily-rt-v02',\
                       'service_id':'OCEANCOLOUR_ATL_OPTICS_L3_NRT_OBSERVATIONS_009_034-TDS',\
                       'url_root':'http://nrt.cmems-du.eu/motu-web/Motu',\
                       'url_template':None,\
                       'depth_range':[0.493,0.4942],\
                       'lat_var':'lat',\
                       'lon_var':'lon',\
                       't_var':'time',\
                       't_ref':'1900-01-01 00:00:00',\
                       't_base':'days',\
                       'EO_username':EO_username,\
                       'EO_password':EO_password,\
                       'vars':['APH443'],\
                       'calc_vars':['APH443'],\
                       'include' : False,\
                       'NRT_clim' : False,\
                       'clim_file' : None},

              'ATOT443' : {'source':'CMEMS',\
                       'local_path_root':None,\
                       'product_id':'dataset-oc-atl-opt-modis_a-l3-atot443_1km_daily-rt-v02',\
                       'service_id':'OCEANCOLOUR_ATL_OPTICS_L3_NRT_OBSERVATIONS_009_034-TDS',\
                       'url_root':'http://nrt.cmems-du.eu/motu-web/Motu',\
                       'url_template':None,\
                       'depth_range':[0.493,0.4942],\
                       'lat_var':'lat',\
                       'lon_var':'lon',\
                       't_var':'time',\
                       't_ref':'1900-01-01 00:00:00',\
                       't_base':'days',\
                       'EO_username':EO_username,\
                       'EO_password':EO_password,\
                       'vars':['ATOT443'],\
                       'calc_vars':['ATOT443'],\
                       'include' : False,\
                       'NRT_clim' : False,\
                       'clim_file' : None},
	
              'SST' : {'source':'CMEMS',\
                       'local_path_root':None,\
                       'product_id':'global-analysis-forecast-phy-001-024',\
                       'service_id':'GLOBAL_ANALYSIS_FORECAST_PHY_001_024-TDS',\
                       'url_root':'http://nrt.cmems-du.eu/motu-web/Motu',\
                       'url_template':None,\
                       'depth_range':[0.493,0.4942],\
                       'lat_var':'latitude',\
                       'lon_var':'longitude',\
                       't_var':'time',\
                       't_ref':'1950-01-01 00:00:00',\
                       't_base':'hours',\
                       'EO_username':EO_username,\
                       'EO_password':EO_password,\
                       'vars':['thetao','so','mlotst'],\
                       'calc_vars':['SST','SSS','MLD'],\
                       'include' : True,\
                       'NRT_clim' : False,\
                       'clim_file' : None},

              'PAR' : {'source':'MODIS',\
                       'local_path_root':None,\
                       'path_suffix':None,\
                       'url_root':'https://oceandata.sci.gsfc.nasa.gov/opendap/hyrax/MODISA/L3SMI/',\
                       'url_template':'$Y/$j/A$Y$j.L3m_DAY_PAR_par_4km.nc.nc',\
                       'lat_var':'lat',\
                       'lon_var':'lon',\
                       't_var':'time',\
                       't_ref':'2000-01-01 00:00:00',\
                       't_base':'seconds',\
                       'vars':['par'],\
                       'calc_vars':['PAR'],\
                       'include' : True,\
                       'NRT_clim' : False,\
                       'clim_file' : None},

              'KD490': {'source':'MODIS',\
                       'local_path_root':None,\
                       'path_suffix':None,\
                       'url_root':'https://oceandata.sci.gsfc.nasa.gov/opendap/hyrax/MODISA/L3SMI/',\
                       'url_template':'$Y/$j/A$Y$j.L3m_DAY_KD490_Kd_490_4km.nc.nc',\
                       'lat_var':'lat',\
                       'lon_var':'lon',\
                       't_var':'time',\
                       't_ref':'2000-01-01 00:00:00',\
                       't_base':'seconds',\
                       'vars':['Kd_490'],\
                       'calc_vars':['KD490'],\
                       'include' : True,\
                       'NRT_clim' : False,\
                       'clim_file' : None},

             'ATMOS': {'source':'ECMWF',\
                       'local_path_root':None,\
                       'path_suffix':None,\
                       'url_root':None,\
                       'url_template':None,\
                       'lat_var':'latitude',\
                       'lon_var':'longitude',\
                       't_var':'time',\
                       't_ref':'1900-01-01 00:00:00',\
                       't_base':'hours',\
                       'vars':['u10','v10','tcc','msl','tco3','tcwv','t2m','d2m'],\
                       'calc_vars':['WSPD','CLOUD','MSLP','O3','TCWV','RH'],\
                       'include' : True,\
                       'NRT_clim' : True,\
                       'clim_file' : '/home/ben/shared/Linux_desktop/data/datasets/Projects/AlterEco/Climatologies/ECMWF_ERA_I/ERAI_monthly_climatology.nc'},

             'ALTIM': {'source':'CMEMS',\
                       'local_path_root':None,\
                       'product_id': 'dataset-duacs-nrt-global-merged-allsat-phy-l4',\
                       'alt_product_id': 'dataset-duacs-rep-global-merged-allsat-phy-l4',\
                       'service_id':'SEALEVEL_GLO_PHY_L4_NRT_OBSERVATIONS_008_046-TDS',\
                       'alt_service_id':'SEALEVEL_GLO_PHY_L4_REP_OBSERVATIONS_008_047-TDS',\
                       'url_root':'http://nrt.cmems-du.eu/motu-web/Motu',\
                       'alt_url_root':'http://my.cmems-du.eu/motu-web/Motu',\
                       'url_template':None,\
                       'depth_range':[0.493,0.4942],\
                       'lat_var':'latitude',\
                       'lon_var':'longitude',\
                       't_var':'time',\
                       't_ref':'1950-01-01 00:00:00',\
                       't_base':'days',\
                       'EO_username':EO_username,\
                       'EO_password':EO_password,\
                       'vars':['sla','adt','ugos','vgos','ugosa','vgosa'],\
                       'calc_vars':['UGOS','VGOS','UGOSA','VGOSA','SLA','ADT','EKE','MKE','TKE'],\
                       'include' : True,\
                       'NRT_clim' : False,\
                       'clim_file' : None},
             }
#EOF
