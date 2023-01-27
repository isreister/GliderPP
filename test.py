#!/usr/bin/env python

import cdsapi

c = cdsapi.Client()

c.retrieve(
    'reanalysis-era5-single-levels',
    {'product_type': 'reanalysis', 'format': 'netcdf', 'variable': ['10m_u_component_of_wind', '10m_v_component_of_wind', '2m_dewpoint_temperature', '2m_temperature', 'mean_sea_level_pressure', 'total_cloud_cover', 'total_column_ozone', 'total_column_water_vapour'], 'year': '2018', 'month': ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12'], 'day': ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31'], 'time': ['12:00'], 'area': ['60.9681669898915/-3.018147955982417/50.96445495449682/6.982075406536717']},
    'download.nc')