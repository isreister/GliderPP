/* par_types.h
 * 
 * Contains common types used in par.
 * 
 * Latest modification: 02/07/01 16:21:01
 */

#ifndef _PAR_TYPES
#define _PAR_TYPES

typedef float irr_type;          /* Type for solar irradiance (W m^-2 nm^-1) */
typedef float coef_type;         /* Type for coeffiecients. */
typedef float pressure_type;     /* Type for atmospheric pressure (millibars) */
typedef float airmass_type;      /* Type for airmass usually 1-10 */
typedef float percentage_type;   /* Type for a percentage */
typedef float cm_type;           /* Type for precipital water vapour (cm) */
typedef float windspeed_type;    /* Type for windspeed (m s^-1) */
typedef float visibility_type;   /* Type for visibility (km) */
typedef float dobson_type;       /* Type for total ozone (dobson units) */
typedef float degrees_type;      /* Type for an angle (degrees) */
typedef float radians_type;      /* Type for an angle (radians) */
typedef int wavelength_type;     /* Type for a wavelength (nm) */
typedef int time_type;           /* Type for a time (mins) */

#endif /* #ifndef _PAR_TYPES */
