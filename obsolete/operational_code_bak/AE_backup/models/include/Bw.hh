#ifndef _BW_HH
#define _BW_HH

#include "shared_list.h"

/**
 * A class that stores and interpolates Bw values.
 */
class Bw
{
private:
protected:
   /**
    * The bw values.
    */
   node *data;

   /**
    * The default bw value to use if data is NULL.
    */
   float defaultValue;

public:
   /**
    * Creates the bw object with a default value.
    * @param defaultValue The default value to return as a bw value.
    */
   Bw (float defaultValue = 0.01);

   /**
    * Frees up resources used by the object.
    */
   virtual ~Bw (void);

   /**
    * Reads the data from the named file.
    * @param filename The name of the file to load bw values from.
    * @param conversionFactor The number to multiply each read value of bw by.
    * @return true if the file failed to load or data is already loaded, false
    *  otherwise.
    */
   bool readFile (const char *filename, float conversionFactor = 1.0);

   /**
    * Returns the value of Bw at the given wavelength.
    * @param wavelength The wavelength (nm).
    * @return The value of Bw.
    */
   float operator() (int wavelength) const;
};

#endif /* #ifndef _BW_HH */
