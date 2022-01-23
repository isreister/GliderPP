#ifndef _PBM_HH
#define _PBM_HH

#include "shared_tree.h"

/**
 * A class that stores and interpolates Pbm values.
 */
class Pbm
{
private:
protected:
   /**
    * The pbm values.
    */
   tree *data;

   /**
    * The default pbm value to use if data is NULL.
    */
   float defaultValue;

public:
   /**
    * Creates the pbm object with a default value.
    * @param defaultValue The default value to return as a pbm value.
    */
   Pbm (float defaultValue = 5.3);

   /**
    * Frees up resources used by the object.
    */
   virtual ~Pbm (void);

   /**
    * Reads the data from the named file.
    * @param filename The name of the file to load pbm values from.
    * @param conversionFactor The number to multiply each read value of pbm by.
    * @return true if the file failed to load or data is already loaded, false
    *  otherwise.
    */
   bool readFile (const char *filename, float conversionFactor = 1.0);

   /**
    * Returns the value of Pbm at the given pbmorophyll and wavelength.
    * @param minute The minute of the day (or data run).
    * @param depth The depth at which to sample the pbm value (m).
    * @return The value of Pbm.
    */
   float operator() (float minute, float depth) const;

   /**
    * Sets the default value of pbmorophyll.
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

#endif /* #ifndef _PBM_HH */
