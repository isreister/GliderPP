#ifndef _K_HH
#define _K_HH

#include "shared_tree.h"

/**
 * A class that stores and interpolates K values.
 */
class K
{
private:
protected:
   /**
    * The k values.
    */
   tree *data;

   /**
    * The default k value to use if data is NULL.
    */
   float defaultValue;

public:
   /**
    * Creates the k object with a default value.
    * @param defaultValue The default value to return as a k value.
    */
   K (float defaultValue = 0.01);

   /**
    * Frees up resources used by the object.
    */
   virtual ~K (void);

   /**
    * Reads the data from the named file.
    * @param filename The name of the file to load k values from.
    * @param conversionFactor The number to multiply each read value of k by.
    * @return true if the file failed to load or data is already loaded, false
    *  otherwise.
    */
   bool readFile (const char *filename, float conversionFactor = 1.0);

   /**
    * Returns the value of K at the given chlorophyll and wavelength.
    * @param depth The depth at which to take the k sample.
    * @param wavelength The wavelength (nm).
    * @return The value of K.
    */
   float operator() (float depth, float wavelength) const;
};

#endif /* #ifndef _K_HH */
