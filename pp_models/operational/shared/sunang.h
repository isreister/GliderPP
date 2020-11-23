#ifdef __cplusplus
extern "C" {
#endif /* __cplusplus */

/**
 * Calculates the solar zenith and azimuth angles based upon a time, day and
 *  position on the Earth's surface.
 * @param iday The day of the year (0-365).
 * @param hr The hour of the day.
 * @param xlon The longitude in degrees (+ve east, -ve west).
 * @param ylat The latitude in degrees (+ve north, -ve south).
 * @param radsunz This should be passed the address of a float. On exit this is
 *  set to the calculated solar zenith angle in radians. 0 radians is at the
 *  zenith.
 * @param radsuna This should be passed the address of a float. On exit this is
 *  set to the calculated solar azimuth angle in radians. 0 radians is due
 *  north.
 */
extern void sunang(int iday, float hr, float xlon, float ylat, 
             float *radsunz, float *radsuna); 

#ifdef __cplusplus
}
#endif /* __cplusplus */
