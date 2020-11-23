/* par_readmodel.c
 * 
 * Functions to read data from files.
 *
 * Latest modification: 02/07/01 16:21:00
 */

#include <stdio.h>

#include "par_defs.h"
#include "par_model.h"
#include "par_readmodel.h"

int read_atmo (char *filename, float h_o_conversion, float a_oz_conversion,
               float a_o_conversion, float a_w_conversion) {
   
   FILE *in;
   wavelength_type wavelength;
   float h_o, a_oz, a_o, a_w;
   int fields_read;
   
   /* Open file and check for error */
   in = fopen(filename, "r");
   if (in == NULL) {
      return FILE_ERROR;
   }
   
   /* Read fields until EOF */
   while (!feof(in)) {
      fields_read = fscanf(in, " %d %f %f %f %f ",
         &wavelength, &h_o, &a_oz, &a_o, &a_w);
      
      if (fields_read < 5) {
         fclose(in);
         return FILE_FORMAT_ERROR;
      }
      add_h_o_data(wavelength, h_o * h_o_conversion);
      add_a_oz_data(wavelength, a_oz * a_oz_conversion);
      add_a_o_data(wavelength, a_o * a_o_conversion);
      add_a_w_data(wavelength, a_w * a_w_conversion);
   }
   
   fclose(in);
   return FILE_OK;
}

int read_theta (char *filename, float theta_conversion) {
   
   FILE *in;
   degrees_type theta_degrees;
   radians_type theta_radians;
   int hours, minutes;
   int fields_read;
   
   /* Open file and check for error */
   in = fopen(filename, "r");
   if (in == NULL) {
      return FILE_ERROR;
   }
   
   /* Read fields until EOF */
   while (!feof(in)) {
      fields_read = fscanf(in, " %d:%d %f ",
         &hours, &minutes, &theta_degrees);
      
      theta_radians = theta_degrees * theta_conversion * 2.0 * M_PI / 360.0;
      
      if (fields_read < 3) {
         fclose(in);
         return FILE_FORMAT_ERROR;
      }
      add_theta_data(hours*60 + minutes, theta_radians);
   }
   
   fclose(in);
   return FILE_OK;
}
