/* morel91_defs.h
 * 
 * Defines for commonly-used constants.
 *
 * Latest modification: 04/08/17 11:18:32
 */

#ifndef _MOREL91_DEFS
#define _MOREL91_DEFS

#define UNDEFINED -1

#define TRUE (1==1)
#define FALSE (!TRUE)

#define CONSTANT           0
#define CALCULATE_SURFACE  1
#define CALCULATE_DEPTH    2

/* A few physical constants */
#define h         (6.625E-34)
#define c         (3.0E8)
#define avagadro  (6.022E23)
#define P0        (1013.25)      /* Standard atmospheric pressure */
#define ecc       (0.0167)       /* Orbital eccentricity */

/* The fraction of irradiance transmitted through the air/water interface */
#define AIR_WATER_INTERFACE 0.967

/* The default start and end times of day */
#define TIME_STEP_DEFAULT  1

/* Depth values. */
#define MIN_DEPTH_DEFAULT  0
#define MAX_DEPTH_DEFAULT  300
#define DEPTH_STEP_DEFAULT 1

/* Wavelength values. */
#define MIN_WAVELENGTH_DEFAULT   400
#define MAX_WAVELENGTH_DEFAULT   700
#define WAVELENGTH_STEP_DEFAULT  5

/* Default values used if no input data given */
#define PBM_DEFAULT     5.3

/* The ratio of surface irradiance to irradiance at the euphotic depth */
#define EUPHOTIC_RATIO_DEFAULT   0.01

/* The default value for KPUR */
#define KPUR_DEFAULT 80.0

/* The default value for T */
#define T_DEFAULT    20.0

/* The default value for phi_mu_max when computing prime production */
#define PHI_MU_MAX_DEFAULT 0.06

/* The default value for a_chl_max when computing PUR(lambda, Z, t) */
#define A_CHL_MAX_DEFAULT 0.033

/* Default conversion factors for loaded data */
#define ED_CONVERT_DEFAULT    (1.0)
#define CHL_CONVERT_DEFAULT   (1.0)
#define BETA_CONVERT_DEFAULT  (1.0)
#define KC_CONVERT_DEFAULT    (1.0)
#define KW_CONVERT_DEFAULT    (1.0)
#define K_CONVERT_DEFAULT     (1.0)
#define AB_CONVERT_DEFAULT    (1.0)
#define AW_CONVERT_DEFAULT    (100.0)
#define BW_CONVERT_DEFAULT    (1.0)
#define ACHL_CONVERT_DEFAULT  (1.0)
#define ST_CONVERT_DEFAULT    (1.0)

#endif /* #ifndef _MOREL91_DEFS */
