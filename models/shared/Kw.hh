#ifndef _KW_HH
#define _KW_HH

#include "shared_list.h"

/**
 * A class that stores and interpolates Kw values.
 */
class Kw
{
private:
protected:
   /**
    * The kw values.
    */
   node *data;

   /**
    * The default kw value to use if data is NULL.
    */
   float defaultValue;

public:
   /**
    * Creates the kw object with a default value.
    * @param defaultValue The default value to return as a kw value.
    */
   Kw (float defaultValue = 0.01);

   /**
    * Frees up resources used by the object.
    */
   virtual ~Kw (void);

   /**
    * Reads the data from the named file.
    * @param filename The name of the file to load kw values from.
    * @param conversionFactor The number to multiply each read value of kw by.
    * @return true if the file failed to load or data is already loaded, false
    *  otherwise.
    */
   bool readFile (const char *filename, float conversionFactor = 1.0);

   /**
    * Returns the value of Kw at the given wavelength.
    * @param wavelength The wavelength (nm).
    * @return The value of Kw.
    */
   float operator() (int wavelength) const;
};

#endif /* #ifndef _KW_HH */
