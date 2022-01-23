#ifndef _AW_HH
#define _AW_HH

#include "shared_list.h"

/**
 * A class that stores and interpolates Aw values.
 */
class Aw
{
private:
protected:
   /**
    * The aw values.
    */
   node *data;

   /**
    * The default aw value to use if data is NULL.
    */
   float defaultValue;

public:
   /**
    * Creates the aw object with a default value.
    * @param defaultValue The default value to return as a aw value.
    */
   Aw (float defaultValue = 0.001);

   /**
    * Frees up resources used by the object.
    */
   virtual ~Aw (void);

   /**
    * Reads the data from the named file.
    * @param filename The name of the file to load aw values from.
    * @param conversionFactor The number to multiply each read value of aw by.
    * @return true if the file failed to load or data is already loaded, false
    *  otherwise.
    */
   bool readFile (const char *filename, float conversionFactor = 1.0);

   /**
    * Returns the value of Aw at the given wavelength.
    * @param wavelength The wavelength (nm).
    * @return The value of Aw.
    */
   float operator() (int wavelength) const;
};

#endif /* #ifndef _AC_HH */
