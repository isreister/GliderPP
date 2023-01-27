/* morel91.c
 * 
 *   High level functions of pp, including main.
 *
 * Latest modification: 02/09/04 13:05:20
 */

#include <stdio.h>

#include "morel91_argument.hh"
#include "morel91_calculate.hh"
#include "morel91_model.hh"

int main (int argc, char *argv[]) {
   int val;
   
   set_arguments(argc, argv);
   
   /* Interpret command line parameters */
   val = interpret_arguments();
   switch (val) {
      case CONTINUE:
      /* Parameters okay - continue running */
      break;
      
      case QUIT:
      /* Parameters okay - but require non error-code exit */
      return 0;
      break;
      
      case ERROR:
      /* Parameters are in error - error-code exit */
      return 1;
      break;
   }
   
   /* Calculate Prime Production */
   printf("Calculated prime production is %f\n", calculate());
   
   /* Release memory and tidy up is set as an atexit function, handled
    *  automatically. */
   
   /* Exit successfully */
   return 0;
}
