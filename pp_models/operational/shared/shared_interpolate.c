/* shared_interpolate.c
 * 
 *	General-purpose interpolation functions.
 *
 * Latest modification: 00/10/26
 */

#include <math.h>

#include "shared_interpolate.h"

typedef struct vector_struct {
	float x,y,z;
} vector;

static vector i = {1.0, 0.0, 0.0};
static vector j = {0.0, 1.0, 0.0};
static vector k = {0.0, 0.0, 1.0};

static float dot (vector *a, vector *b) {
	return a->x*b->x + a->y*b->y + a->z*b->z;
}

static void cross (vector *a, vector *b, vector *c) {
	c->x = a->y*b->z - a->z*b->y;
	c->y = a->z*b->x - a->x*b->z;
	c->z = a->x*b->y - a->y*b->x;
}

static void add (vector *a, vector *b, vector *c) {
	c->x = a->x + b->x;
	c->y = a->y + b->y;
	c->z = a->z + b->z;
}

static void sub (vector *a, vector *b, vector *c) {
	c->x = a->x - b->x;
	c->y = a->y - b->y;
	c->z = a->z - b->z;
}

static void invert (vector *a) {
	a->x = -(a->x);
	a->y = -(a->y);
	a->z = -(a->z);
}

static float length (vector *a) {
	return sqrt(a->x*a->x + a->y*a->y + a->z*a->z);
}

/* Simple bilinear interpolation */
float interpolate_1 (
	float x,
	float x1, float y1,
	float x2, float y2) {
	
	float dx = x2-x1;
	float dy = y2-y1;
	return (x-x1)*(dy/dx) + y1;
}

/* Interpolation of a value on a 2 dimensional value field. The
 *  position (x,y) is the point for which the z value is required.
 *  The maths used in this function is based on vector geometry.
 */
float interpolate_2 (
	float x, float y,
	float x1, float y1, float z1,
	float x2, float y2, float z2,
	float x3, float y3, float z3) {
	
	/* The vectors are defined as static to speed up this
	 *  function. It is therefore not multi-task safe.
	 */
	static vector a,b,c,d,e,e_dash,f,n;
	
	/* The formula can't cope with interpolating a point equal to a,
	 *  but the result is always the z component of a.
	 */
	if (x == x1 && y == y1) {
		return z1;
	}
	
	a.x = x1; a.y = y1; a.z = z1;
	b.x = x2; b.y = y2; b.z = z2;
	c.x = x3; c.y = y3; c.z = z3;
	d.x = x-a.x;  d.y = y-a.y;  d.z = 0.0;
	
	/* let b := b - a */
	sub(&b,&a,&b);
	/* let c := c - a */
	sub(&c,&a,&c);
	/* let n := b ^ c */
	cross(&b,&c,&n);
	
	/* Check if b and c are colinear (ie. length of n is zero) */
	if (n.x == 0.0 && n.y == 0.0 && n.z == 0.0) {
		/* Use a guess value for n, that is perpendicular to b */
		vector tmp;
		cross(&b, &k, &tmp);
		cross(&b, &tmp, &n);
	}
	
	/* Ensure that n.z is +ve */
	if (n.z < 0) invert(&n);
	
	/* let f := d ^ k */
	cross(&d,&k,&f);
	/* let e := n ^ f */
	cross(&n,&f,&e);
	/* let e_dash be the projection of e on the xy plane */
	e_dash = e;
	e_dash.z = 0.0;
	
	return (length(&d)/length(&e_dash)) * dot(&e,&k) + dot(&a,&k);
}
