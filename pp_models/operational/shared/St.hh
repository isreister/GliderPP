#ifndef _ST_HH
#define _ST_HH

#include "shared_tree.h"

/**
 * A class that stores and interpolates sea temperature values.
 */
class St
{
private:
protected:
   /**
    * The sea temperature values.
    */
   tree *data;

   /**
    * The default sea temperature value to use if data is NULL.
    */
   float defaultValue;

public:
   /**
    * Creates the sea temperature object with a default value.
    * @param defaultValue The default value to return as a sea temperature value.
    */
   St (float defaultValue = 0.0);

   /**
    * Frees up resources used by the object.
    */
   virtual ~St (void);

   /**
    * Reads the data from the named file.
    * @param filename The name of the file to load sea temperature values from.
    * @param conversionFactor The number to multiply each read value of sea
    *  temperature by.
    * @return true if the file failed to load or data is already loaded, false
    *  otherwise.
    */
   bool readFile (const char *filename, float conversionFactor = 1.0);

   /**
    * Returns the value of sea temperature at the given time and depth.
    * @param minute The minute of the day (or data run).
    * @param depth The depth at which to sample the sea temperature value (m).
    * @return The value of sea temperature.
    */
   float operator() (float minute, float depth) const;

   /**
    * Sets the default value of sea temperature.
    * @param defaultValue The value to use as the default.
    */
   inline void setDefault (float defaultValue = 0.0)
   {
      this->defaultValue = defaultValue;
   }

   /**
    * Clears out the loaded data. This allows for different values to be loaded
    *  instead or to use the default value.
    */
   void clear (void);
};

#endif /* #ifndef _ST_HH */
