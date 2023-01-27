#ifndef _APH_HH
#define _APH_HH

#include "dataset_3.h"

/**
 * A class that stores and interpolates Aph values.
 */
class Aph
{
private:
protected:
   /**
    * The aph values.
    */
   dataset_3 *data;

   /**
    * The default aph value to use if data is NULL.
    */
   float defaultValue;

public:
   /**
    * Creates the aph object with a default value.
    * @param defaultValue The default value to return as a aph value.
    */
   Aph (float defaultValue = 0.01);

   /**
    * Frees up resources used by the object.
    */
   virtual ~Aph (void);

   /**
    * Reads the data from the named file.
    * @param filename The name of the file to load aph values from.
    * @param conversionFactor The number to multiply each read value of aph by.
    * @return true if the file failed to load or data is already loaded, false
    *  otherwise.
    */
   bool readFile (const char *filename, float conversionFactor = 1.0);

   /**
    * Returns the value of Aph at the given time, depth and wavelength.
    * @param time The time of day (minutes).
    * @param depth The depth (m).
    * @param wavelength The wavelength (nm).
    * @return The value of Aph.
    */
   float operator() (int time, float depth, float wavelength) const;
};

#endif /* #ifndef _APH_HH */
