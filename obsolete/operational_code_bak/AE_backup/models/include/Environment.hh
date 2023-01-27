#ifndef _ENVIRONMENT_HH
#define _ENVIRONMENT_HH

#include "Observer.hh"

namespace NS_Environment
{
/**
 * The fields in the environment class.
 */
typedef enum
{
   /**
    * All the fields in the environment object changed and/or the environment
    *  object itself was exchanged for a new one.
    */
   fAll,
   /// The minute of the day field.
   fMinuteOfDay,
   /// The month of the year field.
   fDayOfYear,
   /// The month of the year field.
   fMonthOfYear,
   /// The year field.
   fYear,

   /// The start time field.
   fMinTime,
   /// The end time field.
   fMaxTime,
   /// The time increment field.
   fTimeStep,
   /// The maximum depth field.
   fMaxDepth,
   /// The depth increment field.
   fDepthStep,
   /// The minimum wavelength field.
   fMinWavelength,
   /// The maximum wavelength field.
   fMaxWavelength,
   /// The wavelength increment field.
   fWavelengthStep,

   /// The latitude field.
   fLatitude,
   /// The longitude field.
   fLongitude,

   /// The minimum latitude field.
   fMinLatitude,
   /// The maximum latitude field.
   fMaxLatitude,
   /// The latitude increment field.
   fLatitudeStep,
   /// The minimum longitude field.
   fMinLongitude,
   /// The maximum longitude field.
   fMaxLongitude,
   /// The longitude increment field.
   fLongitudeStep
} FieldEnum;
}

/**
 * An environment class. This carries global parameters for the state and
 *  parameters for a model's run. This class implements observable and whenever
 *  it changes it passes a pointer to a NS_Environment::FieldEnum variable
 *  which contains a value indicating which field changed.
 * @see NS_Environment::FieldEnum
 */
class Environment : public Observable
{
private:
protected:
   /// The minute of the day.
   int minuteOfDay;
   /// The day of the year.
   int dayOfYear;
   /// The month of the year.
   int monthOfYear;
   /// The year.
   int year;

   /// The start time in minutes.
   int minTime;
   /// The end time in minutes.
   int maxTime;
   /// The time increment in minutes.
   int timeStep;
   /// The maximum depth in metres.
   int maxDepth;
   /// The depth increment in metres.
   int depthStep;
   /// The minimum wavelength in nanometres.
   int minWavelength;
   /// The maximum wavelength in nanometres.
   int maxWavelength;
   /// The wavelength increment in nanometres.
   int wavelengthStep;

   /// The latitude.
   float latitude;
   /// The longitude.
   float longitude;

   /// The minimum latitude to calculate at (degrees).
   float minLatitude;
   /// The maximum latitude to calculate at (degrees).
   float maxLatitude;
   /// The latitude increment (degrees).
   float latitudeStep;
   /// The minimum longitude to visit (degrees).
   float minLongitude;
   /// The maximum longitude to visit (degrees).
   float maxLongitude;
   /// The longitude increment (degrees).
   float longitudeStep;
public:
   /**
    * Creates an environment object with default values.
    */
   Environment (void);

   /**
    * Destructor.
    */
   virtual ~Environment (void);

   /**
    * Sets the minute of the day.
    * @param m The new minute of the day.
    */
   void setMinuteOfDay (int m);

   /**
    * Returns the minute of the day.
    * @return The minute of the day.
    */
   inline int getMinuteOfDay (void) { return minuteOfDay; }

   /**
    * Sets the day of the year.
    * @param doy The new day of the year.
    */
   void setDayOfYear (int doy);

   /**
    * Returns the day of the year.
    * @return The day of the year.
    */
   inline int getDayOfYear (void) { return dayOfYear; }

   /**
    * Sets the month of the year.
    * @param moy The new month of the year.
    */
   void setMonthOfYear (int moy);

   /**
    * Returns the month of the year.
    * @return The month of the year.
    */
   inline int getMonthOfYear (void) { return monthOfYear; }

   /**
    * Sets the year.
    * @param y The new year.
    */
   void setYear (int y);

   /**
    * Returns the year.
    * @return The year.
    */
   inline int getYear (void) const { return year; }

   /**
    * Sets the start time.
    * @param mt The new start time in minutes.
    */
   void setMinimumTime (int mt);

   /**
    * Returns the start time.
    * @return The start time in minutes.
    */
   inline int getMinimumTime (void) const { return minTime; }

   /**
    * Sets the end time.
    * @param mt The new end time in minutes.
    */
   void setMaximumTime (int mt);

   /**
    * Returns the end time.
    * @return The end time in minutes.
    */
   inline int getMaximumTime (void) const { return maxTime; }

   /**
    * Sets the time increment.
    * @param ts The new time increment in minutes.
    */
   void setTimeStep (int ts);

   /**
    * Returns the time increment.
    * @return The time increment in minutes.
    */
   inline int getTimeStep (void) const { return timeStep; }

   /**
    * Sets the maximum depth.
    * @param md The new maximum depth in metres.
    */
   void setMaximumDepth (int md);

   /**
    * Returns the maximum depth.
    * @return The maximum depth in metres.
    */
   inline int getMaximumDepth (void) const { return maxDepth; }

   /**
    * Sets the depth increment.
    * @param ds The new depth increment in metres.
    */
   void setDepthStep (int ds);

   /**
    * Returns the depth increment.
    * @return The depth increment in metres.
    */
   inline int getDepthStep (void) const { return depthStep; }

   /**
    * Sets the minimum wavelength.
    * @param mw The new minimum wavelength in nanometres.
    */
   void setMinimumWavelegnth (int mw);

   /**
    * Returns the minimum wavelength.
    * @return The minimum wavelength in nanometres.
    */
   inline int getMinimumWavelength (void) const { return minWavelength; }

   /**
    * Sets the maximum wavelength.
    * @param mw The new maximum wavelength in nanometres.
    */
   void setMaximumWavelength (int mw);

   /**
    * Returns the maximum wavelength.
    * @return The maximum wavelength in nanometres.
    */
   inline int getMaximumWavelength (void) const { return maxWavelength; }

   /**
    * Sets the wavelength increment.
    * @param ws The new wavelength increment in nanometres.
    */
   void setWavelengthStep (int ws);

   /**
    * Returns the wavelength increment.
    * @return The wavelength increment in nanometres.
    */
   inline int getWavelengthStep (void) const { return wavelengthStep; }

   /**
    * Sets the latitude.
    * @param l The new latitude in degrees.
    */
   void setLatitude (float l);

   /**
    * Returns the latitude.
    * @return The latitude in degrees.
    */
   inline float getLatitude (void) const { return latitude; }

   /**
    * Sets the minimum latitude.
    * @param l The new minimum latitude in degrees.
    */
   void setMinimumLatitude (float l);

   /**
    * Returns the minimum latitude.
    * @return The minimum latitude in degrees.
    */
   inline float getMinimumLatitude (void) const { return minLatitude; }

   /**
    * Sets the maximum latitude.
    * @param l The new maximum latitude in degrees.
    */
   void setMaximumLatitude (float l);

   /**
    * Returns the maximum latitude.
    * @return The maximum latitude in degrees.
    */
   inline float getMaximumLatitude (void) const { return maxLatitude; }

   /**
    * Sets the latitude step.
    * @param l The new latitude step in degrees.
    */
   void setLatitudeStep (float l);

   /**
    * Returns the latitude step.
    * @return The latitude step in degrees.
    */
   inline float getLatitudeStep (void) const { return latitudeStep; }

   /**
    * Sets the longitude.
    * @param l The new longitude in degrees.
    */
   void setLongitude (float l);

   /**
    * Returns the longitude.
    * @return The longitude in degrees.
    */
   inline float getLongitude (void) const { return longitude; }

   /**
    * Sets the minimum longitude.
    * @param l The new minimum longitude in degrees.
    */
   void setMinimumLongitude (float l);

   /**
    * Returns the minimum longitude.
    * @return The minimum longitude in degrees.
    */
   inline float getMinimumLongitude (void) const { return minLongitude; }

   /**
    * Sets the maximum longitude.
    * @param l The new maximum longitude in degrees.
    */
   void setMaximumLongitude (float l);

   /**
    * Returns the maximum longitude.
    * @return The maximum longitude in degrees.
    */
   inline float getMaximumLongitude (void) const { return maxLongitude; }

   /**
    * Sets the longitude step.
    * @param l The new longitude step in degrees.
    */
   void setLongitudeStep (float l);

   /**
    * Returns the longitude step.
    * @return The longitude step in degrees.
    */
   inline float getLongitudeStep (void) const { return longitudeStep; }

   /**
    * Sets latitude to the minimum latitude, and longitude to the minimum
    *  longitude.
    */
   void resetLocation (void);

   /**
    * Increments the latitude and longitude to the next point. It will increment
    *  latitude and longitude by latitudeStep and longitudeStep respectively at
    *  appropriate times. It will wrap longitude as needed. If resetLocation()
    *  is called, and then this method called successively until it returns
    *  false then every sampling point will be visited once each.
    * @return true if the location was updated, false if there are no more
    *  points to visit.
    */
   bool nextLocation (void);
};

/**
 * A base class for objects that use an environment object. Any object that uses
 *  information from an environment object needs only to extend from this class
 *  and implement environmentChanged() (to listen for changing fields in
 *  environment).
 */
class EnvironmentReferencer
{
private:
   /**
    * A class used internally to listen for environment changes.
    */
   class EnvironmentListener : public Observer
   {
   private:
      /// The parent EnvironmentReferencer object.
      EnvironmentReferencer *parent;
   public:
      /**
       * Sets the parent EnvironmentReferencer object.
       * @param p The parent EnvironmentReferencer object.
       */
      EnvironmentListener (EnvironmentReferencer *p);

      void observableChanged(Observable *o, void *msgObject);
   };

   EnvironmentListener eListener;

protected:
   /**
    * The environment.
    */
   Environment *environment;

   /**
    * This is called when one of the environment object's fields changes.
    * @param field The field that changed.
    * @see NS_Environment::fieldEnum
    */
   virtual void environmentChanged (NS_Environment::FieldEnum field) = 0;

public:
   /**
    * Sets the environment object to use.
    * @param e The environment object to use.
    */
   EnvironmentReferencer (Environment *e = NULL);

   /**
    * Destructor.
    */
   virtual ~EnvironmentReferencer (void);

   /**
    * Sets the environment object to use.
    * @param e The environment object to use.
    */
   void setEnvironment (Environment *e);

   /**
    * Returns the environment object being used.
    * @return The environment object being used.
    */
   inline Environment *getEnvironment (void) { return environment; }

   // This line seems to be needed on some versions of gcc (specifically 2.95.2)
   //  otherwise it complains (it shouldn't need this line really, although
   //  there is no harm in having it here).
   friend class EnvironmentListener;
};

#endif /* #ifndef _ENVIRONMENT_HH */
