#!/bin/bash

preproc_dir='/data/datasets/Projects/AlterEco/Glider_data/BODC_preprocessed_data/'
pp_dir='/data/datasets/Projects/AlterEco/Glider_data/BODC_pp_data/'

for glider in 'Cook_441' 'Cabot_454' 'Dolomite_477' \
              'Eltanin_478' 'Kelvin_481' 'Stella_494' \
              'Dolomite_499' 'Coprolite_500' 'Cabot_517' \
              '_579_'; do
  echo '============================================================================'
  for method in 'biermann' 'biermann_eo' 'hemsley' 'hemsley_eo' 'xing' 'xing_eo'; do
    echo '-------'
    files=`find $preproc_dir -name "*$glider*$method.nc"`
    for file in $files; do
      latest_preproc=$file
    done
    echo $latest_preproc

    latest_pp='None'
    echo $pp_dir*$glider*chl*$method.txt
    files=`find $pp_dir -name "*$glider*chl*$method.txt"`
    for file in $files; do
      latest_pp=$file
    done
    echo $latest_pp
  done
done
echo '============================================================================'
