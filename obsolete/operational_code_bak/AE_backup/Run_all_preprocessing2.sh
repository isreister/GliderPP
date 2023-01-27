#!/bin/bash

# gliders: 441,454,477,478,481,494,499,500,517,579

#for glider in 'EGO_441_Cook' 'EGO_454_Cabot' 'EGO_477_Dolomite' \
#              'EGO_478_Eltanin' 'EGO_481_Kelvin' 'EGO_494_Stella' \
#              'EGO_499_Dolomite' 'EGO_500_Coprolite' 'EGO_517_Cabot' \
#              'UEA_579_humpback'; do

for glider in 'EGO_454_Cabot'; do
  echo '>>>>>>>>>' $glider
  for method in 'Swart'; do

    # select glider
    opts='-ag '$glider
    opts1=$opts' -gcfg cfg/config_EGO_Swart.py'

    log_file1='logs/'$glider'_'$method'.out'

    # run
    echo "Running (EO) ./AlterEco_preprocessing.py $opts1"
    ./AlterEco_preprocessing.py $opts1

  done
done
