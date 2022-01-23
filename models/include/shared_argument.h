/* shared_argument.h
 * 
 * Interprets arguments from the command line.
 *
 * Latest modification: 01/06/20
 */

#ifndef _SHARED_ARGUMENT
#define _SHARED_ARGUMENT

#ifdef __cplusplus
extern "C" {
#endif /* __cplusplus */

/* Values returned by argument interpreting functions */
#define CONTINUE 0   /**< No error, ok to continue the program. */
#define QUIT 1       /**< No error, but stop the program. */
#define ERROR 2      /**< Error, stop the program. */

/* A few defines used as values for the parameters min_test and max_test
 *  in read_float(), read_int(), read_float_from(), read_int_from(),
 *  read_float_list() and read_int_list().
 */
#define NO_LIMIT     0     /**< Don't perform this test */
#define EQUAL        1     /**< Non-strict inequality */
#define INEQUAL      2     /**< Strict inequalisty */

/**
 * This should be given the command-line arguments before calling any other
 *  function from this file.
 * @param the_argc The number of arguments.
 * @param the_argv An array of strings, each a command line argument. The first
 *  argument in the array must be the name of the program as invoked from the
 *  command-line.
 */
extern void set_arguments (int the_argc, char **the_argv);

/**
 * Returns the next command-line argument.
 * @return The next command-line argument.
 */
extern char *next_arg (void);

/**
 * The name of the program as invoked from the command-line.
 */
extern char *argv0;

/**
 * Reads the next argument and interprets it as a float.
 * @param description The description of the argument that the floating point
 *  value is associated with.
 * @param dest Where to store the read float value.
 * @param min The minimum allowable value.
 * @param max The maximum allowable value.
 * @param min_test How to test the value against min. One of NO_LIMIT (the value
 *  is not checked against min), EQUAL (the value must be >= min) or INEQUAL
 *  (the value must be > min).
 * @param max_test How to test the value against max. One of NO_LIMIT (the value
 *  is not checked against max), EQUAL (the value must be <= max) or INEQUAL
 *  (the value must be < max).
 * @return CONTINUE if the value was read ok and was within the bounds set,
 *  or ERROR if there was no more arguments to read or the read value was
 *  outside the bounds set.
 */
extern int read_float (const char *description, float *dest,
   float min, float max, int min_test, int max_test);

/**
 * Reads the next argument and interprets it as an integer.
 * @param description The description of the argument that the interger value is
 *  associated with.
 * @param dest Where to store the read int value.
 * @param min The minimum allowable value.
 * @param max The maximum allowable value.
 * @param min_test How to test the value against min. One of NO_LIMIT (the value
 *  is not checked against min), EQUAL (the value must be >= min) or INEQUAL
 *  (the value must be > min).
 * @param max_test How to test the value against max. One of NO_LIMIT (the value
 *  is not checked against max), EQUAL (the value must be <= max) or INEQUAL
 *  (the value must be < max).
 * @return CONTINUE if the value was read ok and was within the bounds set,
 *  or ERROR if there was no more arguments to read or the read value was
 *  outside the bounds set.
 */
extern int read_int (const char *description, int *dest, int min, int max,
   int min_test, int max_test);

/**
 * Reads the string src and interprets it as a float.
 * @param description The description of the argument that the floating point
 *  value is associated with.
 * @param dest Where to store the read float value.
 * @param src The string to read the value from.
 * @param min The minimum allowable value.
 * @param max The maximum allowable value.
 * @param min_test How to test the value against min. One of NO_LIMIT (the value
 *  is not checked against min), EQUAL (the value must be >= min) or INEQUAL
 *  (the value must be > min).
 * @param max_test How to test the value against max. One of NO_LIMIT (the value
 *  is not checked against max), EQUAL (the value must be <= max) or INEQUAL
 *  (the value must be < max).
 * @return CONTINUE if the value was read ok and was within the bounds set,
 *  or ERROR if the read value was outside the bounds set.
 */
extern int read_float_from (const char *description, float *dest,
   const char *src, float min, float max, int min_test, int max_test);

/**
 * Reads the string src and interprets it as an integer.
 * @param description The description of the argument that the interger value is
 *  associated with.
 * @param dest Where to store the read int value.
 * @param src The string to read the value from.
 * @param min The minimum allowable value.
 * @param max The maximum allowable value.
 * @param min_test How to test the value against min. One of NO_LIMIT (the value
 *  is not checked against min), EQUAL (the value must be >= min) or INEQUAL
 *  (the value must be > min).
 * @param max_test How to test the value against max. One of NO_LIMIT (the value
 *  is not checked against max), EQUAL (the value must be <= max) or INEQUAL
 *  (the value must be < max).
 * @return CONTINUE if the value was read ok and was within the bounds set,
 *  or ERROR if the read value was outside the bounds set.
 */
extern int read_int_from (const char *description, int *dest, const char *src,
   int min, int max, int min_test, int max_test);

/**
 * Reads a comma-separated list of floating-point values from the argument list.
 * @param description The description of the argument that the float values are
 *  associated with.
 * @param dest Where to store a pointer to the the arary of read float values.
 *  This array should be deallocated with free() when no longer needed.
 * @param num A pointer to an integer that will be set to the number of values
 *  read (the size of the array that is returned in dest).
 * @param min The minimum allowable value.
 * @param max The maximum allowable value.
 * @param min_test How to test the values against min. One of NO_LIMIT (the
 *  value is not checked against min), EQUAL (the value must be >= min) or
 *  INEQUAL (the value must be > min).
 * @param max_test How to test the values against max. One of NO_LIMIT (the
 *  value is not checked against max), EQUAL (the value must be <= max) or
 *  INEQUAL (the value must be < max).
 * @return CONTINUE if the values were read ok and were all within the bounds
 *  set, or ERROR if any of the read values were outside the bounds set.
 */
extern int read_float_list (const char *description, float **dest, int *num,
   float min, float max, int min_test, int max_test);

/**
 * Reads a comma-separated list of integer values from the argument list.
 * @param description The description of the argument that the integer values
 *  are associated with.
 * @param dest Where to store a pointer to the the arary of read int values.
 *  This array should be deallocated with free() when no longer needed.
 * @param num A pointer to an integer that will be set to the number of values
 *  read (the size of the array that is returned in dest).
 * @param min The minimum allowable value.
 * @param max The maximum allowable value.
 * @param min_test How to test the values against min. One of NO_LIMIT (the
 *  value is not checked against min), EQUAL (the value must be >= min) or
 *  INEQUAL (the value must be > min).
 * @param max_test How to test the values against max. One of NO_LIMIT (the
 *  value is not checked against max), EQUAL (the value must be <= max) or
 *  INEQUAL (the value must be < max).
 * @return CONTINUE if the values were read ok and were all within the bounds
 *  set, or ERROR if any of the read values were outside the bounds set.
 */
extern int read_int_list (const char *description, int **dest, int *num,
   int min, int max, int min_test, int max_test);

#ifdef __cplusplus
}
#endif /* __cplusplus */
   
#endif /* #ifndef _SHARED_ARGUMENT */
