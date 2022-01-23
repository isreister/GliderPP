/* shared_interpolate.h
 * 
 *  General-purpose interpolation functions.
 *
 * Latest modification: 00/10/26
 */

#ifndef _PP_INTERPOLATE
#define _PP_INTERPOLATE

#ifdef __cplusplus
extern "C" {
#endif /* __cplusplus */

/**
 * Simple linear interpolation.
 * @param x The x position of the point to calculate the value at.
 * @param x1 The x position of the first known data value.
 * @param y1 The value of the first known data value.
 * @param x2 The x position of the second known data value.
 * @param y2 The value of the second known data value.
 * @return The interpolated value at x.
 */
float interpolate_1 (
   float x,
   float x1, float y1,
   float x2, float y2);

/**
 * Interpolation of a value on a 2 dimensional value field.
 * @param x The x position of the point to calculate the value at.
 * @param y The y position of the point to calculate the value at.
 * @param x1 The x position of the first known data value.
 * @param y1 The y position of the first known data value.
 * @param z1 The value of the first known data value.
 * @param x2 The x position of the second known data value.
 * @param y2 The y position of the second known data value.
 * @param z2 The value of the second known data value.
 * @param x3 The x position of the third known data value.
 * @param y3 The y position of the third known data value.
 * @param z3 The value of the third known data value.
 * @return The interpolated value at (x,y).
 */
float interpolate_2 (
   float x, float y,
   float x1, float y1, float z1,
   float x2, float y2, float z2,
   float x3, float y3, float z3);

#ifdef __cplusplus
}
#endif /* __cplusplus */

#endif /* #ifndef _PP_INTERPOLATE */
