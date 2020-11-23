/* morel91_argument.c
 * 
 * Interprets arguments from the command line.
 *
 * Latest modification: 04/08/17 11:18:32
 */

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>

#include "morel91_argument.hh"
#include "morel91_defs.hh"
#include "morel91_model.hh"

/* Global variables governing the running of the program, as obtained
 *  from the command line parameters. Default values assigned here.
 */

/* The percentage of surface irradiance reaching the euphotic depth */
float euphotic_ratio = EUPHOTIC_RATIO_DEFAULT;

/* The value for phi_mu_max when computing prime production */
float phi_mu_max = PHI_MU_MAX_DEFAULT;

/* The value for A_chl_max when computing PUR(lambda, Z, t) */
Achl_type A_chl_max = A_CHL_MAX_DEFAULT;

/* Set to CONSTANT, CALCULATE_SURFACE or CALCULATE_DEPTH if A_chl_max should
 *  be left as a constant value, calculated based on the surface value, or
 *  recalculated for each depth.
 */
int A_chl_max_recalc = CONSTANT;

/* Set to CONSTANT, CALCULATE_SURFACE or CALCULATE_DEPTH if phi_mu_max should
 *  be left as a constant value, calculated based on the surface value, or
 *  recalculated for each depth.
 */
int phi_mu_max_recalc = CONSTANT;

/* Set to CONSTANT, CALCULATE_SURFACE or CALCULATE_DEPTH if Chl should
 *  be left as a constant value, calculated based on the surface value, or
 *  recalculated for each depth.
 */
int Chl_recalc = CALCULATE_DEPTH;

/* A value for KPUR */
float KPUR_20 = KPUR_DEFAULT;

/* Whether the euphotic depth and spectral irradiance for each depth
 *  should be calculated for every time of the day (TRUE), or just
 *  once (FALSE).
 */
int recompute_irr = TRUE;

/* Whether k values from file should be used, or values should be calculated
 *  from kc and kw.
 */
int calculate_k = TRUE;

/* Whether or not the g parameter to convert vector irradiance
into scalar irradiance has to be calculated from HYDROLIGHT LUT*/
int calculate_g = FALSE;

/* Whether or not Achl values have been loaded */
int Achl_values_loaded = FALSE;

/* Whether or not Ed values have been loaded */
int ed_values_loaded = FALSE;

/* Start and end times */
time_type time_step = TIME_STEP_DEFAULT;

/* The range of wavelengths to compute prime production for.
 */
wavelength_type min_wavelength = MIN_WAVELENGTH_DEFAULT;
wavelength_type max_wavelength = MAX_WAVELENGTH_DEFAULT;
wavelength_type wavelength_step = WAVELENGTH_STEP_DEFAULT;

/* The range of depths to compute prime production for.
 */
depth_type min_depth = MIN_DEPTH_DEFAULT;
depth_type max_depth = MAX_DEPTH_DEFAULT;
depth_type depth_step = DEPTH_STEP_DEFAULT;

/* The file to save values versus depth to. NULL
 *  means don't save to file.
 */
char *profile_filename = NULL;

/* The file to save spectral k versus depth to. NULL means don't save to file.
 */
char *spec_irr_depth_filename = NULL;

/* The file to save spectral k versus depth 8bit values to. NULL means don't
 *  save to file.
 */
char *spec_irr_depth_8bit_filename = NULL;

/* The file to read hydrolight LUT values from. NULL means don't read a LUT
 *  and calculate the values internally.
 */
char *hydrolight_lut_filename = NULL;

/* Conversion factors for the various data sources.
 */
static float ed_conversion = ED_CONVERT_DEFAULT;
static float chl_conversion = CHL_CONVERT_DEFAULT;
static float beta_conversion = BETA_CONVERT_DEFAULT;
static float kc_conversion = KC_CONVERT_DEFAULT;
static float kw_conversion = KW_CONVERT_DEFAULT;
static float k_conversion = K_CONVERT_DEFAULT;
static float ab_conversion = AB_CONVERT_DEFAULT;
static float aw_conversion = AW_CONVERT_DEFAULT;
static float bw_conversion = BW_CONVERT_DEFAULT;
static float Achl_conversion = ACHL_CONVERT_DEFAULT;
static float st_conversion = ST_CONVERT_DEFAULT;

static int long_command (char *command);
static void display_help (char *subject);
static int set_recalc_policy (int *recalc_setting, char *arg, char *description);

extern int interpret_arguments (void) {
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
   
   /* Check for undefined required values */
   if (!Achl_values_loaded) {
      fprintf(stderr, "%s: Required values for Achl not loaded!\n", argv0);
      return ERROR;
   }
   
   if (!ed_values_loaded) {
      fprintf(stderr, "%s: Required values for Ed not loaded!\n", argv0);
      return ERROR;
   }
   
   return CONTINUE;
}

static int long_command (char *command) {
   /* Is it a read command? */
   if (strstr(command, "read") != NULL) {
      bool retval;
      char *filename = next_arg();
      
      if (!strcmp(command, "ed_read")) {
         /* Load irradiance file into model */
         if (filename == NULL) {
            fprintf(stderr, "%s: please supply filename for --ed_read\n", argv0);
            return ERROR;
         }
         retval = ed.readFile(filename, ed_conversion);
         ed_values_loaded = TRUE;
      } else if (!strcmp(command, "chl_read")) {
         /* Load chlorophyl file into model */
         if (filename == NULL) {
            fprintf(stderr, "%s: please supply filename for --chl_read\n", argv0);
            return ERROR;
         }
         retval = chl.readFile(filename, chl_conversion);
      } else if (!strcmp(command, "beta_read")) {
         /* Load beta file into model */
         if (filename == NULL) {
            fprintf(stderr, "%s: please supply filename for --beta_read\n", argv0);
            return ERROR;
         }
         retval = beta.readFile(filename, beta_conversion);
      } else if (!strcmp(command, "kc_read")) {
         /* Load kc file into model */
         if (filename == NULL) {
            fprintf(stderr, "%s: please supply filename for --kc_read\n", argv0);
            return ERROR;
         }
         retval = kc.readFile(filename, kc_conversion);
      } else if (!strcmp(command, "kw_read")) {
         /* Load kw file into model */
         if (filename == NULL) {
            fprintf(stderr, "%s: please supply filename for --kw_read\n", argv0);
            return ERROR;
         }
         retval = kw.readFile(filename, kw_conversion);
      } else if (!strcmp(command, "k_read")) {
         /* Load k file into model */
         if (filename == NULL) {
            fprintf(stderr, "%s: please supply filename for --k_read\n", argv0);
            return ERROR;
         }
         retval = k.readFile(filename, k_conversion);
         calculate_k = FALSE;
      } else if (!strcmp(command, "ab_read")) {
         /* Load ab file into model */
         if (filename == NULL) {
            fprintf(stderr, "%s: please supply filename for --ab_read\n", argv0);
            return ERROR;
         }
         retval = ab.readFile(filename, ab_conversion);
         calculate_g = TRUE;
      } else if (!strcmp(command, "aw_read")) {
         /* Load aw file into model */
         if (filename == NULL) {
            fprintf(stderr, "%s: please supply filename for --aw_read\n", argv0);
            return ERROR;
         }
         retval = aw.readFile(filename, aw_conversion);
      } else if (!strcmp(command, "bw_read")) {
         /* Load bw file into model */
         if (filename == NULL) {
            fprintf(stderr, "%s: please supply filename for --bw_read\n", argv0);
            return ERROR;
         }
         retval = bw.readFile(filename, bw_conversion);
      } else if (!strcmp(command, "Achl_read")) {
         /* Load achl file into model */
         if (filename == NULL) {
            fprintf(stderr, "%s: please supply filename for --Achl_read\n", argv0);
            return ERROR;
         }
         retval = achl.readFile(filename, Achl_conversion);
         Achl_values_loaded = TRUE;
      } else if (!strcmp(command, "hydrolight_read")) {
         /* Mark the hydrolight LUT file for reading */
         if (filename == NULL) {
            fprintf(stderr,
               "%s: please supply filename for --hydrolight_read\n", argv0);
            return ERROR;
         }
         hydrolight_lut_filename = filename;
         /* Hack!! Assume the file will be read ok, report error inside the
          *  routine read_hydrolight_lut() in morel91_calculate.cc */
         retval = 0;
      } else if (!strcmp(command, "st_read")) {
         /* Load sea temperature file into model */
         if (filename == NULL) {
            fprintf(stderr, "%s: please supply filename for --st_read\n", argv0);
            return ERROR;
         }
         retval = st.readFile(filename, st_conversion);
      } else {
         /* Error - Unknown parameter */
         fprintf(stderr, "%s: Invalid option: %s\n", argv0, command);
         return ERROR;
      }
      
      /* Check for success of reading file */
      if (retval) {
         fprintf(stderr, "%s: could not read file \"%s\" or format incorrect\n",
            argv0, filename);
         return ERROR;
      } else
         return CONTINUE;
      
   /* Non-reading commands */
   } else if (!strcmp(command, "euphotic_ratio")) {
      return read_float("euphotic_ratio",&euphotic_ratio, 0.0,1.0, EQUAL,EQUAL);
      
   } else if (!strcmp(command, "KPUR")) {
      return read_float("KPUR",&KPUR_20, 0.0,0.0, INEQUAL,NO_LIMIT);
      
   } else if (!strcmp(command, "T")) {
      float st_default;
      int retval = read_float("T",&st_default, 0.0,0.0, NO_LIMIT,NO_LIMIT);
      if (retval != ERROR) {
         st.setDefault(st_default);
      }
      return retval;
      
   } else if (!strcmp(command, "phi_mu_max")) {
      phi_mu_max_recalc = CONSTANT;
      return read_float("phi_mu_max",&phi_mu_max, 0.0,0.0, INEQUAL,NO_LIMIT);
      
   } else if (!strcmp(command, "A_chl_max")) {
      A_chl_max_recalc = CONSTANT;
      return read_float("A_chl_max",&A_chl_max, 0.0,0.0, INEQUAL,NO_LIMIT);
      
   } else if (!strcmp(command, "A_chl_max_recalc")) {
      return set_recalc_policy(&A_chl_max_recalc, next_arg(), "A_chl_max_recalc");
      
   } else if (!strcmp(command, "phi_mu_max_recalc")) {
      return set_recalc_policy(&phi_mu_max_recalc, next_arg(), "phi_mu_max_recalc");

   } else if (!strcmp(command, "Chl_recalc")) {
      return set_recalc_policy(&Chl_recalc, next_arg(), "Chl_recalc");

   } else if (!strcmp(command, "no_recompute_irr")) {
      recompute_irr = FALSE;
      return CONTINUE;
      
   } else if (!strcmp(command, "chl")) {
      float v;
      int retval = read_float("chl",&v, 0.0,0.0, INEQUAL,NO_LIMIT);
      if (retval != ERROR) {
         chl.clear();
         chl.setDefault(v);
         Chl_recalc = CONSTANT;
      }
      return retval;
      
   } else if (!strcmp(command, "time_step")) {
      return read_int("time_step",&time_step, 0,0, INEQUAL,NO_LIMIT);
      
   } else if (!strcmp(command, "min_wave")) {
      return read_int("min_wave",&min_wavelength, 0,0, INEQUAL,NO_LIMIT);
   } else if (!strcmp(command, "max_wave")) {
      return read_int("max_wave",&max_wavelength, 0,0, INEQUAL,NO_LIMIT);
   } else if (!strcmp(command, "wave_step")) {
      return read_int("wave_step",&wavelength_step, 0,0, INEQUAL,NO_LIMIT);
      
   } else if (!strcmp(command, "min_depth")) {
      return read_int("min_depth",&min_depth, 0,0, EQUAL,NO_LIMIT);
   } else if (!strcmp(command, "max_depth")) {
      return read_int("max_depth",&max_depth, 0,0, EQUAL,NO_LIMIT);
   } else if (!strcmp(command, "depth_step")) {
      return read_int("depth_step",&depth_step, 0,0, INEQUAL,NO_LIMIT);
      
   } else if (!strcmp(command, "ed_coef")) {
      return read_float("ed_coef",&ed_conversion, 0.0,0.0, NO_LIMIT,NO_LIMIT);
   } else if (!strcmp(command, "ed_div")) {
      float v;
      int retval = read_float("ed_div",&v, 0.0,0.0, INEQUAL,NO_LIMIT);
      ed_conversion = 1.0/v;
      return retval;
      
   } else if (!strcmp(command, "chl_coef")) {
      return read_float("chl_coef",&chl_conversion, 0.0,0.0, NO_LIMIT,NO_LIMIT);
   } else if (!strcmp(command, "chl_div")) {
      float v;
      int retval = read_float("chl_div",&v, 0.0,0.0, INEQUAL,NO_LIMIT);
      chl_conversion = 1.0/v;
      return retval;
      
   } else if (!strcmp(command, "beta_coef")) {
      return read_float("beta_coef",&beta_conversion, 0.0,0.0, NO_LIMIT,NO_LIMIT);
   } else if (!strcmp(command, "beta_div")) {
      float v;
      int retval = read_float("beta_div",&v, 0.0,0.0, INEQUAL,NO_LIMIT);
      beta_conversion = 1.0/v;
      return retval;
      
   } else if (!strcmp(command, "kc_coef")) {
      return read_float("kc_coef",&kc_conversion, 0.0,0.0, NO_LIMIT,NO_LIMIT);
   } else if (!strcmp(command, "kc_div")) {
      float v;
      int retval = read_float("kc_div",&v, 0.0,0.0, INEQUAL,NO_LIMIT);
      kc_conversion = 1.0/v;
      return retval;
      
   } else if (!strcmp(command, "kw_coef")) {
      return read_float("kw_coef",&kw_conversion, 0.0,0.0, NO_LIMIT,NO_LIMIT);
   } else if (!strcmp(command, "kw_div")) {
      float v;
      int retval = read_float("kw_div",&v, 0.0,0.0, INEQUAL,NO_LIMIT);
      kw_conversion = 1.0/v;
      return retval;
      
   } else if (!strcmp(command, "aw_coef")) {
      return read_float("aw_coef",&aw_conversion, 0.0,0.0, NO_LIMIT,NO_LIMIT);
   } else if (!strcmp(command, "aw_div")) {
      float v;
      int retval = read_float("aw_div",&v, 0.0,0.0, INEQUAL,NO_LIMIT);
      aw_conversion = 1.0/v;
      return retval;
      
   } else if (!strcmp(command, "bw_coef")) {
      return read_float("bw_coef",&bw_conversion, 0.0,0.0, NO_LIMIT,NO_LIMIT);
   } else if (!strcmp(command, "bw_div")) {
      float v;
      int retval = read_float("bw_div",&v, 0.0,0.0, INEQUAL,NO_LIMIT);
      bw_conversion = 1.0/v;
      return retval;
      
   } else if (!strcmp(command, "Achl_coef")) {
      return read_float("Achl_coef",&Achl_conversion, 0.0,0.0, NO_LIMIT,NO_LIMIT);
   } else if (!strcmp(command, "Achl_div")) {
      float v;
      int retval = read_float("Achl_div",&v, 0.0,0.0, INEQUAL,NO_LIMIT);
      Achl_conversion = 1.0/v;
      return retval;
      
   } else if (!strcmp(command, "st_coef")) {
      return read_float("st_coef",&st_conversion, 0.0,0.0, NO_LIMIT,NO_LIMIT);
   } else if (!strcmp(command, "st_div")) {
      float v;
      int retval = read_float("st_div",&v, 0.0,0.0, INEQUAL,NO_LIMIT);
      st_conversion = 1.0/v;
      return retval;
      
   } else if (!strcmp(command, "k_coef")) {
      return read_float("k_coef",&k_conversion, 0.0,0.0, NO_LIMIT,NO_LIMIT);
   } else if (!strcmp(command, "k_div")) {
      float v;
      int retval = read_float("k_div",&v, 0.0,0.0, INEQUAL,NO_LIMIT);
      k_conversion = 1.0/v;
      return retval;
      
   } else if (!strcmp(command, "profile_write")) {
      char *s = next_arg();
      if (s == NULL) {
         fprintf(stderr,"%s: please supply a filename for --profile_write\n", argv0);
         return ERROR;
      } else {
         profile_filename = s;
         return CONTINUE;
      }
   } else if (!strcmp(command, "spec_irr_depth_write")) {
      char *s = next_arg();
      if (s == NULL) {
         fprintf(stderr,"%s: please supply a filename for --spec_irr_depth_write\n", argv0);
         return ERROR;
      } else {
         spec_irr_depth_filename = s;
         return CONTINUE;
      }
   } else if (!strcmp(command, "spec_irr_depth_8bit_write")) {
      char *s = next_arg();
      if (s == NULL) {
         fprintf(stderr,"%s: please supply a filename for --spec_irr_depth_8bit_write\n", argv0);
         return ERROR;
      } else {
         spec_irr_depth_8bit_filename = s;
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
         "h - Displays help on a given option\n"
         "ed_read    - uses an irradiance value file for irradiance values\n"
         "ed_coef    - sets the conversion factor as a value\n"
         "ed_div     - sets the conversion factor as the reciprocal of a value\n"
         
         "chl_read   - uses a chlorophyll value file for chlorophyll values\n"
         "chl_coef   - sets the conversion factor as a value\n"
         "chl_div    - sets the conversion factor as the reciprocal of a value\n"
         
         "beta_read  - uses a beta value file for beta values\n"
         "beta_coef  - sets the conversion factor as a value\n"
         "beta_div   - sets the conversion factor as the reciprocal of a value\n"
         
         "kc_read    - uses a kc value file for chlorophyll attenuation values\n"
         "kc_coef    - sets the conversion factor as a value\n"
         "kc_div     - sets the conversion factor as the reciprocal of a value\n"
         
         "kw_read    - uses a kw value file for water attenuation values\n"
         "kw_coef    - sets the conversion factor as a value\n"
         "kw_div     - sets the conversion factor as the reciprocal of a value\n"
         
         "k_read -  uses a k value file for attenuation values, values from"
            " this file will be used instead of calulating from kw and kc.\n"
         "k_coef -  sets the conversion factor as a value\n"
         "k_div -   sets the conversion factor as the reciprocal of a value\n"
         
         "aw_read    - uses an aw value file\n"
         "aw_coef    - sets the conversion factor as a value\n"
         "aw_div     - sets the conversion factor as the reciprocal of a value\n"
         
         "bw_read    - uses a bw value file\n"
         "bw_coef    - sets the conversion factor as a value\n"
         "bw_div     - sets the conversion factor as the reciprocal of a value\n"
         
         "Achl_read  - uses an Achl value file\n"
         "Achl_coef  - sets the conversion factor as a value\n"
         "Achl_div   - sets the conversion factor as the reciprocal of a value\n"
         
         "St_read    - uses an sea temperature value file\n"
         "St_coef    - sets the conversion factor as a value\n"
         "St_div     - sets the conversion factor as the reciprocal of a value\n"
         
         "hydrolight_read  - reads spectral irradiance with depth from file\n"
         
         "euphotic_ratio   - sets the fraction of surface irradiance reaching the"
            " euphotic depth\n"
         "KPUR       - sets the value of KPUR at 20 degrees centigrade\n"
         "T          - sets the temperature (degrees centigrade)\n"
         "chl        - sets a constant value of chlorophyll (CSAT value)\n"
         
         "A_chl_max  - sets the value of A_chl_max\n"
         "phi_mu_max - sets the value of phi_mu_max\n"
         "A_chl_max_recalc    - sets when to recalculate A_chl_max\n"
         "phi_mu_max_recalc   - sets when to recalculate phi_mu_max\n"
         "no_recompute_irr    - if set, then irradiance and euphotic depth values"
            " are not recomputed for each time of the day\n"
         
         "time_step  - sets the time step (minutes)\n"
         "min_wave   - sets the minimum wavelength (nanometres)\n"
         "max_wave   - sets the maximum wavelength (nanometres)\n"
         "wave_step  - sets the wavelength step (nanometres)\n"
         "min_depth  - sets the minimum depth (metres)\n"
         "max_depth  - sets the maximum depth (metres)\n"
         "depth_step - sets the depth step (metres)\n"
         
         "profile_write          - writes the total prime production versus depth information"
            " to disk\n"
         "spec_irr_depth_write   - writes the spectral irr values versus depth"
            " to disk\n"
         "spec_irr_depth_8bit_write   - writes the spectral ed values versus depth"
            " values to disk in 8bit form\n");
   } else if (!strcmp(subject, "h")) {
      printf("Usage: ... -h [option name] ...\n");
      
   } else if (!strcmp(subject, "e_read")) {
      printf("Usage: ... --e_read <filename> ...\n");
   } else if (!strcmp(subject, "e_coef")) {
      printf("Usage: ... --e_coef <number> ...\n");
   } else if (!strcmp(subject, "e_div")) {
      printf("Usage: ... --e_div <number> ...\n");
      
   } else if (!strcmp(subject, "chl_read")) {
      printf("Usage: ... --chl_read <filename> ...\n");
   } else if (!strcmp(subject, "chl_coef")) {
      printf("Usage: ... --chl_coef <number> ...\n");
   } else if (!strcmp(subject, "chl_div")) {
      printf("Usage: ... --chl_div <number> ...\n");
      
   } else if (!strcmp(subject, "pbm_read")) {
      printf("Usage: ... --pbm_read <filename> ...\n");
   } else if (!strcmp(subject, "pbm_coef")) {
      printf("Usage: ... --pbm_coef <number> ...\n");
   } else if (!strcmp(subject, "pbm_div")) {
      printf("Usage: ... --pbm_div <number> ...\n");
      
   } else if (!strcmp(subject, "alpha_read")) {
      printf("Usage: ... --alpha_read <filename> ...\n");
   } else if (!strcmp(subject, "alpha_coef")) {
      printf("Usage: ... --alpha_coef <number> ...\n");
   } else if (!strcmp(subject, "alpha_div")) {
      printf("Usage: ... --alpha_div <number> ...\n");
      
   } else if (!strcmp(subject, "beta_read")) {
      printf("Usage: ... --beta_read <filename> ...\n");
   } else if (!strcmp(subject, "beta_coef")) {
      printf("Usage: ... --beta_coef <number> ...\n");
   } else if (!strcmp(subject, "beta_div")) {
      printf("Usage: ... --beta_div <number> ...\n");
      
   } else if (!strcmp(subject, "kc_read")) {
      printf("Usage: ... --kc_read <filename> ...\n");
   } else if (!strcmp(subject, "kc_coef")) {
      printf("Usage: ... --kc_coef <number> ...\n");
   } else if (!strcmp(subject, "kc_div")) {
      printf("Usage: ... --kc_div <number> ...\n");
      
   } else if (!strcmp(subject, "kw_read")) {
      printf("Usage: ... --kw_read <filename> ...\n");
   } else if (!strcmp(subject, "kw_coef")) {
      printf("Usage: ... --kw_coef <number> ...\n");
   } else if (!strcmp(subject, "kw_div")) {
      printf("Usage: ... --kw_div <number> ...\n");
      
   } else if (!strcmp(subject, "k_read")) {
      printf("Usage: ... --k_read <filename> ...\n");
   } else if (!strcmp(subject, "k_coef")) {
      printf("Usage: ... --k_coef <number> ...\n");
   } else if (!strcmp(subject, "k_div")) {
      printf("Usage: ... --k_div <number> ...\n");
      
   } else if (!strcmp(subject, "aw_read")) {
      printf("Usage: ... --aw_read <filename> ...\n");
   } else if (!strcmp(subject, "aw_coef")) {
      printf("Usage: ... --aw_coef <number> ...\n");
   } else if (!strcmp(subject, "aw_div")) {
      printf("Usage: ... --aw_div <number> ...\n");
      
   } else if (!strcmp(subject, "bw_read")) {
      printf("Usage: ... --bw_read <filename> ...\n");
   } else if (!strcmp(subject, "kw_coef")) {
      printf("Usage: ... --bw_coef <number> ...\n");
   } else if (!strcmp(subject, "kw_div")) {
      printf("Usage: ... --bw_div <number> ...\n");
      
   } else if (!strcmp(subject, "Achl_read")) {
      printf("Usage: ... --Achl_read <filename> ...\n");
   } else if (!strcmp(subject, "Achl_coef")) {
      printf("Usage: ... --Achl_coef <number> ...\n");
   } else if (!strcmp(subject, "Achl_div")) {
      printf("Usage: ... --Achl_div <number> ...\n");
      
   } else if (!strcmp(subject, "St_read")) {
      printf("Usage: ... --St_read <filename> ...\n");
   } else if (!strcmp(subject, "St_coef")) {
      printf("Usage: ... --St_coef <number> ...\n");
   } else if (!strcmp(subject, "St_div")) {
      printf("Usage: ... --St_div <number> ...\n");
      
   } else if (!strcmp(subject, "hydrolight_read")) {
      printf("Usage: ... --hydrolight_read <filename> ...\n");
      
   } else if (!strcmp(subject, "euphotic_ratio")) {
      printf("Usage: ... --euphotic_ratio <number> ...\n");
   } else if (!strcmp(subject, "KPUR")) {
      printf("Usage: ... --KPUR <number> ...\n");
   } else if (!strcmp(subject, "T")) {
      printf("Usage: ... --T <number> ...\n");
   } else if (!strcmp(subject, "chl")) {
      printf("Usage: ... --chl <number> ...\n");
      
   } else if (!strcmp(subject, "A_chl_max")) {
      printf("Usage: ... --A_chl_max <number> ...\n");
   } else if (!strcmp(subject, "phi_mu_max")) {
      printf("Usage: ... --phi_mu_max <number> ...\n");
   } else if (!strcmp(subject, "A_chl_max_recalc")) {
      printf("Usage: ... --A_chl_max_recalc {CONSTANT | SURFACE | DEPTH} ...\n");
   } else if (!strcmp(subject, "phi_mu_max_recalc")) {
      printf("Usage: ... --phi_mu_max_recalc {CONSTANT | SURFACE | DEPTH} ...\n");
   } else if (!strcmp(subject, "norecompute_irr")) {
      printf("Usage: ... --norecompute_irr ...\n");
      
   } else if (!strcmp(subject, "time_step")) {
      printf("Usage: ... --time_step <number> ...\n");
      
   } else if (!strcmp(subject, "min_wave")) {
      printf("Usage: ... --min_wave <number> ...\n");
   } else if (!strcmp(subject, "max_wave")) {
      printf("Usage: ... --max_wave <number> ...\n");
   } else if (!strcmp(subject, "wave_step")) {
      printf("Usage: ... --wave_step <number> ...\n");
      
   } else if (!strcmp(subject, "min_depth")) {
      printf("Usage: ... --min_depth <number> ...\n");
   } else if (!strcmp(subject, "max_depth")) {
      printf("Usage: ... --max_depth <number> ...\n");
   } else if (!strcmp(subject, "depth_step")) {
      printf("Usage: ... --depth_step <number> ...\n");
      
   } else if (!strcmp(subject, "profile_write")) {
      printf("Usage: ... --profile_write <filename> ...\n");
   } else if (!strcmp(subject, "spec_irr_depth_write")) {
      printf("Usage: ... --spec_irr_depth_write <filename> ...\n");
   } else if (!strcmp(subject, "spec_irr_depth_8bit_write")) {
      printf("Usage: ... --spec_irr_depth_8bit_write <filename> ...\n");
      
   } else {
      printf("%s: Unknown option: %s\n", argv0, subject);
   }
}

static int set_recalc_policy (int *recalc_setting, char *arg, char *description) {
   if (arg == NULL) {
      fprintf(stderr,"%s: please supply one of "
                     "'CONSTANT', 'SURFACE' or 'DEPTH' for"
                     "--%s\n", argv0, description);
      return ERROR;
   }
   
   if (!strcmp(arg, "CONSTANT")) {
      *recalc_setting = CONSTANT;
   } else if (!strcmp(arg, "SURFACE")) {
      *recalc_setting = CALCULATE_SURFACE;
   } else if (!strcmp(arg, "DEPTH")) {
      *recalc_setting = CALCULATE_DEPTH;
   } else {
      fprintf(stderr,"%s: please supply one of "
                     "'CONSTANT', 'SURFACE' or 'DEPTH' for "
                     "--%s\n", argv0, description);
      return ERROR;
   }
   
   return CONTINUE;
}
