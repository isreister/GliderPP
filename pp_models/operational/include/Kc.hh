#ifndef _KC_HH
#define _KC_HH

#include "shared_tree.h"

/**
 * A class that stores and interpolates Kc values.
 */
class Kc
{
private:
protected:
   /**
    * The kc values.
    */
   tree *data;

   /**
    * The default kc value to use if data is NULL.
    */
   float defaultValue;

public:
   /**
    * Creates the kc object with a default value.
    * @param defaultValue The default value to return as a kc value.
    */
   Kc (float defaultValue = 0.01);

   /**
    * Frees up resources used by the object.
    */
   virtual ~Kc (void);

   /**
    * Reads the data from the named file.
    * @param filename The name of the file to load kc values from.
    * @param conversionFactor The number to multiply each read value of kc by.
    * @return true if the file failed to load or data is already loaded, false
    *  otherwise.
    */
   bool readFile (const char *filename, float conversionFactor = 1.0);

   /**
    * Returns the value of Kc at the given chlorophyll and wavelength.
    * @param chl The value of chlorophyll (mg m^-3).
    * @param wavelength The wavelength (nm).
    * @return The value of Kc.
    */
   float operator() (float chl, float wavelength) const;
};

#endif /* #ifndef _KC_HH */
