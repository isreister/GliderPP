#include <math.h>
#include <stdio.h>

/*  Function:  sunang.c */
/*  Author:    Tim Smyth */
/*  Version:   1.0*/
/*  Date:      98/05/12 */

/*  Description: */ 
/*   Computes sun azimuth and zenith angles for a given */
/*   time, date, latitude and longitude.  This program */
/*   is from the NMFS ELAS computer code.  Modified for */
/*   standard coordinates (W long. negative), to correct */
/*   for dateline problem, and to correct coefficients (taken */
/*   from Iqbal, 1983, An Introduction to Solar Radiation). */
/*   Watson Gregg, Research and Data Systems, Corp. */


/*  Parameters: */
/*    iday = julian day */
/*    time = time of day in seconds */
/*    ylat = latitude of pixel */
/*    xlon = longitude of pixel */
/*    sunz = solar zenith in degrees */
/*    sdec = solar declination angle in degrees */
/*    thez = theta zero orbital position in degrees */
/*    tc = time correction */
/*    xha = solar hour angle in degrees */

/*  Inputs: julian day, hour, latitude and logitude */

/*  Outputs: solar zenith and azimuth angle */

void sunang(int iday, float hr, float xlon, float ylat, 
             float *radsunz, float *radsuna) 

{
   double   pi, rad;
   float    thez, rthez, sdec, rsdec, tc, xha,
            rlat, rlon, rha, costmp, rsunz, 
            rsuna, sintmp, eps, suna, sunz;
   
/* Compute solar declination angle */
   pi = 2. * asin(1.);
   rad = 180/pi;

   thez = 360.0*(iday-1)/365.0;
   rthez = thez/rad;
   sdec = 0.396372-22.91327*cos(rthez) + 4.02543*sin(rthez)
        - 0.387205*cos(2.0*rthez) + 0.051967*sin(2.0*rthez)
        - 0.154527*cos(3.0*rthez) + 0.084798*sin(3.0*rthez);
   rsdec = sdec/rad;

/* Time correction for solar hour angle, and solar hour angle */
   tc = 0.004297 + 0.107029*cos(rthez) - 1.837877*sin(rthez)
      - 0.837378*cos(2.0*rthez) - 2.342824*sin(2.0*rthez);
   xha = (hr-12.0)*15.0 + xlon + tc;

   if (xha > 180.0)
      xha = xha - 360.0;
   if (xha < -180.0)
      xha = xha + 360.0;

   rlat = ylat/rad;
   rlon = xlon/rad;
   rha = xha/rad;

/* Sun zenith */
   costmp = sin(rlat)*sin(rsdec) +
            cos(rlat)*cos(rsdec)*cos(rha);
   eps = fabs(costmp);

   if (eps > 1.1)
      printf("Error in acos argument in sun zenith\n %f\n", costmp);
   else if (eps > 1.0){
      if (costmp > 0.0)
         costmp = 1.0;
      if (costmp < 0.0)
         costmp = -1.0;
      }

   rsunz = acos(costmp);
/* Sun azimuth */
   sintmp = sin(fabs(rha))*cos(rsdec)/sin(rsunz);
   rsuna = asin(sintmp);
 
   if(ylat > sdec) 
      rsuna = 180.0 / rad - rsuna;
   if(xha >  0.) 
      rsuna = 360.0/rad - rsuna;

/* Convert to degrees */
   suna = rsuna * rad;
   sunz = rsunz*rad;

   *radsunz = rsunz;
   *radsuna = rsuna;
 }

