#!/usr/bin/env python

import os
import datetime

def metadata_specs():

    root_dir = '/home/ben/shared/Linux_desktop/data/datasets/Projects/AlterEco/'

    pp_dir00 = os.path.join(root_dir,'Glider_data/BODC_pp_data/EGO/Cook_20171115/EGO_441_Cook')           # 1
    pp_dir01 = os.path.join(root_dir,'Glider_update_run/BODC_pp_data/EGO/EGO_496_Melonhead')              # 2
    pp_dir02 = os.path.join(root_dir,'Glider_data/BODC_pp_data/EGO/Stella_20180207/EGO_494_Stella')       # 3
    pp_dir03 = os.path.join(root_dir,'Glider_update_run/BODC_pp_data/EGO/EGO_493_Orca')                   # 4
    pp_dir04 = os.path.join(root_dir,'Glider_update_run/BODC_pp_data/EGO/EGO_455_Orca')                   # 5
    pp_dir05 = os.path.join(root_dir,'Glider_update_run/BODC_pp_data/humpback_UEA/UEA_579_humpback')      # 6
    pp_dir06 = os.path.join(root_dir,'Glider_data/BODC_pp_data/EGO/EGO_454_Cabot')                        # 7
    pp_dir07 = os.path.join(root_dir,'Glider_data/BODC_pp_data/EGO/EGO_477_Dolomite')                     # 8
    pp_dir08 = os.path.join(root_dir,'Glider_update_run/BODC_pp_data/EGO/EGO_478_Eltanin')                # 9
    pp_dir09 = os.path.join(root_dir,'Glider_data/BODC_pp_data/EGO/EGO_481_Kelvin')                      # 10
    pp_dir10 = os.path.join(root_dir,'Glider_data/BODC_pp_data/EGO/Coprolite_20181202/EGO_500_Coprolite')# 11
    pp_dir11 = os.path.join(root_dir,'Glider_data/BODC_pp_data/EGO/Dolomite_20181202/EGO_499_Dolomite')  # 12
    pp_dir12 = os.path.join(root_dir,'Glider_data/BODC_pp_data/EGO/Cabot_20190312/EGO_517_Cabot')        # 13

    pp_dirs = [pp_dir00,\
               pp_dir01,\
               pp_dir02,\
               pp_dir03,\
               pp_dir04,\
               pp_dir05,\
               pp_dir06,\
               pp_dir07,\
               pp_dir08,\
               pp_dir09,\
               pp_dir10,\
               pp_dir11,\
               pp_dir12]

    orig_files = ['Cook_441_R.nc',\
                  'Melonhead_496_R.nc',\
                  'Stella_494_R.nc',\
                  'Orca_493_R.nc',\
                  'Orca_455_R.nc',\
                  'AE3_sg579_timeseries_flag_UEA.nc',\
                  'GL_20180508_Cabot_454_R.nc',\
                  'GL_20180812_Dolomite_477_R.nc',\
                  'Eltanin_478_R.nc',\
                  'GL_20180928_Kelvin_481_R.nc',\
                  'Coprolite_500_R.nc',\
                  'Dolomite_499_R.nc',\
                  'Cabot_517_R.nc']

    final_files = ['Cook_441_PP_R.nc',\
                   'Melonhead_496_PP_R.nc',\
                   'Stella_494_PP_R.nc',\
                   'Orca_493_PP_R.nc',\
                   'Orca_455_PP_R.nc',\
                   'Humpback_497_PP_R.nc',\
                   'Cabot_454_PP_R.nc',\
                   'Dolomite_477_PP_R.nc',\
                   'Eltanin_478_PP_R.nc',\
                   'Kelvin_481_PP_R.nc',\
                   'Coprolite_500_PP_R.nc',\
                   'Dolomite_499_PP_R.nc',\
                   'Cabot_517_PP_R.nc']

    cook_441_dict = {'data_type':'EGO glider time-series data',\
		 'format_version':'1.2',\
		 'platform_code':'Cook',\
                 'deployment_code':'441',\
                 'project_name':'AlterEco',\
                 'project_description':'Data collected as part of the NERC UKRI AlterEco project (https://projects.noc.ac.uk/altereco/)',\
                 'campaign':'1',\
		 'date_update':str(datetime.datetime.today()),\
		 'data_mode':'R',\
		 'naming_authority':'EGO',\
		 'id':[],\
                 'processing':'Data set processed by Ben Loveday (Plymouth Marine Laboratory/Innoflair) and Tim Smyth (Plymouth Marine Laboratory)',\
                 'ancillary_mission_overview':'https://www.bodc.ac.uk/data/bodc_database/gliders/',\
                 'ancillary_mission_specifics':'https://api.linked-systems.uk/api/meta/v2/deployments/info/441',\
                 'ancillary_base_data':'https://linkedsystems.uk/erddap/files/Public_Glider_Data_0711/Cook_20171115/Cook_441_R.nc'}

    melonhead_496_dict = {'data_type':'EGO glider time-series data',\
		 'format_version':'1.2',\
		 'platform_code':'Melonhead',\
                 'deployment_code':'496',\
                 'project_name':'AlterEco',\
                 'project_description':'Data collected as part of the NERC UKRI AlterEco project (https://projects.noc.ac.uk/altereco/)',\
                 'campaign':'2',\
		 'date_update':str(datetime.datetime.today()),\
		 'data_mode':'R',\
		 'naming_authority':'EGO',\
		 'id':[],\
                 'processing':'Data set processed by Ben Loveday (Plymouth Marine Laboratory/Innoflair) and Tim Smyth (Plymouth Marine Laboratory)',\
                 'ancillary_mission_overview':'https://www.bodc.ac.uk/data/bodc_database/gliders/',\
                 'ancillary_mission_specifics':'https://api.linked-systems.uk/api/meta/v2/deployments/info/496',\
                 'ancillary_base_data':'https://linkedsystems.uk/erddap/files/Public_Glider_Data_0711/Melonhead_20180207/Melonhead_496_R.nc'}
    
    stella_494_dict = {'data_type':'EGO glider time-series data',\
		 'format_version':'1.2',\
		 'platform_code':'Stella',\
                 'deployment_code':'494',\
                 'project_name':'AlterEco',\
                 'project_description':'Data collected as part of the NERC UKRI AlterEco project (https://projects.noc.ac.uk/altereco/)',\
                 'campaign':'2',\
		 'date_update':str(datetime.datetime.today()),\
		 'data_mode':'R',\
		 'naming_authority':'EGO',\
		 'id':[],\
                 'processing':'Data set processed by Ben Loveday (Plymouth Marine Laboratory/Innoflair) and Tim Smyth (Plymouth Marine Laboratory)',\
                 'ancillary_mission_overview':'https://www.bodc.ac.uk/data/bodc_database/gliders/',\
                 'ancillary_mission_specifics':'https://api.linked-systems.uk/api/meta/v2/deployments/info/494',\
                 'ancillary_base_data':'https://linkedsystems.uk/erddap/files/Public_Glider_Data_0711/Stella_20180207/Stella_494_R.nc'}

    orca_493_dict = {'data_type':'EGO glider time-series data',\
		 'format_version':'1.2',\
		 'platform_code':'Orca',\
                 'deployment_code':'493',\
                 'project_name':'AlterEco',\
                 'project_description':'Data collected as part of the NERC UKRI AlterEco project (https://projects.noc.ac.uk/altereco/)',\
                 'campaign':'2',\
		 'date_update':str(datetime.datetime.today()),\
		 'data_mode':'R',\
		 'naming_authority':'EGO',\
		 'id':[],\
                 'processing':'Data set processed by Ben Loveday (Plymouth Marine Laboratory/Innoflair) and Tim Smyth (Plymouth Marine Laboratory)',\
                 'ancillary_mission_overview':'https://www.bodc.ac.uk/data/bodc_database/gliders/',\
                 'ancillary_mission_specifics':'https://api.linked-systems.uk/api/meta/v2/deployments/info/493',\
                 'ancillary_base_data':'https://linkedsystems.uk/erddap/files/Public_Glider_Data_0711/Orca_20180307/Orca_493_R.nc'}

    orca_455_dict = {'data_type':'EGO glider time-series data',\
		 'format_version':'1.2',\
		 'platform_code':'Orca',\
                 'deployment_code':'455',\
                 'project_name':'AlterEco',\
                 'project_description':'Data collected as part of the NERC UKRI AlterEco project (https://projects.noc.ac.uk/altereco/)',\
                 'campaign':'3',\
		 'date_update':str(datetime.datetime.today()),\
		 'data_mode':'R',\
		 'naming_authority':'EGO',\
		 'id':[],\
                 'processing':'Data set processed by Ben Loveday (Plymouth Marine Laboratory/Innoflair) and Tim Smyth (Plymouth Marine Laboratory)',\
                 'ancillary_mission_overview':'https://www.bodc.ac.uk/data/bodc_database/gliders/',\
                 'ancillary_mission_specifics':'https://api.linked-systems.uk/api/meta/v2/deployments/info/455',\
                 'ancillary_base_data':'https://linkedsystems.uk/erddap/files/Public_Glider_Data_0711/Orca_20180508/Orca_455_R.nc'}

    humpback_497_dict = {'data_type':'EGO glider time-series data',\
		 'format_version':'1.2',\
		 'platform_code':'Humpback',\
                 'deployment_code':'497',\
                 'project_name':'AlterEco',\
                 'project_description':'Data collected as part of the NERC UKRI AlterEco project (https://projects.noc.ac.uk/altereco/)',\
                 'campaign':'3',\
		 'date_update':str(datetime.datetime.today()),\
		 'data_mode':'R',\
		 'naming_authority':'EGO',\
		 'id':[],\
                 'processing':'Data set processed by Ben Loveday (Plymouth Marine Laboratory/Innoflair) and Tim Smyth (Plymouth Marine Laboratory)',\
                 'ancillary_mission_overview':'https://www.bodc.ac.uk/data/bodc_database/gliders/',\
                 'ancillary_mission_specifics':'https://api.linked-systems.uk/api/meta/v2/deployments/info/497',\
                 'ancillary_base_data':'https://linkedsystems.uk/erddap/files/Public_Glider_Data_0711/Humpback_20180509/Humpback_497_R.nc'}

    cabot_454_dict = {'data_type':'EGO glider time-series data',\
		 'format_version':'1.2',\
		 'platform_code':'Cabot',\
                 'deployment_code':'454',\
                 'project_name':'AlterEco',\
                 'project_description':'Data collected as part of the NERC UKRI AlterEco project (https://projects.noc.ac.uk/altereco/)',\
                 'campaign':'3',\
		 'date_update':str(datetime.datetime.today()),\
		 'data_mode':'R',\
		 'naming_authority':'EGO',\
		 'id':[],\
                 'processing':'Data set processed by Ben Loveday (Plymouth Marine Laboratory/Innoflair) and Tim Smyth (Plymouth Marine Laboratory)',\
                 'ancillary_mission_overview':'https://www.bodc.ac.uk/data/bodc_database/gliders/',\
                 'ancillary_mission_specifics':'https://api.linked-systems.uk/api/meta/v2/deployments/info/454',\
                 'ancillary_base_data':'https://linkedsystems.uk/erddap/files/Public_Glider_Data_0711/Cabot_20180508/Cabot_454_R.nc'}

    dolomite_477_dict = {'data_type':'EGO glider time-series data',\
		 'format_version':'1.2',\
		 'platform_code':'Dolomite',\
                 'deployment_code':'477',\
                 'project_name':'AlterEco',\
                 'project_description':'Data collected as part of the NERC UKRI AlterEco project (https://projects.noc.ac.uk/altereco/)',\
                 'campaign':'4',\
		 'date_update':str(datetime.datetime.today()),\
		 'data_mode':'R',\
		 'naming_authority':'EGO',\
		 'id':[],\
                 'processing':'Data set processed by Ben Loveday (Plymouth Marine Laboratory/Innoflair) and Tim Smyth (Plymouth Marine Laboratory)',\
                 'ancillary_mission_overview':'https://www.bodc.ac.uk/data/bodc_database/gliders/',\
                 'ancillary_mission_specifics':'https://api.linked-systems.uk/api/meta/v2/deployments/info/477',\
                 'ancillary_base_data':'https://linkedsystems.uk/erddap/files/Public_Glider_Data_0711/Cabot_20180508/Cabot_454_R.nc'}

    eltanin_478_dict = {'data_type':'EGO glider time-series data',\
		 'format_version':'1.2',\
		 'platform_code':'Eltanin',\
                 'deployment_code':'478',\
                 'project_name':'AlterEco',\
                 'project_description':'Data collected as part of the NERC UKRI AlterEco project (https://projects.noc.ac.uk/altereco/)',\
                 'campaign':'4',\
		 'date_update':str(datetime.datetime.today()),\
		 'data_mode':'R',\
		 'naming_authority':'EGO',\
		 'id':[],\
                 'processing':'Data set processed by Ben Loveday (Plymouth Marine Laboratory/Innoflair) and Tim Smyth (Plymouth Marine Laboratory)',\
                 'ancillary_mission_overview':'https://www.bodc.ac.uk/data/bodc_database/gliders/',\
                 'ancillary_mission_specifics':'https://api.linked-systems.uk/api/meta/v2/deployments/info/478',\
                 'ancillary_base_data':'https://linkedsystems.uk/erddap/files/Public_Glider_Data_0711/Cabot_20180508/Cabot_454_R.nc'}

    kelvin_481_dict = {'data_type':'EGO glider time-series data',\
		 'format_version':'1.2',\
		 'platform_code':'Kelvin',\
                 'deployment_code':'481',\
                 'project_name':'AlterEco',\
                 'project_description':'Data collected as part of the NERC UKRI AlterEco project (https://projects.noc.ac.uk/altereco/)',\
                 'campaign':'5',\
		 'date_update':str(datetime.datetime.today()),\
		 'data_mode':'R',\
		 'naming_authority':'EGO',\
		 'id':[],\
                 'processing':'Data set processed by Ben Loveday (Plymouth Marine Laboratory/Innoflair) and Tim Smyth (Plymouth Marine Laboratory)',\
                 'ancillary_mission_overview':'https://www.bodc.ac.uk/data/bodc_database/gliders/',\
                 'ancillary_mission_specifics':'https://api.linked-systems.uk/api/meta/v2/deployments/info/481',\
                 'ancillary_base_data':'https://linkedsystems.uk/erddap/files/Public_Glider_Data_0711/Cabot_20180508/Cabot_454_R.nc'}

    coprolite_500_dict = {'data_type':'EGO glider time-series data',\
		 'format_version':'1.2',\
		 'platform_code':'Coprolite',\
                 'deployment_code':'500',\
                 'project_name':'AlterEco',\
                 'project_description':'Data collected as part of the NERC UKRI AlterEco project (https://projects.noc.ac.uk/altereco/)',\
                 'campaign':'6',\
		 'date_update':str(datetime.datetime.today()),\
		 'data_mode':'R',\
		 'naming_authority':'EGO',\
		 'id':[],\
                 'processing':'Data set processed by Ben Loveday (Plymouth Marine Laboratory/Innoflair) and Tim Smyth (Plymouth Marine Laboratory)',\
                 'ancillary_mission_overview':'https://www.bodc.ac.uk/data/bodc_database/gliders/',\
                 'ancillary_mission_specifics':'https://api.linked-systems.uk/api/meta/v2/deployments/info/500',\
                 'ancillary_base_data':'https://linkedsystems.uk/erddap/files/Public_Glider_Data_0711/Cabot_20180508/Cabot_454_R.nc'}

    dolomite_499_dict = {'data_type':'EGO glider time-series data',\
		 'format_version':'1.2',\
		 'platform_code':'Dolomite',\
                 'deployment_code':'499',\
                 'project_name':'AlterEco',\
                 'project_description':'Data collected as part of the NERC UKRI AlterEco project (https://projects.noc.ac.uk/altereco/)',\
                 'campaign':'6',\
		 'date_update':str(datetime.datetime.today()),\
		 'data_mode':'R',\
		 'naming_authority':'EGO',\
		 'id':[],\
                 'processing':'Data set processed by Ben Loveday (Plymouth Marine Laboratory/Innoflair) and Tim Smyth (Plymouth Marine Laboratory)',\
                 'ancillary_mission_overview':'https://www.bodc.ac.uk/data/bodc_database/gliders/',\
                 'ancillary_mission_specifics':'https://api.linked-systems.uk/api/meta/v2/deployments/info/499',\
                 'ancillary_base_data':'https://linkedsystems.uk/erddap/files/Public_Glider_Data_0711/Cabot_20180508/Cabot_454_R.nc'}

    cabot_517_dict = {'data_type':'EGO glider time-series data',\
		 'format_version':'1.2',\
		 'platform_code':'Cabot',\
                 'deployment_code':'517',\
                 'project_name':'AlterEco',\
                 'project_description':'Data collected as part of the NERC UKRI AlterEco project (https://projects.noc.ac.uk/altereco/)',\
                 'campaign':'7',\
		 'date_update':str(datetime.datetime.today()),\
		 'data_mode':'R',\
		 'naming_authority':'EGO',\
		 'id':[],\
                 'processing':'Data set processed by Ben Loveday (Plymouth Marine Laboratory/Innoflair) and Tim Smyth (Plymouth Marine Laboratory)',\
                 'ancillary_mission_overview':'https://www.bodc.ac.uk/data/bodc_database/gliders/',\
                 'ancillary_mission_specifics':'https://api.linked-systems.uk/api/meta/v2/deployments/info/517',\
                 'ancillary_base_data':'https://linkedsystems.uk/erddap/files/Public_Glider_Data_0711/Cabot_20180508/Cabot_454_R.nc'}

    metadata_descs = [cook_441_dict,\
                      melonhead_496_dict,\
                      stella_494_dict,\
                      orca_493_dict,\
                      orca_455_dict,\
                      humpback_497_dict,\
                      cabot_454_dict,\
                      dolomite_477_dict,\
                      eltanin_478_dict,\
                      kelvin_481_dict,\
                      coprolite_500_dict,\
                      dolomite_499_dict,\
                      cabot_517_dict]

    return pp_dirs, orig_files, final_files, metadata_descs

