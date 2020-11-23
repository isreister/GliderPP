/* par_calculate.c
 * 
 * Calculates PAR.
 * 
 * Latest modification: 06/01/10 12:25:16
 */

#include <math.h>
#include <stdio.h>

#include "par_argument.h"
#include "par_calculate.h"
#include "par_defs.h"
#include "par_model.h"

/* The solar zenith angle in degrees and radians. */
static degrees_type theta_degrees;
static radians_type theta_radians;

/* The sine and cosine of the sun zenith angle at the current time, these
 *  variables are only updated by calculate(). */
static float sin_theta, cos_theta;

/* The atmospheric path length, this
 *  variable is only updated by calculate(). */
static float M_theta;

/* The atmospheric path length adjusted for atmospheric pressure, this
 *  variable is only updated by calculate(). */
static float Mprime_theta;

/* The atmospheric path length thru ozone, this
 *  variable is only updated by calculate(). */
static float Moz_theta;

/* The turbitity coefficient, this
 *  variable is only updated by calculate(). */
static coef_type beta;

/* Single-scattering albedo, this
 *  variable is only updated by calculate(). */
static float omega_a;

/* Direct sea-surface reflectance and diffuse
 *  sea-surface reflectance */
static coef_type ps, pd;

/* Forward scattering probability of aerosol. */
static coef_type Fa;

/* Ozone scale height. */
static float Hoz;

/* The coeficent of light not attenuated by cloud cover */
static coef_type cloud_coef;

/* Prototypes for helper functions */
static irr_type Edd (wavelength_type lambda);
static irr_type Eds (wavelength_type lambda);
static irr_type Fo (wavelength_type lambda);
static float Tr (wavelength_type lambda);
static float Ta (wavelength_type lambda);
static float Toz (wavelength_type lambda);
static float To (wavelength_type lambda);
static float Tw (wavelength_type lambda);
static float Ir (wavelength_type lambda);
static float Ia (wavelength_type lambda);
static float Taa (wavelength_type lambda);
static float Tas (wavelength_type lambda);
static float tau_a (wavelength_type lambda);
static void calculate_Fa (void);
static void calculate_ps_and_pd (void);
static void calculate_beta (void);
static void calculate_Hoz (void);
static void calculate_cloud_coef(void);
static void display_input_parameters (void);

/* Calulates the PAR.
 */
extern void calculate (void) {
   time_type t;
   wavelength_type lambda;
   FILE *par_file = NULL;
   FILE *sensor_file = NULL;
   FILE *total_par_file = NULL;
   FILE *zen_file = NULL;
   irr_type par_total;
   irr_type par_Edd;
   irr_type par_Eds;
   float Ed_lambda, Edd_lambda, Eds_lambda;
   float mu0, mu_sun, mu_sky;
   float daily_par;
   
   display_input_parameters();
   
   /* Open file to write PAR values to. */
   if (par_filename != NULL) {
      if ((par_file = fopen(par_filename, "w")) == NULL) {
         fprintf(stderr, "Could not open %s for writing: ", par_filename);
         perror(NULL);
         exit(1);
      }
   }
   
   /* Open file to write sensor values to (hemispherical) */
   if (sensor_filename != NULL){
      if ((sensor_file = fopen(sensor_filename, "w")) == NULL) {
         fprintf(stderr, "Could not open %s for writing: ", sensor_filename);
         perror(NULL);
         exit(1);
      }
   }
   
   /* Open file to write Total PAR values to. */
   if (total_par_filename != NULL) {
      if ((total_par_file = fopen(total_par_filename, "w")) == NULL) {
         fprintf(stderr, "Could not open %s for writing: ", total_par_filename);
         perror(NULL);
         exit(1);
      }
   }
   
   /* Open file to write solar zenith angle values to. */
   if (zen_filename != NULL) {
      if ((zen_file = fopen(zen_filename, "w")) == NULL) {
         fprintf(stderr, "Could not open %s for writing: ", zen_filename);
         perror(NULL);
         exit(1);
      }
   }
   
   /* Calculate coefficient due to cloud cover */
   calculate_cloud_coef();
   
   /* Calculate Single-Scattering Albedo */
   omega_a = (-0.0032*AM + 0.972) * exp(3.06E-4 * RH);
   
   /* Calculate the turbidity coefficient */
   calculate_beta();
   
   /* Calculate the ozone scale height */
   calculate_Hoz();
   
   /* For each time and wavelength, calculate a value of PAR */
   daily_par = 0.0;
   for (t = begin; t <= end; t += time_step) {
      par_total = 0.0;
      par_Edd = 0.0;
      par_Eds = 0.0;

      /* Calculate the solar zenith angle */
      theta_radians = get_theta(t);
      theta_degrees = 360.0 * theta_radians/(2*M_PI);
      
      /* Don't work anything out if the sun is below the horizon */
      if (theta_degrees >= 90.0) {
         continue;
      }
      
      /* First, recalculate a few global values. */
      sin_theta = sin(theta_radians);
      cos_theta = cos(theta_radians);
      M_theta = 1.0/(cos_theta + 0.15*pow(93.885 - theta_degrees, -1.253));
      Mprime_theta = M_theta * P/P0;
      Moz_theta = 1.0035/sqrt(cos_theta*cos_theta + 0.007);
      
      calculate_ps_and_pd();
      
      /*printf("M_theta=%f Mprime_theta=%f Moz_theta=%f\n", M_theta, Mprime_theta, Moz_theta);*/
      
      /* Write the solar zenith angle if required */
      if (zen_file != NULL) {
         fprintf(zen_file, "%2d:%02d\t%f\n", t/60, t%60, theta_degrees);
      }
      
      /* Recalculate a few more global values. */
      calculate_Fa();
      
      /* Then work out Ed and mu0 for each wavelength at the current time */
      mu_sky = 0.89;
      mu_sun = cos(asin(sin_theta/1.341));
      for (lambda = min_wavelength;
           lambda <= max_wavelength;
           lambda += wavelength_step) {
         
         Edd_lambda = Edd(lambda) * cloud_coef;
         Eds_lambda = Eds(lambda) * cloud_coef;
         Ed_lambda = Edd_lambda + Eds_lambda;
         
         mu0 = (mu_sun*Edd_lambda + mu_sky*Eds_lambda)/Ed_lambda;
         
         par_total += lambda * Ed_lambda * wavelength_step;
         par_Edd += lambda * Edd_lambda * wavelength_step;
         par_Eds += lambda * Eds_lambda * wavelength_step;
         
         /* Write the PAR values if required */
         if (par_file != NULL) {
            fprintf(par_file, "%2d:%02d\t%d\t%f\t%f\n", t/60, t%60,
               lambda, Ed_lambda, mu0);
         }
      }
      
      par_total *= (1.0E-9) * (1.0E6/avagadro) * 1/(h*c);
      par_Edd *= (1.0E-9) * (1.0E6/avagadro) * 1/(h*c);
      par_Eds *= (1.0E-9) * (1.0E6/avagadro) * 1/(h*c);
      
      if (sensor_file != NULL) {
         fprintf(sensor_file,"%2d:%02d\t%f\t%f\t%f\n", t/60, t%60,
            par_Edd, par_Eds, asin(sin_theta)); 
      }
         
      /* Print out the instanteous irradiance if flag set */
      if (total_par_file != NULL) {
         fprintf(total_par_file, "%2d:%02d\t%f\n", t/60, t%60, par_total);
      }
      
      daily_par += par_total;
   }
   
   printf("Daily PAR, in Em-2d-1: %f\n", daily_par*time_step*60./1.0e+06);
   
   if (par_file != NULL) {
      fclose(par_file);
   }

   if (sensor_file != NULL) {
      fclose(sensor_file);
   }
   
   if (total_par_file != NULL) {
      fclose(total_par_file);
   }
   
   if (zen_file != NULL) {
      fclose(zen_file);
   }
}

static irr_type Edd (wavelength_type lambda) {
   /*printf("%d Fo=%f cos_theta=%f Tr=%f Ta=%f Toz=%f To=%f Tw=%f pd=%f\n",
      lambda,
      Fo(lambda), cos_theta, Tr(lambda), Ta(lambda), Toz(lambda), 
      To(lambda), Tw(lambda), pd);*/
   return Fo(lambda) * cos_theta * Tr(lambda) * Ta(lambda) * Toz(lambda) * 
      To(lambda) * Tw(lambda) * (1.0-pd);
}

static irr_type Eds (wavelength_type lambda) {
   /*printf("%d Ir=%f Ia=%f ps=%f\n",
      lambda, Ir(lambda), Ia(lambda),ps);*/
   return (Ir(lambda) + Ia(lambda)) * (1.0-ps);
}

static irr_type Fo (wavelength_type lambda) {
   return get_h_o(lambda) * pow(1 + ecc*cos(2.0*M_PI*(D-3)/365.0), 2.0);
}

static float Tr (wavelength_type lambda) {
   return exp(-Mprime_theta/(115.6406*pow(lambda/1000.0,4.0) - 1.335*pow(lambda/1000,2.0)));
}

static float Ta (wavelength_type lambda) {
   return exp(-tau_a(lambda)*M_theta);
}

static float Toz (wavelength_type lambda) {
   return exp(-get_a_oz(lambda) * Hoz * Moz_theta);
}

static float To (wavelength_type lambda) {
   coef_type a_o = get_a_o(lambda);
   
   return
      exp(
         (-1.41*a_o*Mprime_theta)/
         pow(1.0 + 118.3*a_o*Mprime_theta,0.45));
}

static float Tw (wavelength_type lambda) {
   coef_type a_w = get_a_w(lambda);
   
   return
      exp(
         (-0.2385*a_w*WV*M_theta)/
         pow(1.0 + 20.07*a_w*WV*M_theta, 0.45));
}

static float Ir (wavelength_type lambda) {
   return Fo(lambda) * cos_theta * Toz(lambda) * To(lambda) * Tw(lambda)
      * Taa(lambda) * (1.0 - pow(Tr(lambda),0.95)) * 0.5;
}

static float Ia (wavelength_type lambda) {
   return Fo(lambda) * cos_theta * Toz(lambda) * To(lambda) * Tw(lambda)
      * Taa(lambda) * pow(Tr(lambda),1.5) * (1.0 - Tas(lambda)) * Fa;
}

static float Taa (wavelength_type lambda) {
   return exp(-(1-omega_a) * tau_a(lambda) * M_theta);
}

static float Tas (wavelength_type lambda) {
   return exp(-omega_a * tau_a(lambda) * M_theta);
}

static float tau_a (wavelength_type lambda) {
   return beta*pow(lambda/1000.0, -alpha);
}

/* Calculates forward scattering probability of aerosol (Fa) */
static void calculate_Fa (void) {
   float B1, B2, B3;
   float cos_theta_angle_brackets;
   
   if (alpha < 0.0) {
      cos_theta_angle_brackets = 0.82;
   } else if (alpha <= 1.2) {
      cos_theta_angle_brackets = -0.1417*alpha + 0.82;
   } else {
      cos_theta_angle_brackets = 0.65;
   }
   
   B3 = log(1.0 - cos_theta_angle_brackets);
   B2 = B3*(0.0783 + B3*(-0.3824 - 0.5874*B3));
   B1 = B3*(1.459 + B3*(0.1595 + 0.4129*B3));
   
   Fa = 1 - 0.5*exp((B1 + B2*cos_theta)*cos_theta);
}

/* Calculates pd and ps. Only reasonably accurate with zenith
 *  angles >= 40 degrees.
 */
static void calculate_ps_and_pd(void) {
   static const float pa = 1.2E3;
   static const float
      D1 = 2.2E-5,
      D2 = 4.0E-4,
      D3 = 4.5E-5,
      D4 = 4.0E-5;
   static const float nw = 1.341;   /* Index of refraction for sea water */
   
   coef_type pf, pdsp, pssp;
   coef_type Cd;
   float b = -7.14E-4 * W + 0.0618;
   
   /* Calculate coefficient of drag */
   if (W <= 7.0) {
      Cd = (0.62 + 1.56/W) * 1.0E-3;
   } else {
      Cd = (0.49 + 0.065*W) * 1.0E-3;
   }
   
   /* Calculate sea-foam reflectance */
   if (W <= 4.0) {
      pf = 0.0;
   } else if (W <= 7.0) {
      pf = D1 * pa * Cd * W*W - D2;
   } else {
      pf = (D3 * pa * Cd - D4) * W*W;
   }
   
   /* Calculate direct sea surface reflectance (pd) */
   if (W <= 2) {
      float theta_r_radians = asin(sin_theta/nw);
      float sin_num = sin(theta_radians - theta_r_radians);
      float sin_denom = sin(theta_radians + theta_r_radians);
      float tan_num = tan(theta_radians - theta_r_radians);
      float tan_denom = tan(theta_radians + theta_r_radians);
      pd = (1.0/2.0) * (
         (sin_num*sin_num)/(2*sin_denom*sin_denom) +
         (tan_num*tan_num)/(tan_denom*tan_denom));
   } else {
      pdsp = 0.0253*exp(b*(theta_degrees-40));
      pd = pdsp + pf;
   }
   
   /* Calculate diffuse sea surface reflectance (ps) */
   if (W <= 4) {
      pssp = 0.066;
   } else {
      pssp = 0.057;
   }
   ps = pssp + pf;
}

static void calculate_beta (void) {
   float Ca_550 = 3.91/V;
   float tau_a_550 = Ca_550*1.0;
   
   beta = tau_a_550/pow(0.55, -alpha);
}

static void calculate_Hoz (void) {
   Hoz = O_3/1000.0;
}

static void calculate_cloud_coef (void) {
/* Correction from zenith to elevation angle */
   float noon_elevation_angle = 90.0 - (360.0 * get_theta(720)/(2*M_PI));
   const float Fvis = 0.46;
   float delta = 0.632*C - 0.0019*noon_elevation_angle;
   
   cloud_coef = 1 -  (0.75*delta)/(1 - 0.25*Fvis);
   
   if (cloud_coef >= 0.95) {
      cloud_coef = 0.95;
   }
}

static void display_input_parameters (void) {
   printf("begin=\t%2d:%02d\n", begin/60, begin%60);
   printf("end=\t%2d:%02d\n", end/60, end%60);
   printf("time_step=\t%d mins\n", time_step);
   
   printf("min_wavelength=\t%d nm\n", min_wavelength);
   printf("max_wavelength=\t%d nm\n", max_wavelength);
   printf("wavelength_step=\t%d nm\n", wavelength_step);
   
   printf("AM=\t%g\n", AM);
   printf("RH=\t%g\n", RH);
   printf("alpha=\t%g\n", alpha);
   printf("WV=\t%g\n", WV);
   printf("P=\t%g\n", P);
   printf("W=\t%g\n", W);
   printf("WM=\t%g\n", WM);
   printf("D=\t%d\n", D);
   printf("V=\t%g\n", V);
   printf("O_3=\t%g\n", O_3);
   printf("C=\t%g\n", C);
   printf("lat=\t%g\n", lat);
   printf("lon=\t%g\n", lon);
}
