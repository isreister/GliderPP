#ifndef _ACHL_HH
#define _ACHL_HH

#include "shared_list.h"

/**
 * A class that stores and interpolates Achl values.
 */
class Achl
{
private:
protected:
   /**
    * The achl values.
    */
   node *data;

   /**
    * The default achl value to use if data is NULL.
    */
   float defaultValue;

public:
   /**
    * Creates the achl object with a default value.
    * @param defaultValue The default value to return as a achl value.
    */
   Achl (float defaultValue = 0.54);

   /**
    * Frees up resources used by the object.
    */
   virtual ~Achl (void);

   /**
    * Reads the data from the named file.
    * @param filename The name of the file to load achl values from.
    * @param conversionFactor The number to multiply each read value of achl by.
    * @return true if the file failed to load or data is already loaded, false
    *  otherwise.
    */
   bool readFile (const char *filename, float conversionFactor = 1.0);

   /**
    * Returns the value of Achl at the given wavelength.
    * @param wavelength The wavelength (nm).
    * @return The value of Achl.
    */
   float operator() (int wavelength) const;
};

#endif /* #ifndef _ACHL_HH */
