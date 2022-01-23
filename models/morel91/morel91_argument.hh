/* morel91_argument.h
 * 
 * Interprets arguments from the command line.
 *
 * Latest modification: 04/08/17 11:18:33
 */

#ifndef _MOREL91_ARGUMENT
#define _MOREL91_ARGUMENT

#include "shared_argument.h"

#include "morel91_types.hh"

/* Global variables governing the running of the program, as obtained
 *  from the command line parameters.
 */

/* Start and end times */
extern time_type time_step;

/* The range of wavelengths to compute prime production for.
 */
extern wavelength_type min_wavelength;
extern wavelength_type max_wavelength;
extern wavelength_type wavelength_step;

/* The range of depths to compute prime production for.
 */
extern depth_type min_depth;
extern depth_type max_depth;
extern depth_type depth_step;

/* The file to save values versus depth to. NULL
 *  means don't save to file.
 */
extern char *profile_filename;

/* The file to save spectral k versus depth to. NULL means don't save to file.
 */
extern char *spec_irr_depth_filename;

/* The file to save spectral k versus depth 8bit values to. NULL means don't
 *  save to file.
 */
extern char *spec_irr_depth_8bit_filename;

/* The file to read hydrolight LUT values from. NULL means don't read a LUT
 *  and calculate the values internally.
 */
extern char *hydrolight_lut_filename;

/* The percentage of surface irradiance reaching the euphotic depth */
extern float euphotic_ratio;

/* The value for phi_mu_max when computing prime production */
extern float phi_mu_max;

/* The value for a chl max when computing PUR(lambda, Z, t) */
extern Achl_type A_chl_max;

/*
 * Set to CONSTANT, CALCULATE_SURFACE or CALCULATE_DEPTH if A_chl_max should
 *  be left as a constant value, calculated based on the surface value, or
 *  recalculated for each depth.
 */
extern int A_chl_max_recalc;

/* Set to CONSTANT, CALCULATE_SURFACE or CALCULATE_DEPTH if phi_mu_max should
 *  be left as a constant value, calculated based on the surface value, or
 *  recalculated for each depth.
 */
extern int phi_mu_max_recalc;

/* Set to CALC_BY_CHL if phi_mu_max should be calculated
 *  using chloropyll values (the default).
 */
extern int phi_mu_max_calc;

/* Set to CONSTANT, CALCULATE_SURFACE or CALCULATE_DEPTH if Chl should
 *  be left as a constant value, calculated based on the surface value, or
 *  recalculated for each depth.
 */
extern int Chl_recalc;

/* A value for KPUR at 20 degrees C */
extern float KPUR_20;

/* Whether the euphotic depth and spectral irradiance for each depth
 *  should be calculated for every time of the day (TRUE), or just
 *  once (FALSE).
 */
extern int recompute_irr;

/* Whether k values from file should be used, or values should be calculated
 *  from kc and kw.
 */
extern int calculate_k;

/* Whether or not the g parameter to convert vector irradiance
into scalar irradiance has to be calculated from HYDROLIGHT LUT*/
extern int calculate_g;

extern int interpret_arguments (void);

#endif /* #ifndef _MOREL91_ARGUMENT */
