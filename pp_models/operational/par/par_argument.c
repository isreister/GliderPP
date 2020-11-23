/* par_argument.c
 * 
 *   Interprets arguments from the command line.
 *
 * Latest modification: 03/04/30 08:53:52
 */

#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#include "par_argument.h"
#include "par_defs.h"
#include "par_model.h"
#include "par_readmodel.h"

/* Global variables governing the running of the program, as obtained
 *  from the command line parameters. Default values assigned here.
 */

/* Start and end times */
time_type begin = BEGIN_DEFAULT;
time_type end = END_DEFAULT;
time_type time_step = TIME_STEP_DEFAULT;

/* The range of wavelengths to compute par for.
 */
wavelength_type min_wavelength = MIN_WAVELENGTH_DEFAULT;
wavelength_type max_wavelength = MAX_WAVELENGTH_DEFAULT;
wavelength_type wavelength_step = WAVELENGTH_STEP_DEFAULT;

/* The file to save par to. NULL means don't save to file. */
char *par_filename = NULL;
/* The file to save sensor values to. NULL means don't save to file. */
char *sensor_filename = NULL;
/* The file to save total par to. NULL means don't save to file. */
char *total_par_filename = NULL;
/* The file to save solar zenith angle values to. NULL means
 *  don't save to file. */
char *zen_filename = NULL;

/* Conversion factors for the various data sources.
 */
static float h_o_conversion = H_O_CONVERT_DEFAULT;
static float a_oz_conversion = A_OZ_CONVERT_DEFAULT;
static float a_o_conversion = A_O_CONVERT_DEFAULT;
static float a_w_conversion = A_W_CONVERT_DEFAULT;
static float theta_conversion = THETA_CONVERT_DEFAULT;

static int theta_read = 0;

/* The latitude and longitude in degrees */
degrees_type lon = LON_DEFAULT, lat = LAT_DEFAULT;

/* actual atmospheric pressure (millibars) */
pressure_type P = P_DEFAULT;

/* Angstrom exponent */
float alpha = ALPHA_DEFAULT;

/* Total precipitable water in cm^2 area in a
 *  vertical path from the top of the atmosphere
 *  to the surface (cm) */
cm_type WV = WV_DEFAULT;

/* Instantaneous windspeed m s^-1 */
windspeed_type W = W_DEFAULT;

/* Average windspeed over the last 24 hours m s^-1 */
windspeed_type WM = WM_DEFAULT;

/* Day of year measured from Jan 1st */
int D = UNDEFINED;

/* Visiblilty (km) */
visibility_type V = V_DEFAULT;

/* Air Mass */
float AM = AM_DEFAULT;

/* Relative humidity */
percentage_type RH = RH_DEFAULT;

/* Total ozone (Dobson units) */
dobson_type O_3 = O_3_DEFAULT;

/* Cloud cover (0.0-1.0) */
float C = C_DEFAULT;

int interpret_arguments (void);

static int long_command (char *command);
static void display_help (char *subject);

int interpret_arguments (void) {
   char *cur_arg;
   int val;
   
   for (cur_arg = next_arg(); cur_arg != NULL; cur_arg = next_arg()) {
      /* Test the first char of the argument */
      switch (cur_arg[0]) {
         case '-':
         /* argument is an option - now identify option by the following char */
         switch (cur_arg[1]) {
            case 'h':
            /* Display help for the following argument */
            display_help(next_arg());
            return QUIT;
            
            case '-':
            /* A longer option - delegate to long_command */
            if ((val = long_command(cur_arg+2)) != CONTINUE) {
               return val;
            }
            break;
            
            default:
            fprintf(stderr, "%s: Invalid option: %c\n", argv0, cur_arg[1]);
            return ERROR;
         }
         break;
      }
   }
   
   /* Check for required values */
   if (D == UNDEFINED && !theta_read) {
      fprintf(stderr, "%s: D must be specified or theta values read from file"
         " with --theta_read.\n", argv0);
      return ERROR;
   }
   
   if (par_filename == NULL) {
      fprintf(stderr, "%s: par file to write to must be specified with"
         " --par.\n", argv0);
      return ERROR;
   }
   
   return CONTINUE;
}

static int long_command (char *command) {
   
   /* Is it a read command? */
   if (strstr(command, "read") != NULL) {
      char *filename = next_arg();
      int val;
      
      if (!strcmp(command, "atmo_read")) {
         /* Load atmosphere file into model */
         if (filename == NULL) {
            fprintf(stderr, "%s: please supply filename for --atmo_read\n", argv0);
            return ERROR;
         }
         val = read_atmo(filename, h_o_conversion, a_oz_conversion, a_o_conversion,
            a_w_conversion);
      } else if (!strcmp(command, "theta_read")) {
         /* Load atmosphere file into model */
         if (filename == NULL) {
            fprintf(stderr, "%s: please supply filename for --theta_read\n", argv0);
            return ERROR;
         }
         val = read_theta (filename, theta_conversion);
         theta_read = 1;
      } else {
         fprintf(stderr, "%s: unknown option: %s\n", argv0, command);
         return ERROR;
      }
      
      
      /* Check for success of reading file */
      switch (val) {
         case FILE_OK:
         return CONTINUE;
         
         case FILE_ERROR:
         fprintf(stderr, "%s: could not read file %s: ", argv0, filename);
         perror(NULL);
         return ERROR;
         
         case FILE_FORMAT_ERROR:
         fprintf(stderr, "%s: format incorrect in file %s\n", argv0, filename);
         return ERROR;
         
         default:
         fprintf(stderr, "%s: unknown error\n", argv0);
         return ERROR;
      }
      
   /* Non-reading commands */
   } else if (!strcmp(command, "begin")) {
      return read_int("begin",&begin, 0,MAX_MINUTES, EQUAL,EQUAL);
   } else if (!strcmp(command, "end")) {
      return read_int("end",&end, 0,MAX_MINUTES, EQUAL,EQUAL);
   } else if (!strcmp(command, "time_step")) {
      return read_int("time_step",&time_step, 0,0, INEQUAL,NO_LIMIT);
      
   } else if (!strcmp(command, "min_wave")) {
      return read_int("min_wave", &min_wavelength, 0,0, INEQUAL, NO_LIMIT);
   } else if (!strcmp(command, "max_wave")) {
      return read_int("max_wave", &max_wavelength, 0,0, INEQUAL, NO_LIMIT);
   } else if (!strcmp(command, "wave_step")) {
      return read_int("wave_step", &wavelength_step, 0,0, INEQUAL, NO_LIMIT);
      
   } else if (!strcmp(command, "h_o_coef")) {
      return read_float("h_o_coef", &h_o_conversion, 0.0,0.0, NO_LIMIT,NO_LIMIT);
   } else if (!strcmp(command, "h_o_div")) {
      float v;
      int retval = read_float("h_o_div", &v, 0.0,0.0, INEQUAL,NO_LIMIT);
      h_o_conversion = 1.0/v;
      return retval;
      
   } else if (!strcmp(command, "a_oz_coef")) {
      return read_float("a_oz_coef", &a_oz_conversion, 0.0,0.0, NO_LIMIT,NO_LIMIT);
   } else if (!strcmp(command, "a_oz_div")) {
      float v;
      int retval = read_float("a_oz_div", &v, 0.0,0.0, INEQUAL,NO_LIMIT);
      a_oz_conversion = 1.0/v;
      return retval;
      
   } else if (!strcmp(command, "a_o_coef")) {
      return read_float("a_o_coef", &a_o_conversion, 0.0,0.0, NO_LIMIT,NO_LIMIT);
   } else if (!strcmp(command, "a_o_div")) {
      float v;
      int retval = read_float("a_o_div", &v, 0.0,0.0, INEQUAL,NO_LIMIT);
      a_o_conversion = 1.0/v;
      return retval;
      
   } else if (!strcmp(command, "a_w_coef")) {
      return read_float("a_w_coef", &a_w_conversion, 0.0,0.0, NO_LIMIT,NO_LIMIT);
   } else if (!strcmp(command, "a_w_div")) {
      float v;
      int retval = read_float("a_w_div", &v, 0.0,0.0, INEQUAL,NO_LIMIT);
      a_w_conversion = 1.0/v;
      return retval;
      
   } else if (!strcmp(command, "theta_coef")) {
      return read_float("theta_coef", &theta_conversion, 0.0,0.0, NO_LIMIT,NO_LIMIT);
   } else if (!strcmp(command, "theta_div")) {
      float v;
      int retval = read_float("theta_div", &v, 0.0,0.0, INEQUAL,NO_LIMIT);
      theta_conversion = 1.0/v;
      return retval;
      
   /* Latitude and longitude */
   } else if (!strcmp(command, "lat")) {
      return read_float("lat", &lat, -90.0,90.0, EQUAL,EQUAL);
   } else if (!strcmp(command, "lon")) {
      return read_float("lon", &lon, -180.0,180.0, EQUAL,EQUAL);
      
   /* Atmospheric pressure (millibars) */
   } else if (!strcmp(command, "P")) {
      return read_float("P", &P, 0.0,0.0, EQUAL,NO_LIMIT);
      
   /* Angstrom exponent */
   } else if (!strcmp(command, "alpha")) {
      return read_float("alpha", &alpha, 0.0,0.0, INEQUAL,NO_LIMIT);
      
   /* Pecipitable water vapour (cm) */
   } else if (!strcmp(command, "WV")) {
      return read_float("WV", &WV, 0.0,0.0, EQUAL,NO_LIMIT);
      
   /* Wind speed (m s^-1) */
   } else if (!strcmp(command, "W")) {
      return read_float("W", &W, 0.0,0.0, EQUAL,NO_LIMIT);
      
   /* Average wind speed over last 24 hours (m s^-1) */
   } else if (!strcmp(command, "WM")) {
      return read_float("WM", &WM, 0.0,0.0, EQUAL,NO_LIMIT);
      
   /* Days since Jan 1st */
   } else if (!strcmp(command, "D")) {
      return read_int("D", &D, 1,366, EQUAL,EQUAL);
      
   /* Visibility (km) */
   } else if (!strcmp(command, "V")) {
      return read_float("V", &V, 0.0,0.0, INEQUAL,NO_LIMIT);
      
   /* Single-scattering albedo of the aerosol */
   } else if (!strcmp(command, "AM")) {
      return read_float("AM", &AM, 1.0,10.0, EQUAL,EQUAL);
      
   /* Relative humidity */
   } else if (!strcmp(command, "RH")) {
      return read_float("RH", &RH, 0.0,100.0, EQUAL,EQUAL);
      
   /* Ozone */
   } else if (!strcmp(command, "O_3")) {
      return read_float("O_3", &O_3, 0.0,0.0, EQUAL,NO_LIMIT);
      
   /* Cloud cover */
   } else if (!strcmp(command, "C")) {
      return read_float("C", &C, 0.0,1.0, EQUAL,EQUAL);

   /* if total par filename is set then total par is stored into a file at each
      timestep */
   } else if (!strcmp(command, "total_par")) {
      char *s = next_arg();
      total_par_filename = next_arg();
      if (s == NULL) {
         fprintf(stderr,"%s: please supply a filename for --total_par\n",argv0);
         return ERROR;
      } else {
         total_par_filename = s;
         return CONTINUE;
      }
      return CONTINUE;
   } else if (!strcmp(command, "par")) {
      char *s = next_arg();
      if (s == NULL) {
         fprintf(stderr,"%s: please supply a filename for --par\n", argv0);
         return ERROR;
      } else {
         par_filename = s;
         return CONTINUE;
      }
   } else if (!strcmp(command, "sensor")) {
      char *s = next_arg();
      if (s == NULL) {
         fprintf(stderr,"%s: please supply a filename for --sensor\n", argv0);
         return ERROR;
      } else {
         sensor_filename = s;
         return CONTINUE;
      }
   } else if (!strcmp(command, "zen")) {
      char *s = next_arg();
      if (s == NULL) {
         fprintf(stderr,"%s: please supply a filename for --zen\n", argv0);
         return ERROR;
      } else {
         zen_filename = s;
         return CONTINUE;
      }
   } else {
      fprintf(stderr, "%s: unknown option: %s\n", argv0, command);
      return ERROR;
   }
}

static void display_help (char *subject) {
   if (subject == NULL) {
      printf(
         "\nNote: set ???_coef or ???_div BEFORE a ???_read to change the"
            " conversion value. Many ???_read arguments may be repeated, in which"
            " case the data will be appended to already loaded data, different"
            " conversion factors may be given for each read, but the conversion"
            " factor must precede the corresponding ???_read call.\n\n"
         "Help topics available:\n"
         "h - Displays help on a given option\n");
         
      printf(
         "atmo_read - uses an atmosphere value file for atmosphere values\n"
         "h_o_coef - sets the conversion factor as a value\n"
         "h_o_div - sets the conversion factor as the reciprocal of a value\n"
         "a_oz_coef - sets the conversion factor as a value\n"
         "a_oz_div - sets the conversion factor as the reciprocal of a value\n"
         "a_o_coef - sets the conversion factor as a value\n"
         "a_o_div - sets the conversion factor as the reciprocal of a value\n"
         "a_w_coef - sets the conversion factor as a value\n"
         "a_w_div - sets the conversion factor as the reciprocal of a value\n");
         
      printf(
         "theta_read - reads the zenith angles from the specified file\n"
         "theta_coef - sets the conversion factor as a value\n"
         "theta_div - sets the conversion factor as the reciprocal of a value\n");
         
      printf(
         "begin - sets the beginning time (minute of the day)\n"
         "end - sets the ending time (minute of the day)\n"
         "time_step - sets the time step (minutes)\n");
         
      printf(
         "min_wave - sets the minimum wavelength (nanometres)\n"
         "max_wave - sets the maximum wavelength (nanometres)\n"
         "wave_step - sets the wavelength step (nanometres)\n");
         
      printf(
         "AM - sets the air mass\n"
         "RH - sets the relative humidity\n");
         
      printf(
         "alpha - Sets angstrom exponent\n"
         "WV - Sets the precipitable water vapour (cm)\n"
         "P - Sets the actual atmospheric pressure (millibars)\n"
         "W - Sets the actual windspeed (m s^-1)\n"
         "WM - Sets the average windspeed over the last 24 hours (m s^-1)\n"
         "D - sets the day of the year since Jan 1st\n"
         "V - sets the visibility (km)\n"
         "O_3 - total ozone (Dobson units)\n"
         "C - sets the cloud cover (0.0 [Clear] - 1.0 [Totally overcast])\n");

      printf(
         "lat - sets the latitude in decimal degrees\n"
         "lon - sets the longitude in decimal degrees\n");
         
      printf(
         "par - specifies the file to write the PAR values to\n"
         "sensor - specifies the file to write the sensor values to\n"
         "total_par - specifies the file to write total PAR per timestep to\n"
         "zen - specifies the file to write the sun zenith angle values to\n");
   } else if (!strcmp(subject, "h")) {
      printf("Usage: ... -h [option name] ...\n");
      
   } else if (!strcmp(subject, "atmo_read")) {
      printf("Usage: ... --atmo_read <filename> ...\n");
   } else if (!strcmp(subject, "h_o_coef")) {
      printf("Usage: ... --h_o_coef <number> ...\n");
   } else if (!strcmp(subject, "h_o_div")) {
      printf("Usage: ... --h_o_div <number> ...\n");
   } else if (!strcmp(subject, "a_oz_coef")) {
      printf("Usage: ... --a_oz_coef <number> ...\n");
   } else if (!strcmp(subject, "a_oz_div")) {
      printf("Usage: ... --a_oz_div <number> ...\n");
   } else if (!strcmp(subject, "a_o_coef")) {
      printf("Usage: ... --a_o_coef <number> ...\n");
   } else if (!strcmp(subject, "a_o_div")) {
      printf("Usage: ... --a_o_div <number> ...\n");
   } else if (!strcmp(subject, "a_w_coef")) {
      printf("Usage: ... --a_w_coef <number> ...\n");
   } else if (!strcmp(subject, "a_w_div")) {
      printf("Usage: ... --a_w_div <number> ...\n");
      
   } else if (!strcmp(subject, "theta_read")) {
      printf("Usage: ... --theta_read <filename> ...\n");
   } else if (!strcmp(subject, "theta_coef")) {
      printf("Usage: ... --theta_coef <number> ...\n");
   } else if (!strcmp(subject, "theta_div")) {
      printf("Usage: ... --theta_div <number> ...\n");
   
   } else if (!strcmp(subject, "lat")) {
      printf("Usage: ... --lat <number> ...\n");
   } else if (!strcmp(subject, "lon")) {
      printf("Usage: ... --lon <number> ...\n");
      
   } else if (!strcmp(subject, "alpha")) {
      printf("Usage: ... --alpha <number> ...\n");
   } else if (!strcmp(subject, "WV")) {
      printf("Usage: ... --WV <number> ...\n");
   } else if (!strcmp(subject, "P")) {
      printf("Usage: ... --P <number> ...\n");
   } else if (!strcmp(subject, "W")) {
      printf("Usage: ... --W <number> ...\n");
   } else if (!strcmp(subject, "WM")) {
      printf("Usage: ... --WM <number> ...\n");
   } else if (!strcmp(subject, "D")) {
      printf("Usage: ... --D <number> ...\n");
   } else if (!strcmp(subject, "V")) {
      printf("Usage: ... --V <number> ...\n");
   } else if (!strcmp(subject, "O_3")) {
      printf("Usage: ... --O_3 <number> ...\n");
   } else if (!strcmp(subject, "C")) {
      printf("Usage: ... --C <number> ...\n");

   } else if (!strcmp(subject, "AM")) {
      printf("Usage: ... --AM <number> ...\n");
   } else if (!strcmp(subject, "RH")) {
      printf("Usage: ... --RH <number> ...\n");
   } else if (!strcmp(subject, "ta_865")) {
      printf("Usage: ... --ta_865 <number> ...\n");
   } else if (!strcmp(subject, "Hoz")) {
      printf("Usage: ... --Hoz <number> ...\n");
   } else if (!strcmp(subject, "par")) {
      printf("Usage: ... --par <filename> ...\n");
   } else if (!strcmp(subject, "sensor")) {
      printf("Usage: ... --sensor <filename> ...\n");
   } else if (!strcmp(subject, "total_par")) {
      printf("Usage: ... --total_par <filename> ...\n");
   } else if (!strcmp(subject, "zen")) {
      printf("Usage: ... --zen <filename> ...\n");
      
   } else {
      printf("%s: Unknown option: %s\n", argv0, subject);
   }
}
