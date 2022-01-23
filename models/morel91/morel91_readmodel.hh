/* morel91_readmodel.h
 * 
 *	Functions to read data from files.
 *
 * Latest modification: $Date: 2002-07-01 16:36:13 +0100 (Mon, 01 Jul 2002) $ 
 */

#ifndef _MOREL91_READMODEL
#define _MOREL91_READMODEL

#define FILE_OK 0
#define FILE_ERROR 1
#define FILE_FORMAT_ERROR 2

extern int read_ed (char *filename, float conversion_factor, int *begin, int *end);
extern int read_chl (char *filename, float conversion_factor);
extern int read_beta (char *filename, float conversion_factor);
extern int read_kc (char *filename, float conversion_factor);
extern int read_kw (char *filename, float conversion_factor);
extern int read_k (char *filename, float conversion_factor);
extern int read_aw (char *filename, float conversion_factor);
extern int read_bw (char *filename, float conversion_factor);
extern int read_Achl (char *filename, float conversion_factor);

#endif /* #ifndef _MOREL91_READMODEL */
