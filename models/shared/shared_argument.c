/* shared_argument.c
 * 
 * Interprets arguments from the command line.
 *
 * Latest modification: 01/06/20
 */

#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#include "shared_argument.h"

/* Arguments from main */
static int argc;
static char **argv;
static int cur_index = 1;

char *argv0;

void set_arguments (int the_argc, char **the_argv) {
   argc = the_argc;
   argv = the_argv;
   argv0 = argv[0];
}

char *next_arg (void) {
   if (cur_index < argc) {
      return argv[cur_index++];
   } else {
      return NULL;
   }
}

int read_float (const char *description, float *dest, float min, float max,
   int min_test, int max_test) {
   
   return read_float_from(description, dest, next_arg(), min, max,
      min_test, max_test);
}

int read_int (const char *description, int *dest, int min, int max,
   int min_test, int max_test) {
   
   return read_int_from(description, dest, next_arg(), min, max,
      min_test, max_test);
}

extern int read_float_from (const char *description, float *dest,
   const char *src, float min, float max, int min_test, int max_test) {
   
   int min_okay, max_okay;    /* Which limit conditions have been met */
   float v;
   char *endptr;
   
   if (src != NULL) {
      v = strtod(src,&endptr);
      
      /* Is v in the correct range? */
      min_okay =
         /* No minimum value */
         (min_test == NO_LIMIT) ||
         /* Minimum is inclusive of the range */
         (min_test == EQUAL && v >= min) ||
         /* Minimum is exclusive of the range */
         (min_test == INEQUAL && v > min);
      
      /* Is v in the correct range? */
      max_okay =
         /* No maxnimum value */
         (max_test == NO_LIMIT) ||
         /* Maximum is inclusive of the range */
         (max_test == EQUAL && v <= max) ||
         /* Maximum is exclusive of the range */
         (max_test == INEQUAL && v < max);

      if (min_okay && max_okay) {
         *dest = v;
         return CONTINUE;
      }
   }
   
   /* Print out an error message stating the required range of the value */
   fprintf(stderr, "%s: please supply a number ", argv[0]);
   switch (min_test) {
      case NO_LIMIT:
      break;
      
      case EQUAL:
      fprintf(stderr, ">= %f ", min);
      break;
      
      case INEQUAL:
      fprintf(stderr, "> %f ", min);
      break;
   }
   
   if (min_test != NO_LIMIT && max_test != NO_LIMIT) {
      fprintf(stderr, "and ");
   }
   
   switch (max_test) {
      case NO_LIMIT:
      break;
      
      case EQUAL:
      fprintf(stderr, "<= %f ", max);
      break;
      
      case INEQUAL:
      fprintf(stderr, "< %f ", max);
      break;
   }
   
   fprintf(stderr, "for --%s\n", description);
   
   return ERROR;
}

extern int read_int_from (const char *description, int *dest, const char *src,
   int min, int max, int min_test, int max_test) {
   
   int min_okay, max_okay;    /* Which limit conditions have been met */
   int v;
   char *endptr;
   
   if (src != NULL) {
      v = strtol(src, &endptr, 10);
      
      /* Is v in the correct range? */
      min_okay =
         /* No minimum value */
         (min_test == NO_LIMIT) ||
         /* Minimum is inclusive of the range */
         (min_test == EQUAL && v >= min) ||
         /* Minimum is exclusive of the range */
         (min_test == INEQUAL && v > min);

      /* Is v in the correct range? */
      max_okay =
         /* No maximum value */
         (max_test == NO_LIMIT) ||
         /* Maximum is inclusive of the range */
         (max_test == EQUAL && v <= max) ||
         /* Maximum is exclusive of the range */
         (max_test == INEQUAL && v < max);

      if (min_okay && max_okay) {
         *dest = v;
         return CONTINUE;
      }
   }
   
   /* Print out an error message stating the required range of the value */
   fprintf(stderr, "%s: please supply a number ", argv[0]);
   switch (min_test) {
      case NO_LIMIT:
      break;
      
      case EQUAL:
      fprintf(stderr, ">= %d ", min);
      break;
      
      case INEQUAL:
      fprintf(stderr, "> %d ", min);
      break;
   }
   
   if (min_test != NO_LIMIT && max_test != NO_LIMIT) {
      fprintf(stderr, "and ");
   }
   
   switch (max_test) {
      case NO_LIMIT:
      break;
      
      case EQUAL:
      fprintf(stderr, "<= %d ", max);
      break;
      
      case INEQUAL:
      fprintf(stderr, "< %d ", max);
      break;
   }
   
   fprintf(stderr, "for --%s\n", description);
   
   return ERROR;
}

int read_int_list (const char *description, int **dest, int *num,
   int min, int max, int min_test, int max_test) {
   
   int num_values = 0;
   int i;
   char *arg = next_arg();
   char *ptr = arg;
   int *array;
   
   /* Count up how many numbers there should be ((num of commas) + 1). */
   while (ptr != NULL) {
      num_values++;
      ptr = strchr(ptr+1, ',');
   }
   
   /* Allocate an array to hold the numbers. */
   array = malloc(num_values*sizeof(int));
   
   /* Read each number into the array. */
   ptr = arg;
   for (i = 0; i < num_values; i++) {
      int retval = read_int_from(description, array+i, ptr, min, max,
         min_test, max_test);
      /* If there was an error, free the array and return the error. */
      if (retval != CONTINUE) {
         free(array);
         return retval;
      }
      ptr = strchr(ptr+1, ',')+1;
   }
   
   *num = num_values;
   *dest = array;
   return CONTINUE;
}

int read_float_list (const char *description, float **dest, int *num,
   float min, float max, int min_test, int max_test) {
   
   int num_values = 0;
   int i;
   char *arg = next_arg();
   char *ptr = arg;
   float *array;
   
   /* Count up how many numbers there should be ((num of commas) + 1). */
   while (ptr != NULL) {
      num_values++;
      ptr = strchr(ptr+1, ',');
   }
   
   /* Allocate an array to hold the numbers. */
   array = malloc(num_values*sizeof(float));
   
   /* Read each number into the array. */
   ptr = arg;
   for (i = 0; i < num_values; i++) {
      int retval = read_float_from(description, array+i, ptr, min, max,
         min_test, max_test);
      /* If there was an error, free the array and return the error. */
      if (retval != CONTINUE) {
         free(array);
         return retval;
      }
      ptr = strchr(ptr+1, ',')+1;
   }
   
   *num = num_values;
   *dest = array;
   return CONTINUE;
}
