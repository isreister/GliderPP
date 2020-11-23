#!/bin/bash

# gliders: 441,454,477,478,481,494,499,500,517,579

#for glider in 'EGO_441_Cook' 'EGO_454_Cabot' 'EGO_477_Dolomite' \
#              'EGO_478_Eltanin' 'EGO_481_Kelvin' 'EGO_494_Stella' \
#              'EGO_499_Dolomite' 'EGO_500_Coprolite' 'EGO_517_Cabot' \
#              'UEA_579_humpback'; do

for glider in 'EGO_478_Eltanin' 'EGO_496_Melonhead'; do
  echo '>>>>>>>>>' $glider
  for method in 'Xing'; do

    # select glider
    opts='-ag '$glider

    # select method
    if [[ $glider == *"humpback" ]]; then
      opts1=$opts' -gcfg cfg/config_UEA_'$method'_EO.py'
      opts2=$opts' -gcfg cfg/config_UEA_'$method'.py'
    elif [[ $glider == *"Melonhead" ]]; then
      opts1=$opts' -gcfg cfg/config_MELONHEAD_'$method'_EO.py' 
      opts2=$opts' -gcfg cfg/config_MELONHEAD_'$method'.py'
    else
      opts1=$opts' -gcfg cfg/config_ELTANIN_'$method'_EO.py' 
      opts2=$opts' -gcfg cfg/config_ELTANIN_'$method'.py'
    fi

    # set log file
    log_file1='logs/'$glider'_'$method'_EO.out'
    log_file2='logs/'$glider'_'$method'.out'

    # run
    echo "Running (EO) ./AlterEco_preprocessing.py $opts1 > $log_file1"
    nohup ./AlterEco_preprocessing.py $opts1 > $log_file1 &
    sleep 60

    # Launch EO sensitivity runs
    echo "Running (in situ) ./AlterEco_preprocessing.py $opts2 > $log_file2"
    nohup ./AlterEco_preprocessing.py $opts2 > $log_file2 &
    sleep 60
    
    if  [[ $glider == *"_Cabot" ]]; then
      echo "Running (in situ) ./AlterEco_preprocessing.py $opts2 > $log_file2"
      #nohup ./AlterEco_preprocessing.py $opts2 > $log_file2 &
    fi

  done
done
