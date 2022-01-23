/* morel91_types.h
 * 
 * Common type definitions used in pp, and some functions to handle them.
 * 
 * Latest modification: 04/08/17 11:18:32
 */

#ifndef _MOREL91_TYPES
#define _MOREL91_TYPES

/* Time measured in whole minutes */
typedef int time_type;

/* Wavelength value type */
typedef int wavelength_type;

/* Depth measured in whole metres - note: is int accurate enough? */
typedef int depth_type;

/* Irradiance value type */
typedef float irr_type;

/* Chlorophyll value type */
typedef float chl_type; 

/* PBM value type */
typedef float pbm_type;

/* Alpha value type */
typedef float alpha_type;

/* Beta value type */
typedef float beta_type;

/* Light attenuation value type */
typedef float k_type;

/* IOP values type */
typedef float ab_type;

typedef float aw_type;
typedef float bw_type;
typedef float Achl_type;

/* Prime production type */
typedef float pp_type;

#endif /* #ifndef _MOREL91_TYPES */
