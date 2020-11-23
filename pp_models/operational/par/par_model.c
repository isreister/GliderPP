/* par_model.c
 * 
 * Data structures that hold models of the various factors in
 *  the atmosphere. Includes inbuilt interpolation functions.
 *
 * Latest modification: 02/07/01 16:21:00
 */

#include <stdio.h>
#include <stdlib.h>

#include "sunang.h"
#include "shared_list.h"
#include "shared_tree.h"

#include "par_argument.h"
#include "par_defs.h"
#include "par_model.h"
#include "par_types.h"

/* Stored data
 */
static node *h_o;
static node *a_oz;
static node *a_o;
static node *a_w;
static node *theta;

/* Function to clear data and ready the models for data. This must be called
 *  before any calls to add_???_data, get_???_data or.
 */
void clear_data (void) {
   static int initialised = FALSE;
   
   /* If the stored data has been previously initialised, then
    *  any non-NULL values indicate memory that must be freed.
    */
   if (initialised) {
      if (h_o != NULL) delete_list(h_o);
      if (a_oz != NULL) delete_list(a_oz);
      if (a_o != NULL) delete_list(a_o);
      if (a_w != NULL) delete_list(a_w);
      if (theta != NULL) delete_list(theta);
   } else {
      /* Not strictly nessecary but register the data to be deleted on exit. */
      atexit(&clear_data);
      initialised = TRUE;
   }
   
   h_o = NULL;
   a_oz = NULL;
   a_o = NULL;
   a_w = NULL;
   theta = NULL;
}

/* Functions to add stored data - data for current time will not be
 *  re-interpolated unless set_time is called again.
 */
void add_h_o_data(wavelength_type wavelength, float value) {
   h_o = add_list_value(h_o, wavelength, value);
}

void add_a_oz_data(wavelength_type wavelength, float value) {
   a_oz = add_list_value(a_oz, wavelength, value);
}

void add_a_o_data(wavelength_type wavelength, float value) {
   a_o = add_list_value(a_o, wavelength, value);
}

void add_a_w_data(wavelength_type wavelength, float value) {
   a_w = add_list_value(a_w, wavelength, value);
}

void add_theta_data(time_type t, float value) {
   theta = add_list_value(theta, t, value);
}

/* Functions to retrieve interpolated data for a wavelength.
 */
irr_type get_h_o (wavelength_type wavelength) {
   irr_type tmp = interpolate_using_list(h_o, wavelength, H_O_DEFAULT);
   
   if (tmp < H_O_MINIMUM)
      return H_O_MINIMUM;
   else if (tmp > H_O_MAXIMUM)
      return H_O_MAXIMUM;
   else
      return tmp;
}

coef_type get_a_oz (wavelength_type wavelength) {
   coef_type tmp = interpolate_using_list(a_oz, wavelength, A_OZ_DEFAULT);
   
   if (tmp < A_OZ_MINIMUM)
      return A_OZ_MINIMUM;
   else if (tmp > A_OZ_MAXIMUM)
      return A_OZ_MAXIMUM;
   else
      return tmp;
}

coef_type get_a_o (wavelength_type wavelength) {
   coef_type tmp = interpolate_using_list(a_o, wavelength, A_O_DEFAULT);
   
   if (tmp < A_O_MINIMUM)
      return A_O_MINIMUM;
   else if (tmp > A_O_MAXIMUM)
      return A_O_MAXIMUM;
   else
      return tmp;
}

coef_type get_a_w (wavelength_type wavelength) {
   coef_type tmp = interpolate_using_list(a_w, wavelength, A_W_DEFAULT);
   
   if (tmp < A_W_MINIMUM)
      return A_W_MINIMUM;
   else if (tmp > A_W_MAXIMUM)
      return A_W_MAXIMUM;
   else
      return tmp;
}

radians_type get_theta (time_type t) {
   radians_type tmp;
   float hour = t/60 + (t%60)/60.0;
   float sun_azi, sun_zen;
   
   sunang(D, hour, lon, lat, 
          &sun_zen, &sun_azi);
   
   tmp = interpolate_using_list(theta, t, sun_zen);
   
   if (tmp < 0.0)
      return 0.0;
   else if (tmp > M_PI)
      return M_PI;
   else
      return tmp;
   
   return sun_zen;
}

/* Functions to print data out if needed. Likely only to be used for debugging. */
void print_h_o_data (void) {
   print_list(h_o);
}

void print_a_oz_data (void) {
   print_list(a_oz);
}

void print_a_o_data (void) {
   print_list(a_o);
}

void print_a_w_data (void) {
   print_list(a_w);
}

void print_theta_data (void) {
   print_list(theta);
}
