/* par_readmodel.h
 * 
 * Functions to read data from files.
 *
 * Latest modification: 02/07/01 16:21:01
 */

#ifndef _PAR_READMODEL
#define _PAR_READMODEL

#define FILE_OK 0
#define FILE_ERROR 1
#define FILE_FORMAT_ERROR 2

extern int read_atmo (char *filename, float h_o_conversion,
   float a_oz_conversion, float a_o_conversion, float a_w_conversion);
extern int read_theta (char *filename, float theta_conversion);

#endif /* #ifndef _PAR_READMODEL */
