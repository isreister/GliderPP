/* morel91_model.c
 * 
 *   Data structures that hold models of the various factors in
 *  a water column, whether read from file or generated. Includes
 *  inbuilt interpolation functions.
 *
 * Latest modification: 04/08/17 11:18:32
 */

#include <stdio.h>
#include <stdlib.h>

#include "shared_list.h"
#include "shared_tree.h"

#include "morel91_defs.hh"
#include "morel91_model.hh"
#include "morel91_types.hh"

/* Stored data */
Achl achl;
Aw aw;
Bw bw;
Beta beta(0.01);
Chl chl;
Ed ed;
Kc kc;
Kw kw;
K k;
Ab ab;
St st(T_DEFAULT);
