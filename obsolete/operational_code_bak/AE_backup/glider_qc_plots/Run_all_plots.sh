#!/bin/bash

nohup ./Check_CHL.py -m '_xing' > CHL_plot_xing.out &
nohup ./Check_CHL.py -m '_xing_eo' > CHL_plot_xing_eo.out &
nohup ./Check_CHL.py -m '_biermann' > CHL_plot_biermann.out &
nohup ./Check_CHL.py -m '_biermann_eo' > CHL_plot_biermann_eo.out &
nohup ./Check_CHL.py -m '_hemsley' > CHL_plot_hemsley.out &
nohup ./Check_CHL.py -m '_hemsley_eo' > CHL_plot_hemsley_eo.out &

exit






nohup ./Check_PP.py > PP_plot.out & 
nohup ./Check_PP.py -r '.corr' > PP_plot_corr.out &
nohup ./Check_PP.py -r '.split' > PP_plot_split.out &

# - 

nohup ./Check_PP.py -m '_xing' > PP_plot_xing.out &
nohup ./Check_PP.py -r '.corr' -m '_xing' > PP_plot_xing_corr.out &
nohup ./Check_PP.py -r '.split' -m '_xing' > PP_plot_xing_split.out &

nohup ./Check_PP.py -m '_biermann' > PP_plot_biermann.out &
nohup ./Check_PP.py -r '.corr' -m '_biermann' > PP_plot_biermann_corr.out &
nohup ./Check_PP.py -r '.split' -m '_biermann' > PP_plot_biermann_split.out &

nohup ./Check_PP.py -m '_hemsley_eo' > PP_plot_hemsley_eo.out &
nohup ./Check_PP.py -r '.corr' -m '_hemsley_eo' > PP_plot_hemsley_eo_corr.out &
nohup ./Check_PP.py -r '.split' -m '_hemsley_eo' > PP_plot_hemsley_eo_split.out &
