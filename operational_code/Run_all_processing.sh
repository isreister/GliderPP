#!/bin/bash

# gliders: 441,454,477,478,481,494,499,500,517,579,455,493,496

#455, 493, 496, 579

#for glider in '455' '493' '496' '579'; do
for glider in '478' '496'; do

  for method in '_xing'; do

    # select glider
    opts1=$glider' '$method'_eo.txt N 4'
    opts2=$glider' '$method'.txt N 4'

    # set log file
    log_file1='logs/'$glider'_'$method'_EO_pp.out'
    log_file2='logs/'$glider'_'$method'_pp.out'

    # run
    echo "Running: Process_PP_gliders.run $opts1 > $log_file1"
    nohup ./Process_PP_gliders.run $opts1 > $log_file1 2>&1 &    
    sleep 60

    if  [[ $glider == "454" ]] || [[ $glider == "517" ]] || [[ $glider == "579" ]] || [[ $glider == "496" ]]; then
      echo "Running: Process_PP_gliders.run $opts2 > $log_file2"
      nohup ./Process_PP_gliders.run $opts2 > $log_file2 2>&1 &
      sleep 60
    fi

  done
done
