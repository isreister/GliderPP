/* morel91_calculate.c
 * 
 * Calculates prime production for a water column over a day. Many of the
 *  functions and variables in this module take their names from Morel 1991
 *
 * Latest modification: 04/08/17 11:18:33
 */

#include <math.h>
#include <stdio.h>
#include <stdlib.h>

#include "morel91_calculate.hh"
#include "morel91_types.hh"
#include "morel91_defs.hh"
#include "morel91_model.hh"
#include "morel91_argument.hh"

/* Storage space for spectral irradiance ratios at each depth at the current
 *  time, this will be initialised by a call to calculate euphotic depth().
 */
static float **irr_ratio;

/* Storage space for prime production at each depth. */
static pp_type *pp_depth;

/* The number of wavelengths, and depths for which we stop and
 *  calculate at. */
static int num_wavelengths, num_depths;

/* These three functions do the calculations themselves. */
static pp_type integrate_over_time (void);
static pp_type integrate_over_depth (time_type t, depth_type Ze);
static pp_type integrate_over_wavelength (time_type t, depth_type Z,
   chl_type mean_Chl_value);

/* Sub-functions for working out prime-production */
static float KPUR (time_type t, depth_type Z);
static chl_type Chl (time_type t, depth_type Z);
static chl_type mean_Chl (time_type, depth_type Z0, depth_type Z1);
static float PUR (wavelength_type l, depth_type Z, time_type t,
   chl_type mean_Chl_value);
static float PAR (wavelength_type l, depth_type Z, time_type t,
   chl_type mean_Chl_value);
static pp_type f (time_type t, depth_type Z, float PAR_value);
static float Ed (wavelength_type l, depth_type Z, time_type t);
static float g (wavelength_type l, time_type t, chl_type mean_Chl_value);
static float b (wavelength_type l, chl_type mean_Chl_value);
static float a (wavelength_type l, chl_type mean_Chl_value);
static float y (wavelength_type l);

/* Calculates the euphotic depth and returns it, also in the
 *  process calculates the ratio of surface irradiance to
 *  that at every depth down to the euphotic depth and
 *  stores the values in irr_ratio.
 */
static depth_type calculate_euphotic_depth(time_type t);

/* Calculates the euphotic depth as given by a hydrolight LUT file. It also
 *  reads the LUT (irr_ratio) for spectral light values as a fraction of the
 *  surface value. It is assumed that the LUT has spectral values from
 *  min_waveslength up to max_wavelength in wavelength_step intervals, and that
 *  the depths are recorded at every depth_step metres. It returns a non-zero
 *  number if there was a problem reading the file (read error or format
 *  problem), or zero on success.
 */
static int read_hydrolight_lut (const char *filename,
   depth_type *euphotic_depth);

/* Functions to write out intermediate calculation data to disk. */
static void write_profile (void);
static void write_spectral_irr_depth (void);
static void write_spectral_irr_depth_8bit (void);

/* These functions deal with the allocation and deallocation
 *  of dynamically allocated temporary memory, and they also
 *  work out values for num_wavelengths and num_depths. */
static int alloc_temporary(void);
static void dealloc_temporary(void);

/* Functions to calculate values for A_chl_max and phi_mu_max based on
 *  a chlorophyll value */
static Achl_type calculate_A_chl_max (chl_type Chl_value);
static float calculate_phi_mu_max (chl_type Chl_value);

static void display_input_parameters(void);

pp_type calculate (void) {
   pp_type result;
   
   /* Allocate some temporary memory */
   if (alloc_temporary()) {
      perror("Couldn't allocate temporary memory for calculations");
      exit(-1);
   }
   
   /* Display input parameters */
   display_input_parameters();
   
   /* Calculate prime production */
   result = integrate_over_time();
   
   /* Write pp_depth to disk if necessary. */
   write_profile();
   
   /* Write spectral k to disk if necessary. */
   write_spectral_irr_depth();
   
   /* Write spectral k to disk if necessary. (in 8bit form) */
   write_spectral_irr_depth_8bit ();
   
   /* Deallocate temporary memory */
   dealloc_temporary();
   
   return result;
}

static pp_type integrate_over_time (void) {
   pp_type total = 0.0;
   time_type t;
   depth_type Ze;
   
   /* Two possible loops, the first recomputes spectral irr with depth
    *  for each time (slow). The second possible loop only calculates it
    *  once which is faster. But if chl or other relevant values
    *  change with time then the slower loop should be used.
    */
   if (recompute_irr) {
      /* For each time... */
      for (t = ed.getFirstMinute(); t <= ed.getLastMinute(); t += time_step) {
         Ze = calculate_euphotic_depth(t);
         total += integrate_over_depth(t, Ze) * time_step * 60.0;
      }
   } else {
      Ze = calculate_euphotic_depth(720);
      /* For each time... */
      for (t = ed.getFirstMinute(); t <= ed.getLastMinute(); t += time_step) {
         total += integrate_over_depth(t, Ze) * time_step * 60.0;
      }
   }
   
   return total;
}

static pp_type integrate_over_depth (time_type t, depth_type Ze) {
   pp_type total = 0.0, temp;
   depth_type Z;
   chl_type Chl_value, mean_Chl_value = mean_Chl(t, min_depth, Ze);
   int depth_index;
   
   /* Print out the time and euphotic depth */
   printf("%2d:%02d Euphotic depth = %dm\n",
      t/60, t%60, Ze);
   
   /* Do we need to recalculate A_chl_max or phi_mu_max for the surface Chl value? */
   Chl_value = Chl(t, 0);
   if (A_chl_max_recalc == CALCULATE_SURFACE) {
      A_chl_max = calculate_A_chl_max(Chl_value);
   }
   if (phi_mu_max_recalc == CALCULATE_SURFACE) {
      phi_mu_max = calculate_phi_mu_max(Chl_value);
   }

   /* For each depth... */
   depth_index = 0;
   for (Z = min_depth; Z <= Ze; Z += depth_step) {
      /* Do we need to recalculate A_chl_max or phi_mu_max for the depth Chl value? */
      Chl_value = Chl(t, Z);
      if (A_chl_max_recalc == CALCULATE_DEPTH) {
         A_chl_max = calculate_A_chl_max(Chl_value);
      }
      if (phi_mu_max_recalc == CALCULATE_DEPTH) {
         phi_mu_max = calculate_phi_mu_max(Chl_value);
      }
      
      temp = integrate_over_wavelength(t, Z, mean_Chl_value) * depth_step;
      pp_depth[depth_index] += temp*time_step*60.0;
      total += temp;
      
      depth_index++;
   }
   
   return total;
}

static pp_type integrate_over_wavelength (time_type t, depth_type Z,
   chl_type mean_Chl_value) {
   
   float PUR_total = 0.0;
   wavelength_type l;
   float x;
   
   /* Calculate x */
   for (l = min_wavelength; l <= max_wavelength; l += wavelength_step) {
      PUR_total += PUR(l,Z,t, mean_Chl_value);
   }
   PUR_total *= wavelength_step;
   x = PUR_total/KPUR(t,Z);
   
   return (12.0 * phi_mu_max) * (A_chl_max * Chl(t,Z) * PUR_total) * f(t, Z, x);
}

/* Sub-functions for working out prime-production */
static float KPUR (time_type t, depth_type Z) {
   return (KPUR_20/1E6) * pow(1.065, st(t,Z)-20.0);
}

static chl_type Chl (time_type t, depth_type Z) {
   if (Chl_recalc == CALCULATE_SURFACE || Chl_recalc == CONSTANT) {
      return chl(t,0);
   } else {
      return chl(t,Z);
   }
}

/* Calculates the mean chlorophyll between two depths - chl sampled every
 *  depth_step metres.
 */
static chl_type mean_Chl (time_type t, depth_type Z0, depth_type Z1) {
   chl_type total_chl = 0.0;
   depth_type Z;
   int num_samples = 0;
   
   for (Z = Z0; Z <= Z1; Z += depth_step) {
      total_chl += Chl(t, Z);
      num_samples++;
   }
   
   if (num_samples == 0) {
      return Chl(t, Z0);
   } else {
      return total_chl/num_samples;
   }
}

static float PUR (wavelength_type l, depth_type Z, time_type t,
   chl_type mean_Chl_value) {
   
   return PAR(l,Z,t, mean_Chl_value) * achl(l);
}

static float PAR (wavelength_type l, depth_type Z, time_type t,
   chl_type mean_Chl_value) {
   float mu0 = ed.getMu0(t, l);
   if (calculate_g){
      return Ed(l,Z,t) * (1.0/mu0) * sqrt (1.0 + (0.425*mu0 - 0.19) *
         ab(Z,l)) * l * (1.0E-9)*(1.0/(h*c))*(1.0/avagadro);
   } else {
      return Ed(l,Z,t) * g(l,t,mean_Chl_value) * l *
         (1.0E-9)*(1.0/(h*c))*(1.0/avagadro);
   }
}

static pp_type f (time_type t, depth_type Z, float x) {
   if (x == 0.0) {
      return 1.0;
   } else {
      return (1.0/x) * (1.0-exp(-x)) * exp(-beta(t,Z)*x);
   }
}

/* Returns the downwelling irradiance at a given wavelength, depth and time.
 */
static float Ed (wavelength_type l, depth_type Z, time_type t) {
   int depth_index = (Z - min_depth)/(depth_step);
   int wavelength_index = (l - min_wavelength)/(wavelength_step);
   
   return irr_ratio[depth_index][wavelength_index] * ed(t, l);
}

static float g (wavelength_type l, time_type t, chl_type mean_Chl_value) {
   float mu0 = ed.getMu0(t, l);
   return (1.0/mu0) *
      sqrt (1.0 + (0.425*mu0 - 0.19) *
         b(l,mean_Chl_value)/a(l,mean_Chl_value));
}

static float b (wavelength_type l, chl_type mean_Chl_value) {
   return bw(l) + (550.0/l)*0.3*pow(mean_Chl_value, 0.62);
}

static float a (wavelength_type l, chl_type mean_Chl_value) {
   return (aw(l) + 0.06*achl(l)*pow(mean_Chl_value, 0.65)) * (1 + 0.2*y(l));
}

static float y (wavelength_type l) {
   return exp(-0.014*(l-440));
}

/* Returns the euphotic depth at a given time of day. It also generates the
 *  LUT (irr_ratio) for spectral light values as a fraction of the surface
 *  value.
 */
static depth_type calculate_euphotic_depth(time_type t) {
   wavelength_type l;      /* The current wavelength */
   float total;            /* The total ratio at the current depth. */
   depth_type Z;           /* The current depth. */
   k_type kt;              /* Total K (absorbtion) */
   int i;                  /* Used in iterating over depth indices */
   int j;                  /* Used in iterating over wavelength indices */
   
   /* Read hydrolight LUT if there is one given. */
   if (hydrolight_lut_filename != NULL) {
      depth_type euphotic_depth;
      if (read_hydrolight_lut(hydrolight_lut_filename, &euphotic_depth)) {
         fprintf(stderr, "Error reading hydrolight LUT file (format incorrect "
            "or read error)\n");
         exit(1);
      }
      return euphotic_depth;
   }
   
   /* The first depth of water must be specifically initialised to 1.0 */
   for (j = 0; j < num_wavelengths; j++) {
      irr_ratio[0][j] = 1.0;
   }
   
   /* Keep going down until light_coef < euphotic ratio,
    *  or we reach max_depth */
   i = 1;
   for (Z = min_depth+depth_step; Z < max_depth; Z += depth_step) {
      j = 0;
      total = 0.0;
      
      for (l = min_wavelength; l <= max_wavelength; l += wavelength_step) {
         /* Get values for k for water and chlorophyll */
         if (calculate_k) {
            /* Get values for k for water and chlorophyll */
            kt = kw(l) + kc(chl(t,Z), l);
         } else {
            kt = k(Z, l);
         }
         irr_ratio[i][j] = irr_ratio[i-1][j] * exp(-kt * depth_step);
         total += irr_ratio[i][j];
         j++;
      }
      
      if (total/num_wavelengths < euphotic_ratio) {
         break;
      }
      
      i++;
   }
   
   return Z;
}

/* Calculates the euphotic depth as given by a hydrolight LUT file. It also
 *  reads the LUT (irr_ratio) for spectral light values as a fraction of the
 *  surface value. It is assumed that the LUT has spectral values from
 *  min_waveslength up to max_wavelength in wavelength_step intervals, and that
 *  the depths are recorded at every depth_step metres. It returns a non-zero
 *  number if there was a problem reading the file (read error or format
 *  problem), or zero on success.
 */
static int read_hydrolight_lut (const char *filename,
   depth_type *euphotic_depth) {
   wavelength_type l;      /* The current wavelength */
   float total;            /* The total ratio at the current depth. */
   depth_type Z;           /* The current depth. */
   int i;                  /* Used in iterating over depth indices */
   int j;                  /* Used in iterating over wavelength indices */
   FILE *in;
   
   /* Until we find the actual euphotic depth, assume that it's max_depth */
   *euphotic_depth = max_depth;
   
   in = fopen(filename, "r");
   if (in == NULL) {
      return 2;
   }
   
   i = 0;
   for (Z = min_depth; Z < max_depth; Z += depth_step) {
      j = 0;
      total = 0.0;
      for (l = min_wavelength; l <= max_wavelength; l += wavelength_step) {
         if (fscanf(in, " %f ", &(irr_ratio[i][j])) != 1) {
            if (j == 0) {
               /* Run out of depths, say that we've reached the euphotic depth
                *  here but give a warning. */
               *euphotic_depth = Z;
               fclose(in);
               printf("Warning: actual euphotic depth not reached"
                  " when using hydrolight data from %s\n", filename);
               return 0;
            }
            fclose(in);
            return 1;
         }
         total += irr_ratio[i][j];
         j++;
      }
      
      /* Have we found the euphotic depth? */
      if (total/num_wavelengths < euphotic_ratio) {
         *euphotic_depth = Z;
         break;
      }
      
      i++;
   }

   *euphotic_depth = Z;
   fclose(in);
   return 0;
}

/* Functions to write out intermediate calculation data to disk. */
static void write_profile (void) {
   if (profile_filename != NULL) {
      FILE *out = fopen(profile_filename, "w");
      depth_type Z;  /* To iterate over depth. */
      depth_type Ze = calculate_euphotic_depth(720);
      chl_type Chl_value, mean_Chl_value = mean_Chl(720, min_depth, Ze);
      wavelength_type l;
      
      float PUR_total, PAR_watts_total, PAR_einsteins_total;
      int depth_index;
      
      if (out == NULL) {
         return;
      }
      
      /* Write out the pp value at each depth. */
      depth_index = 0;
      fprintf(out, "Z\tPP\tAchl_max\tChl\tPhi_mu_max\tPUR_total"
         "\tPAR_total/uE m^-2 s^-1\tPAR_total/W m^-2\tEd(400nm)/W m^-2 nm^-1\tBeta\tKPUR\n");
      Chl_value = Chl(720, 0);
      if (A_chl_max_recalc == CALCULATE_SURFACE) {
         A_chl_max = calculate_A_chl_max(Chl_value);
      }
      if (phi_mu_max_recalc == CALCULATE_SURFACE) {
         phi_mu_max = calculate_phi_mu_max(Chl_value);
      }
      for (Z = min_depth; Z <= Ze; Z += depth_step) {
         PUR_total = 0.0, PAR_einsteins_total = 0.0, PAR_watts_total = 0.0;
         for (l = min_wavelength; l <= max_wavelength; l += wavelength_step) {
            float ed_lambda = Ed(l,Z,720);
            PUR_total += PUR(l,Z,720, mean_Chl_value);
            PAR_watts_total  += ed_lambda;
            PAR_einsteins_total += ed_lambda*l
               * (1E6)*(1.0E-9)*(1.0/(h*c*avagadro));
         }
         PUR_total *= wavelength_step;
         PAR_watts_total *= wavelength_step;
         PAR_einsteins_total *= wavelength_step;
         
         Chl_value = Chl(720, Z);
         if (A_chl_max_recalc == CALCULATE_DEPTH) {
            A_chl_max = calculate_A_chl_max(Chl_value);
         }
         if (phi_mu_max_recalc == CALCULATE_DEPTH) {
            phi_mu_max = calculate_phi_mu_max(Chl_value);
         }
         fprintf(out, "%d\t%7g\t%7g\t%7g\t%7g\t%7g\t%7g\t%7g\t%7g\t%7g\t%7g\n",
            Z, pp_depth[depth_index], A_chl_max,
            Chl_value, phi_mu_max, PUR_total, PAR_einsteins_total,
            PAR_watts_total, Ed(400,Z,720), beta(720,Z), KPUR(720,Z));
         depth_index++;
      }
      
      fclose(out);
   }
}

static void write_spectral_irr_depth (void) {
   if (spec_irr_depth_filename != NULL) {
      int i;               /* To iterate over depth indices. */
      int j;               /* To iterate over wavelength indices. */
      depth_type Z;        /* To iterate over depth. */
      wavelength_type l;   /* To iterate over wavelength. */
      FILE *out = fopen(spec_irr_depth_filename, "w");
      
      if (out == NULL) {
         return;
      }
      
      /* Write out the wavelength column headers. */
      for (l = min_wavelength; l <= max_wavelength; l+= wavelength_step) {
         fprintf(out, "\t%7d", l);
      }
      fprintf(out, "\n");
      
      /* Write out the values at each depth. */
      i = 0;
      for (Z = min_depth; Z <= max_depth; Z += depth_step) {
         /* Write out the actual depth in metres. */
         fprintf(out, "%d", Z);
         
         /* Write out the values at each wavelength for the current
          *  depth. */
         for (j = 0; j < num_wavelengths; j++) {
            fprintf(out, "\t%07.5f", irr_ratio[i][j]);
         }
         fprintf(out, "\n");
         
         i++;
      }
      
      fclose(out);
   }
}

static void write_spectral_irr_depth_8bit (void) {
   if (spec_irr_depth_8bit_filename != NULL) {
      int i;               /* To iterate over depth indices. */
      int j;               /* To iterate over wavelength indices. */
      depth_type Z;        /* To iterate over depth. */
      FILE *out = fopen(spec_irr_depth_8bit_filename, "wb");
      unsigned char *row;
      
      if (out == NULL) {
         return;
      }
      
      row = (unsigned char *)malloc(num_wavelengths * sizeof(unsigned char));
      
      if (row == NULL) {
         fclose(out);
         return;
      }
      
      /* Write out the values at each depth. */
      i = 0;
      for (Z = min_depth; Z <= max_depth; Z += depth_step) {
         /* Write out the values at each wavelength for the current
          *  depth. */
         for (j = 0; j < num_wavelengths; j++) {
            row[j] = (unsigned char)(irr_ratio[i][j] * 255);
         }
         fwrite(row, sizeof(unsigned char), num_wavelengths, out);
         
         i++;
      }
      
      free(row);
      fclose(out);
   }
}

/* These functions deal with the allocation and deallocation
 *  of dynamically allocated temporary memory. */
static int alloc_temporary(void) {
   int i, j;
   
   num_wavelengths = ((max_wavelength - min_wavelength)/wavelength_step) + 1;
   num_depths = ((max_depth - min_depth)/depth_step) + 1;
   
   /* Allocate pp_depth. (1-d array) */
   pp_depth = (pp_type*)malloc(sizeof(pp_type) * num_depths);
   if (pp_depth == NULL) {
      dealloc_temporary();
      return -1;
   }
   
   /* Initialise pp_depth to 0.0 */
   for (i = 0; i < num_depths; i++) {
      pp_depth[i] = 0.0;
   }
   
   /* Allocate irr_ratio. (2-d array) */
   irr_ratio = (float **)malloc(num_depths * sizeof(float *));
   if (irr_ratio == NULL) {
      dealloc_temporary();
      return -1;
   }
   
   for (i = 0; i < num_depths; i++) {
      irr_ratio[i] = (float *)malloc(num_wavelengths * sizeof(float));
      if (irr_ratio[i] == NULL) {
         dealloc_temporary();
         return -1;
      } else {
         /* Initialise each value to 0.0 */
         for (j = 0; j < num_wavelengths; j++) {
            irr_ratio[i][j] = 0.0;
         }
      }
   }
   
   return 0;
}

static void dealloc_temporary(void) {
   int i;
   
   /* Deallocate pp_depth. (1-d array) */
   if (pp_depth != NULL) {
      free(pp_depth);
   }
   
   /* Deallocate irr_ratio. (2-d array) */
   if (irr_ratio != NULL) {
      for (i = 0; i < num_depths; i++) {
         if (irr_ratio[i] != NULL) {
            free(irr_ratio[i]);
         }
      }
      free(irr_ratio);
   }
}

static Achl_type calculate_A_chl_max (chl_type Chl_value) {
   return 40.3 * pow(Chl_value, -0.33) / 1000.0;
}

static float calculate_phi_mu_max (chl_type Chl_value) {
   return 0.05 * pow(Chl_value,0.66) / (pow(Chl_value,0.66)+0.44);
}

static void display_input_parameters(void) {
   printf("KPUR(20)=\t%g micro Einsteins m^-2 s^-1\n", KPUR_20);
   printf("begin=\t%2d:%02d\nend=\t%2d:%02d\ntime_step=\t%d mins\n",
      ed.getFirstMinute()/60,ed.getFirstMinute()%60,
      ed.getLastMinute()/60,ed.getLastMinute()%60,
      time_step);
   printf("min_wavelength=\t%d nm\nmax_wavelength=\t%d nm\nwavelength_step=\t%d nm\n",
      min_wavelength,
      max_wavelength,
      wavelength_step);
   printf("min_depth=\t%d m\nmax_depth=\t%d m\ndepth_step=\t%d m\n",
      min_depth,
      max_depth,
      depth_step);
   printf("phi_mu_max=\t");
   if (Chl_recalc == CONSTANT) {
      printf("%f\t", phi_mu_max);
      printf("Calculated using Csat\n");
   } else {
      switch (phi_mu_max_recalc) {
         case CONSTANT:
         printf("%g (mol C) E^-1\n", phi_mu_max);
         break;
         case CALCULATE_SURFACE:
         printf("Calculated using Chl(0) (Takes surface value)\n");
         break;
         case CALCULATE_DEPTH:
         printf("Calculated using Chl(Z) (Varies with depth)\n");
         break;
      }
   }
   printf("A_chl_max=\t");
   if (Chl_recalc == CONSTANT) {
      printf("%f\t", A_chl_max);
      printf("Calculated using Csat\n");
   } else {
      switch (A_chl_max_recalc) {
         case CONSTANT:
         printf("%g m^2 (mg Chl)^-1\n", A_chl_max);
         break;
         case CALCULATE_SURFACE:
         printf("Calculated using Chl(0) (Takes surface value)\n");
         break;
         case CALCULATE_DEPTH:
         printf("Calculated using Chl(Z) (Varies with depth)\n");
         break;
      }
   }
   printf("Chl(Z)=\t");
   switch (Chl_recalc) {
      case CONSTANT:
      printf("Csat=%g mg Chl m^-3\n", chl(0,0));
      break;
      case CALCULATE_SURFACE:
      printf("Real_Chl(0) (Takes surface value)\n");
      break;
      case CALCULATE_DEPTH:
      printf("Real_Chl(Z) (Varies with depth)\n");
      break;
   }
}   
