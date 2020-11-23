/* par_defs.h
 * 
 * Defines for commonly-used constants.
 *
 * Latest modification: 02/07/01 16:21:00
 */

#ifndef _PAR_DEFS
#define _PAR_DEFS

#define TRUE (1==1)
#define FALSE (!TRUE)

#define UNDEFINED -1

/* The fraction of irradiance transmitted through the air/water interface */
#define AIR_WATER_INTERFACE   0.967

/* Max. number of recorded minutes in a day. If this program is to be
 *  modified to calculate PAR over the course of more than
 *  one day, simply increase this.
 */
#define MAX_MINUTES  (60*24)

/* The default start and end times of day */
#define BEGIN_DEFAULT      0
#define END_DEFAULT        MAX_MINUTES
#define TIME_STEP_DEFAULT  1

/* Wavelength values. */
#define MIN_WAVELENGTH_DEFAULT   400
#define MAX_WAVELENGTH_DEFAULT   700
#define WAVELENGTH_STEP_DEFAULT  5

/* Default values used if no input data given */
#define O_3_DEFAULT  270.0
#define H_O_DEFAULT  0.0
#define A_OZ_DEFAULT 0.0
#define A_O_DEFAULT  0.0
#define A_W_DEFAULT  0.0

#define P_DEFAULT       1013.0
#define W_DEFAULT       2.0
#define WM_DEFAULT      4.0
#define AM_DEFAULT      1.0
#define RH_DEFAULT      75.0
#define WV_DEFAULT      2.0
#define V_DEFAULT       15.0
#define ALPHA_DEFAULT   0.8

#define C_DEFAULT       0.0

#define LAT_DEFAULT  51.0
#define LON_DEFAULT  -5.0

/* Maximum and minimum values for constraining extrapolation/interpolation */
#define H_O_MINIMUM  0.0
#define H_O_MAXIMUM  10.0
#define A_OZ_MINIMUM 0.0
#define A_OZ_MAXIMUM 10.0
#define A_O_MINIMUM  0.0
#define A_O_MAXIMUM  10.0
#define A_W_MINIMUM  0.0
#define A_W_MAXIMUM  10.0

/* Default conversion factors for loaded data */
#define H_O_CONVERT_DEFAULT   (10.0)
#define A_OZ_CONVERT_DEFAULT  (1.0)
#define A_O_CONVERT_DEFAULT   (1.0)
#define A_W_CONVERT_DEFAULT   (1.0)
#define THETA_CONVERT_DEFAULT (1.0)

/* A few physical constants */
#define h         (6.625E-34)
#define c         (3.0E8)
#define avagadro  (6.022E23)
#define P0        (1013.25)      /* Standard atmospheric pressure */
#define ecc       (0.0167)       /* Orbital eccentricity */

/* Define pi if it hasn't been defined */
#ifndef M_PI
#define M_PI   3.141592654
#endif /* #ifndef M_PI */

#endif /* #ifndef _PAR_DEFS */
