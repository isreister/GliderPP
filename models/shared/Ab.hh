#ifndef _AB_HH
#define _AB_HH

#include "shared_tree.h"

/**
 * A class that stores and interpolates b/a values.
 * The original matrix is values of a and b as a function
 * of depth and wavelength and is currently the output
 * from HYDROLIGHT
 */
class Ab
{
private:
protected:
   /**
    * The ab values.
    */
   tree *data;

   /**
    * The default ab values to use if data is NULL.
    */
   float defaultValue;

public:
   /**
    * Creates the k object with a default value.
    * @param defaultValue The default value to return as a k value.
    */
   Ab (float defaultValue = 0.01);

   /**
    * Frees up resources used by the object.
    */
   virtual ~Ab (void);

   /**
    * Reads the data from the named file.
    * @param filename The name of the file to load a and b values from.
    * @param conversionFactor The number to multiply each read value of a and b by.
    * @return true if the file failed to load or data is already loaded, false
    *  otherwise.
    */
   bool readFile (const char *filename, float conversionFactor = 1.0);

   /**
    * Returns the value of b/a at the given depth and wavelength.
    * @param depth The depth at which to take the b/a sample.
    * @param wavelength The wavelength (nm).
    * @return The value of b/a.
    */
   float operator() (float depth, float wavelength) const;
};

#endif /* #ifndef _AB_HH */
