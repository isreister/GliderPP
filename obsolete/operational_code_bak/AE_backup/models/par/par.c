/* par.c
 * 
 *	High level functions of par, including main.
 *
 * Latest modification: 02/07/01 16:20:59
 */

#include <stdio.h>
#include <stdlib.h>

#include "par_argument.h"
#include "par_calculate.h"
#include "par_model.h"

int main (int argc, char *argv[]) {
	int val;
	
	clear_data();
	
	set_arguments(argc, argv);
	
	/* Interpret command line parameters */
	val = interpret_arguments();
	switch (val) {
		case CONTINUE:
		/* Parameters okay - continue running */
		break;
		
		case QUIT:
		/* Parameters okay - but require non error-code exit */
		exit(0);
		break;
		
		case ERROR:
		/* Parameters are in error - error-code exit */
		exit(-1);
		break;
	}
	
	/* Calculate PAR and write to disk */
	calculate();
	
	/* Release memory and tidy up is set as an atexit function, handled
	 *  automatically. */
	
	/* Exit successfully */
	exit(0);
}
