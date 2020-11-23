#ifndef _ALPHA_HH
#define _ALPHA_HH

#include "shared_tree.h"

/**
 * A class that stores and interpolates Alpha values.
 */
class Alpha
{
private:
protected:
   /**
    * The alpha values.
    */
   tree *data;

   /**
    * The default alpha value to use if data is NULL.
    */
   float defaultValue;

public:
   /**
    * Creates the alpha object with a default value.
    * @param defaultValue The default value to return as a alpha value.
    */
   Alpha (float defaultValue = 0.026);

   /**
    * Frees up resources used by the object.
    */
   virtual ~Alpha (void);

   /**
    * Reads the data from the named file.
    * @param filename The name of the file to load alpha values from.
    * @param conversionFactor The number to multiply each read value of alpha by.
    * @return true if the file failed to load or data is already loaded, false
    *  otherwise.
    */
   bool readFile (const char *filename, float conversionFactor = 1.0);

   /**
    * Returns the value of Alpha at the given alpha and wavelength.
    * @param minute The minute of the day (or data run).
    * @param depth The depth at which to sample the alpha value (m).
    * @return The value of Alpha.
    */
   float operator() (float minute, float depth) const;

   /**
    * Sets the default value of alpha.
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

#endif /* #ifndef _ALPHA_HH */
