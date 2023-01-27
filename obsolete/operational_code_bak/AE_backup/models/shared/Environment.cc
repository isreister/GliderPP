#include "Environment.hh"

using namespace std;
using namespace NS_Environment;

// Environment::*
Environment::Environment (void)
{
   minuteOfDay = 0;
   dayOfYear = 1;
   monthOfYear = 1;
   year = 2000;

   timeStep = 5;
   depthStep = 1;
   wavelengthStep = 5;

   latitude = 0.0f;
   longitude = 0.0f;

   minLatitude = -90.0f;
   maxLatitude = 90.0f;
   latitudeStep = 1.0f;
   minLongitude = -180.0f;
   maxLongitude = 180.0f;
   longitudeStep = 1.0f;
}

Environment::~Environment (void)
{
}

void Environment::setMinuteOfDay (int m)
{
   minuteOfDay = m;
   FieldEnum field = fMinuteOfDay;
   notifyObservers(&field);
}

void Environment::setDayOfYear (int doy)
{
   dayOfYear = doy;
   FieldEnum field = fDayOfYear;
   notifyObservers(&field);
}

void Environment::setMonthOfYear (int moy)
{
   monthOfYear = moy;
   FieldEnum field = fMonthOfYear;
   notifyObservers(&field);
}

void Environment::setYear (int y)
{
   year = y;
   FieldEnum field = fYear;
   notifyObservers(&field);
}

void Environment::setMinimumTime (int mt)
{
   minTime = mt;
   FieldEnum field = fMinTime;
   notifyObservers(&field);
}

void Environment::setMaximumTime (int mt)
{
   maxTime = mt;
   FieldEnum field = fMaxTime;
   notifyObservers(&field);
}

void Environment::setTimeStep (int ts)
{
   timeStep = ts;
   FieldEnum field = fTimeStep;
   notifyObservers(&field);
}

void Environment::setMaximumDepth (int md)
{
   maxDepth = md;
   FieldEnum field = fMaxDepth;
   notifyObservers(&field);
}

void Environment::setDepthStep (int ds)
{
   depthStep = ds;
   FieldEnum field = fDepthStep;
   notifyObservers(&field);
}

void Environment::setMinimumWavelegnth (int mw)
{
   minWavelength = mw;
   FieldEnum field = fMinWavelength;
   notifyObservers(&field);
}

void Environment::setMaximumWavelength (int mw)
{
   maxWavelength = mw;
   FieldEnum field = fMaxWavelength;
   notifyObservers(&field);
}

void Environment::setWavelengthStep (int ws)
{
   wavelengthStep = ws;
   FieldEnum field = fWavelengthStep;
   notifyObservers(&field);
}

void Environment::setLatitude (float l)
{
   latitude = l;
   FieldEnum field = fLatitude;
   notifyObservers(&field);
}

void Environment::setMinimumLatitude (float l)
{
   minLatitude = l;
   FieldEnum field = fMinLatitude;
   notifyObservers(&field);
}

void Environment::setMaximumLatitude (float l)
{
   maxLatitude = l;
   FieldEnum field = fMaxLatitude;
   notifyObservers(&field);
}

void Environment::setLatitudeStep (float l)
{
   latitudeStep = l;
   FieldEnum field = fLatitudeStep;
   notifyObservers(&field);
}

void Environment::setLongitude (float l)
{
   longitude = l;
   FieldEnum field = fLongitude;
   notifyObservers(&field);
}

void Environment::setMinimumLongitude (float l)
{
   minLongitude = l;
   FieldEnum field = fMinLongitude;
   notifyObservers(&field);
}

void Environment::setMaximumLongitude (float l)
{
   maxLongitude = l;
   FieldEnum field = fMaxLongitude;
   notifyObservers(&field);
}

void Environment::setLongitudeStep (float l)
{
   longitudeStep = l;
   FieldEnum field = fLongitudeStep;
   notifyObservers(&field);
}

void Environment::resetLocation (void)
{
   latitude = minLatitude;
   FieldEnum field = fLatitude;
   notifyObservers(&field);
   latitude = minLongitude;
   field = fLongitude;
   notifyObservers(&field);
}

bool Environment::nextLocation (void)
{
   float nextLongitude = longitude + longitudeStep;
   FieldEnum field;

   if (nextLongitude <= maxLongitude)
   {
      // Move one step along the line
      longitude = nextLongitude;
      return true;
   }
   else
   {
      // Gone off end of line (past maxLongitude)
      float nextLatitude = latitude + latitudeStep;

      // Have we reached the last line of the image?
      if (nextLatitude <= maxLatitude)
      {
         // Move down one line and move to its start
         longitude = minLongitude;
         field = fLongitude;
         notifyObservers(&field);
         latitude = nextLatitude;
         field = fLatitude;
         notifyObservers(&field);
         return true;
      }
      else
      {
         // No more locations to visit
         return false;
      }
   }
}

// EnvironmentReferencer::*
EnvironmentReferencer::EnvironmentReferencer (Environment *e)
   : eListener(this)
{
   environment = NULL;
   setEnvironment(e);
}

EnvironmentReferencer::~EnvironmentReferencer (void)
{
   setEnvironment(NULL);
}

void EnvironmentReferencer::setEnvironment (Environment *e)
{
   if (environment != NULL)
      environment->removeObserver(&eListener);
   environment = e;
   if (e != NULL)
      e->addObserver(&eListener);
}

// EnvironmentReferencer::EnvironmentListener::*
EnvironmentReferencer::
EnvironmentListener::
EnvironmentListener (EnvironmentReferencer *p)
{
   parent = p;
}

void
EnvironmentReferencer::
EnvironmentListener::
observableChanged(Observable *o, void *msgObject)
{
   FieldEnum *field = (FieldEnum *)msgObject;
   parent->environmentChanged(*field);
}
