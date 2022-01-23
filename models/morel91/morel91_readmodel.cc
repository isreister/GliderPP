/* morel91_readmodel.c
 * 
 *   Functions to read data from files.
 *
 * Latest modification: $Date: 2002-07-01 16:36:13 +0100 (Mon, 01 Jul 2002) $ 
 */

#include <stdio.h>

#include "morel91_defs.h"
#include "morel91_model.h"
#include "morel91_readmodel.h"

int read_ed (char *filename, float conversion_factor, int *begin, int *end) {
   
   FILE *in;
   time_type time;
        wavelength_type wavelength;
   int minutes, hours;
   int fields_read;
   irr_type ed;
   float mu0;
   
   /* Open file and check for error */
   in = fopen(filename, "r");
   if (in == NULL) {
      return FILE_ERROR;
   }
   
   /* Read fields until EOF */
   while (!feof(in)) {
      fields_read = fscanf(in, " %d:%d %d %f %f ",
         &hours, &minutes, &wavelength, &ed, &mu0);
      
      if (fields_read <= 0) {
         continue;
      } else if (fields_read != 5) {
         fclose(in);
         return FILE_FORMAT_ERROR;
      }
      
      time = minutes + hours * 60;
      
      if (*begin == UNDEFINED || time < *begin) {
         *begin = time;
      }
      
      if (*end == UNDEFINED || time > *end) {
         *end = time;
      }
      
      add_ed_data(time, wavelength, ed*conversion_factor);
      add_mu0_data(time, wavelength, mu0);
   }
   
   fclose(in);
   return FILE_OK;
}

int read_chl (char *filename, float conversion_factor) {
   FILE *in;
   time_type time;
   chl_type chl;
   depth_type depth;
   int fields_read;
   int minutes, hours;
   
   /* Open file and check for error */
   in = fopen(filename, "r");
   if (in == NULL) {
      return FILE_ERROR;
   }
   
   /* Read fields until EOF */
   while (!feof(in)) {
      fields_read = fscanf(in, " %d:%d %d %f\n", &hours, &minutes, &depth, &chl);
      if (fields_read <= 0) {
         continue;
      } else if (fields_read != 4) {
         fclose(in);
         return FILE_FORMAT_ERROR;
      }
      time = minutes + hours*60;
      add_chl_data(time, depth, chl*conversion_factor);
   }
   
   fclose(in);
   return FILE_OK;
}

int read_beta (char *filename, float conversion_factor) {
   FILE *in;
   time_type time;
   beta_type beta;
   depth_type depth;
   int fields_read;
   int minutes, hours;
   
   /* Open file and check for error */
   in = fopen(filename, "r");
   if (in == NULL) {
      return FILE_ERROR;
   }
   
   /* Read fields until EOF */
   while (!feof(in)) {
      fields_read = fscanf(in, " %d:%d %d %f\n", &hours, &minutes, &depth, &beta);
      if (fields_read <= 0) {
         continue;
      } else if (fields_read != 4) {
         fclose(in);
         return FILE_FORMAT_ERROR;
      }
      time = minutes + hours*60;
      add_beta_data(time, depth, beta*conversion_factor);
   }
   
   fclose(in);
   return FILE_OK;
}

int read_kc (char *filename, float conversion_factor) {
   FILE *in;
   wavelength_type wavelength;
   k_type kc;
   chl_type chl;
   int fields_read;
   
   /* Open file and check for error */
   in = fopen(filename, "r");
   if (in == NULL) {
      return FILE_ERROR;
   }
   
   /* Read fields until EOF */
   while (!feof(in)) {
      fields_read = fscanf(in, " %d %f %f\n", &wavelength, &chl, &kc);
      if (fields_read <= 0) {
         continue;
      } else if (fields_read != 3) {
         fclose(in);
         return FILE_FORMAT_ERROR;
      }
      add_kc_data(wavelength, chl, kc*conversion_factor);
   }
   
   fclose(in);
   return FILE_OK;
}

int read_kw (char *filename, float conversion_factor) {
   FILE *in;
   wavelength_type wavelength;
   k_type kw;
   int fields_read;
   
   /* Open file and check for error */
   in = fopen(filename, "r");
   if (in == NULL) {
      return FILE_ERROR;
   }
   
   /* Read fields until EOF */
   while (!feof(in)) {
      fields_read = fscanf(in, " %d %f\n", &wavelength, &kw);
      if (fields_read <= 0) {
         continue;
      } else if (fields_read != 2) {
         fclose(in);
         return FILE_FORMAT_ERROR;
      }
      add_kw_data(wavelength, kw*conversion_factor);
   }
   
   fclose(in);
   return FILE_OK;
}

int read_k (char *filename, float conversion_factor) {
   FILE *in;
   depth_type depth;
   wavelength_type wavelength;
   k_type k;
   int fields_read;
   
   /* Open file and check for error */
   in = fopen(filename, "r");
   if (in == NULL) {
      return FILE_ERROR;
   }
   
   /* Read fields until EOF */
   while (!feof(in)) {
      fields_read = fscanf(in, " %d %d %f ", &depth, &wavelength, &k);
      if (fields_read != 3) {
         fclose(in);
         return FILE_FORMAT_ERROR;
      }
      add_k_data(depth, wavelength, k*conversion_factor);
   }
   
   fclose(in);
   return FILE_OK;
}

int read_aw (char *filename, float conversion_factor) {
   FILE *in;
   wavelength_type wavelength;
   aw_type aw;
   int fields_read;
   
   /* Open file and check for error */
   in = fopen(filename, "r");
   if (in == NULL) {
      return FILE_ERROR;
   }
   
   /* Read fields until EOF */
   while (!feof(in)) {
      fields_read = fscanf(in, " %d %f\n", &wavelength, &aw);
      if (fields_read <= 0) {
         continue;
      } else if (fields_read != 2) {
         fclose(in);
         return FILE_FORMAT_ERROR;
      }
      add_aw_data(wavelength, aw*conversion_factor);
   }
   
   fclose(in);
   return FILE_OK;
}

int read_bw (char *filename, float conversion_factor) {
   FILE *in;
   wavelength_type wavelength;
   bw_type bw;
   int fields_read;
   
   /* Open file and check for error */
   in = fopen(filename, "r");
   if (in == NULL) {
      return FILE_ERROR;
   }
   
   /* Read fields until EOF */
   while (!feof(in)) {
      fields_read = fscanf(in, " %d %f\n", &wavelength, &bw);
      if (fields_read <= 0) {
         continue;
      } else if (fields_read != 2) {
         fclose(in);
         return FILE_FORMAT_ERROR;
      }
      add_bw_data(wavelength, bw*conversion_factor);
   }
   
   fclose(in);
   return FILE_OK;
}

int read_Achl (char *filename, float conversion_factor) {
   FILE *in;
   wavelength_type wavelength;
   Achl_type Achl;
   int fields_read;
   
   /* Open file and check for error */
   in = fopen(filename, "r");
   if (in == NULL) {
      return FILE_ERROR;
   }
   
   /* Read fields until EOF */
   while (!feof(in)) {
      fields_read = fscanf(in, " %d %f\n", &wavelength, &Achl);
      if (fields_read <= 0) {
         continue;
      } else if (fields_read != 2) {
         fclose(in);
         return FILE_FORMAT_ERROR;
      }
      add_Achl_data(wavelength, Achl*conversion_factor);
   }
   
   fclose(in);
   return FILE_OK;
}
