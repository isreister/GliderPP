Stages (cron):

Transfer between stages managed by SQL database keys for NRT and DT chains.
Most user parameters passed to the chain via the config_main.py file

1) AlterEco_SQL_chain_database_initialise.py	Controls initialisation and backup of databases. (done)

2) AlterEco_autodownload.py 			Automatically downloads SFTP staged glider data. Populates data with downloaded and pre-esxisting data. Arguments passed via config file. (done)

3) AlterEco_staging.py   			Looks for new data, splits profiles and interpolates/bins if requested. (done - No longer concatenates, can work with original format)

4) AlterEco_acquire_EO.py 			Concatenates glider data into trajectory file
						Looks for ancillary EO data to support gliders (done)
						NRT case: ERAI and CCI monthly climatology, up-to-date daily NRT SST, iPAR and AVISO
						DT case: ERAI and CCI DT daily product, up-to-date daily NRT SST, iPAR and AVISO

===================== Non operational =============================

5) AlterEco_preprocessing.py			Reads in glider files
						Converts eng units to PAR, Chlorophyll and back-scattering.
						Selects variables for use.
						Determines quenching method
						NRT mode: fluorescence quenching methods: Biermann, Swart, Xi.
						DT mode: fluorescence quenching methods: Hemsley, Biermann, Swart, Xi.

6) AlterEco_spectral.py				Calculate CHL and Ed scaling prior to running PP model (Hemsley mode: DT)

7) AlterEco_corrections.py			Applies Chl and Ed scaling factors to pp input files

8) AlterEco_primary_prod.py			Makes Morel91 primary productivity calculations for all models

9) AlterEco_postprocessing.py			Manages interfaces for data output

10) AlterEco_visualisation.py			Connects to pyplot routines for NRT/DT plotting


TO DO:

Fix humpback profile splitting
Process Melonhead
