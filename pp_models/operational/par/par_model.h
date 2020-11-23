/* par_model.h
 * 
 * Data structures that hold models of the various factors in
 *  the atmosphere. Includes inbuilt interpolation functions.
 *
 * Latest modification: 02/07/01 16:21:00
 */

#ifndef _PAR_MODEL
#define _PAR_MODEL

#include "par_types.h"

/* Function to clear data and ready the models for data. This must be called
 *  before any calls to add_???_data or get_???_data.
 */
extern void clear_data (void);

/* Functions to add stored data - data for current time will not be
 *  re-interpolated unless set_time is called again.
 */
extern void add_h_o_data(wavelength_type wavelength, float value);
extern void add_a_oz_data(wavelength_type wavelength, float value);
extern void add_a_o_data(wavelength_type wavelength, float value);
extern void add_a_w_data(wavelength_type wavelength, float value);
extern void add_theta_data(time_type t, float value);

/* Functions to retrieve interpolated data.
 */
extern irr_type get_h_o(wavelength_type wavelength);
extern coef_type get_a_oz(wavelength_type wavelength);
extern coef_type get_a_o(wavelength_type wavelength);
extern coef_type get_a_w(wavelength_type wavelength);
extern radians_type get_theta (time_type t);

/* Functions to print data out if needed. Likely only to be used for debugging. */
extern void print_h_o_data (void);
extern void print_a_oz_data (void);
extern void print_a_o_data (void);
extern void print_a_w_data (void);
extern void print_theta_data (void);

#endif /* #ifndef _PAR_MODEL */
