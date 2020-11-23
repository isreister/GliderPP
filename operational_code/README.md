**ALTERECO OPERATIONAL CODE**
---
|Description    | Main scripts for processing AlterEco data |
| :-------------| :----------------------------------------------------------- |
|Author         | Ben Loveday (blo@pml.ac.uk; ben.loveday@gmail.com) |
|Date           | 02/2020 |
|Version        | v1.0 |
|Project use    | **ALTERECO** |

*Notes*

Processing should be run in the following order presented below and/or using the Process_PP_gliders.run
main script. Parameters for differing glider types are provided by the config files in the /cfg drectory. 

---
**MODULES:**
---
| Module                                       | Job                                       |
| :-------------                               | :----------------------------------------------------------- |
| AlterEco_SQL_chain_database_initialise.py    | Controls initialisation and backup of databases |
| AlterEco_autodownload.py                     | Automatically downloads SFTP staged glider data. Populates data with downloaded and pre-esxisting data. Arguments passed via config file. |
| AlterEco_staging.py                          | Stages AlterEco data.  |
| AlterEco_acquire_EO.py                       | Manages interpolation of external data on the glider track. | 
| AlterEco_preprocessing.py                    | Preprocesses glider data ready for external PP calculations |
| Process_PP_gliders.run                       | Main Bash script that coordinates all of the above and runs all subsequent processing scripts |
| Tools                                        | Folder containing all relevant sub-routines |

---
MODULE NOTES:
---

*AlterEco_SQL_chain_database_initialise.py*

Uses the information in cfg/config_main.py t o construct a DT or NRT database. 
NT or DT are selected using the -pc argument (e.g. -pc NRT). Table and column
names can be adapted by the user.


*AlterEco_autodownload.py*

Autodownloads all data from the BODC FTP site hosted by NOC Liverpool. The contact 
for this is Emma Slater at BODC (emmer@BODC.AC.UK). Current FTP log in details are
as follows: HOST: sftp://livftp.noc.ac.uk, USERNAME: AlterEco, PWORD: Spr!ngM00n.

All configurable parameters are set in cfg/config_main.py, including data storage
locations, server credentials and filters for including/excluding files.

This routine will also scrape local directories to add anything that may have been
missed, in case you decide to re-build the database.

*AlterEco_staging.py*

'Stages' the AlterEco EGO (and UEA) formatted data. We need to calculate PP on a profile by profile
basis, so this splits any EGO format data into consituent profiles (either a single dive down, or dive up).
If possible missing data is interpolated across small data gaps.

Staged data will be put in: ../../BODC_staged_data/

*AlterEco_acquire_EO.py*

Sources and interpolates external EO data sources onto the consolidated glider track.
Begins by concatenating glider data into a single trajectory file, which is then used
to set the bounds of data gathering. It then looks for ancillary EO data to support 
gliders. In the NRT case this is ERAI and CCI monthly climatologies, up-to-date daily 
NRT SST, PAR and AVISO altimetry vars. In the DT case, this is ERAI and CCI DT daily product, 
up-to-date daily NRT SST, MODIS PAR and AVISO altimetry vars. All required variables are
determind by cfg/config_EO_trajectory.py

*AlterEco_preprocessing.py*

Performs final preprocessing of the relevant glider data. It converts glider units to
actual quantities (e.g. PAR/CHL/BBP) if required, selects variables to use, applies 
the relevant quenching method (Xing et al for AlterEco) and outputs the necessary variables
as txt files for ingestion into external tools. The preprocessing stage is extensive and exploits
a number of differing configuration files, which depend on the glider being used. All relevant 
config files are in cfg/config_EGO... etc.

It will create the following output files:\
1. ../../BODC__preprocessed_data/ : 1 netCDF files per profile, contains all corrected data (.nc).
2. ../../BODC_pp_data/ : 1 telemetry file, 1 chl file and 1 par file per profile (.txt).

The Run_all_preprocessing.sh batch file can be used to do this en masse, and provides information
on how to run the preprocessing script.

*Process_PP_gliders.run*

Main script. This can be used to run all of the above processes and can be launched in batch mode
for all gliders using Run_all_processing.sh (check stage start name to determine which processes
to run). After the pre-processing stage, this will perform the following tasks:
1. calculate the relevant spectral PAR using Gregg and Carder; produces the 'ed' and 'zen' files.
2. calculate the relevant scaling factors for PAR/E0+ (all methods) and CHL (Hemsley only) using the
  project_spectral_PAR.py routine. This creates a scale file for each profile.
3. subsets the ed file for the relevant time for each profile and applies the scale factors for ed and
  chl if required (apply_Chl_Ed_corrections.py). Scaled profiles have a .corr extension. Uncorrected 
  values are retained in the .txt file. (by this point there will be and ed???.txt file and ed???.txt' 
  subset file and an eds???.corr  file.
4. Lastly, it will run the morel91 PP model for three cases:\
  -  with uncorrected eds/chl > pp????.txt
  -  with corrected eds and chl > pp????.corr
  -  with corrected eds and uncorrected chl >> pp????.split

Note that here, corrected chl refers ONLY to scaled CHL a la Hemsley. Quenching is ALWAYS applied.

All other routines are used to configure specific parts of specific gliders.

---
OUTSTANDING:
---
> Fix humpback profile splitting
> Process Melonhead
