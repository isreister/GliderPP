/* morel91_model.h
 * 
 * Data structures that hold models of the various factors in
 *  a water column, whether read from file or generated. Includes
 *  inbuilt interpolation functions.
 *
 * Latest modification: 04/08/17 11:18:32
 */

#ifndef _MOREL91_MODEL
#define _MOREL91_MODEL

#include "Achl.hh"
#include "Aw.hh"
#include "Bw.hh"
#include "Beta.hh"
#include "Chl.hh"
#include "Ed.hh"
#include "K.hh"
#include "Ab.hh"
#include "Kc.hh"
#include "Kw.hh"
#include "St.hh"

#include "morel91_types.hh"

extern Achl achl;
extern Aw aw;
extern Bw bw;
extern Beta beta;
extern Chl chl;
extern Ed ed;
extern K k;
extern Ab ab;
extern Kc kc;
extern Kw kw;
extern St st;

#endif /* #ifndef _MOREL91_MODEL */
