import logging
import numpy as np

def spheric_dist(lat1,lat2,lon1,lon2,mode='global',logging=logging):
#####################################################################
#
# function dist=spheric_dist(lat1,lat2,lon1,lon2)
#
# compute distances for a simple spheric earth
#
# input:
#
# lat1 : latitude of first point (matrix or point)
# lon1 : longitude of first point (matrix or point)
# lat2 : latitude of second point (matrix or point)
# lon2 : longitude of second point (matrix or point)
#
# output:
# dist : distance from first point to second point (matrix)
################################################################

   R = 6367442.76
   # Determine proper longitudinal shift.
   l = np.abs(lon2-lon1)
   try:
      l[l >= 180] = 360 - l[l >= 180]
   except:
      pass
   # Convert Decimal degrees to radians.
   deg2rad = np.pi/180
   phi1    = (90-lat1)*deg2rad
   phi2    = (90-lat2)*deg2rad
   theta1  = lon1*deg2rad
   theta2  = lon2*deg2rad

   lat1    = lat1*deg2rad
   lat2    = lat2*deg2rad
   l       = l*deg2rad

   if mode=='global':
      # Compute the distances: new
      cos     = (np.sin(phi1)*np.sin(phi2)*np.cos(theta1 - theta2) + 
                 np.cos(phi1)*np.cos(phi2))
      arc     = np.arccos( cos )
      dist    = R*arc
   elif mode=='regional':
      # Compute the distances: 1 old, deprecated ROMS version - unsuitable for global
      dist    = R*np.arcsin(np.sqrt(((np.sin(l)*np.cos(lat2))**2) + (((np.sin(lat2)*np.cos(lat1)) - \
                (np.sin(lat1)*np.cos(lat2)*np.cos(l)))**2)))
   elif mode=='local':
      #uses approx for now: 
      x = [lon2-lon1] * np.cos(0.5*[lat2+lat1])
      y = lat2-lat1
      dist = R*[x*x+y*y]^0.5
   else:
      if logging:
         logging.info('incorrect mode')
      else:
         print('incorrect mode')

   return dist

def fix_bad_points(lons,lats,times,threshold=50,npol=2):

   print('----Stripping geographic outliers----')

   # check for polarity swapping: LAT
   polarity = np.ones(np.shape(lats))
   polarity[lats<0]=-1
   if len(np.where(abs(np.diff(polarity)) > 0)[0]) > npol:
      # put in northern hemisphere
      print('Putting in northern hemisphere')
      lats = abs(lats)

   # check for bad lons
   lons[lons>180] = lons[lons> 180] - 360

   bad_flag = True   
   # keep looping until all bad points are gone - or we run out of points!
   while bad_flag:
      bad_flag = False
      #first point:
      d1 = spheric_dist(lats[0],lats[1],lons[0],lons[1],logging=None)/1000
      s1 = d1/(times[1] - times[0])

      if s1 < threshold:
         lons_stripped   = [lons[0]]
         lats_stripped   = [lats[0]]
         times_stripped  = [times[0]]
      else:
         lons_stripped   = []
         lats_stripped   = []
         times_stripped  = []
         bad_flag = True

      # if point is more than threshold (in km/day) away from its neighbours, ditch it
      for i in np.arange(1,len(lons)-1):
         d1 = spheric_dist(lats[i-1],lats[i],lons[i-1],lons[i],logging=None)/1000
         d2 = spheric_dist(lats[i],lats[i+1],lons[i],lons[i+1],logging=None)/1000
         s1 = d1/(times[i]   - times[i - 1])
         s2 = d2/(times[i+1] - times[i])
         if s1 < threshold and s2 < threshold:
            lons_stripped.append(lons[i])
            lats_stripped.append(lats[i])
            times_stripped.append(times[i])
         else:
            new_lat,new_lon,viable = min_quadrant(lats[i-1],lats[i],\
                                                  lons[i-1],lons[i],
                                                  times[i-1],times[i],threshold)
            if viable:
               lons_stripped.append(new_lon)
               lats_stripped.append(new_lat)
               times_stripped.append(times[i])
            else:
               bad_flag = True

      # last point:
      d1 = spheric_dist(lats[-2],lats[-1],lons[-2],lons[-1],logging=None)/1000
      s1 = d1/(times[-1] - times[-2])

      if s1 < threshold:
         lons_stripped.append(lons[-1])
         lats_stripped.append(lats[-1])
         times_stripped.append(times[-1])
      else:
         bad_flag = True

      lons  = lons_stripped[:]
      lats  = lats_stripped[:]
      times = times_stripped[:]

   return np.asarray(lons_stripped), np.asarray(lats_stripped),np.asarray(times_stripped)

def min_quadrant(lat_m1,lat,lon_m1,lon,t_m1,t,threshold):
  
   ret_lat = []
   ret_lon = []
   ii_saved = []
   jj_saved = []
   viable  = False
   #find minimum for d1*d2
   for ii in [-1,1]:
      for jj in [-1,1]:
         d1 = spheric_dist(lat_m1,lat*ii,lon_m1,lon*jj,logging=None)/1000
         s1 = d1/(t   - t_m1)
         if s1 < threshold:
            ret_lat = lat*ii
            ret_lon = lon*ii
            viable = True
            break

   return ret_lat,ret_lon,viable
