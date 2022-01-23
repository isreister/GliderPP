/* par_argument.h
 * 
 * Interprets arguments from the command line.
 *
 * Latest modification: 03/04/30 08:46:34
 */

#ifndef _PAR_ARGUMENT
#define _PAR_ARGUMENT

#include "shared_argument.h"
#include "par_types.h"

/* Global variables governing the running of the program, as obtained
 *  from the command line parameters.
 */
extern pressure_type P;       /* actual atmospheric pressure (millibars) */
extern percentage_type RH;    /* relative humidity % */
extern cm_type WV;            /* Total precipitable water in cm^2 area in a
                               *  vertical path from the top of the atmosphere
                               *  to the surface (cm) */
extern windspeed_type WM;     /* Average windspeed over the last 24
                               *  hours m s^-1 */
extern windspeed_type W;      /* Instantaneous windspeed m s^-1 */
extern float alpha;           /* Angstrom exponent */
extern int D;                 /* Day of year measured from Jan 1st */
extern dobson_type O_3;       /* Total ozone (Dobson units) */
extern float AM;              /* Air Mass */
extern percentage_type RH;    /* Relative humidity */
extern visibility_type V;     /* Visiblilty (km) */

extern degrees_type lon, lat; /* The latitude and longitude in degrees */

extern float C;               /* Cloud cover (0.0-1.0) */

/* Start and end times */
extern time_type begin;
extern time_type end;
extern time_type time_step;

/* The range of wavelengths to compute par for. */
extern wavelength_type min_wavelength;
extern wavelength_type max_wavelength;
extern wavelength_type wavelength_step;

/* The file to save PAR values to. NULL means don't save to file. */
extern char *par_filename;
/* The file to save hemispherical values to. NULL means don't save to file. */
extern char *sensor_filename;
/* The file to save PAR values to. NULL means don't save to file. */
extern char *total_par_filename;
/* The file to save solar zenith angle values to. NULL means
 *  don't save to file. */
extern char *zen_filename;

extern int interpret_arguments (void);

#endif /* #ifndef _PAR_ARGUMENT */
