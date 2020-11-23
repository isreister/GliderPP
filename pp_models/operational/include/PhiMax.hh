#ifndef _PHI_MAX_HH
#define _PHI_MAX_HH

#include "shared_tree.h"

/**
 * A class that stores and interpolates PhiMax values.
 */
class PhiMax
{
private:
protected:
   /**
    * The phiMax values.
    */
   tree *data;

   /**
    * The default phiMax value to use if data is NULL.
    */
   float defaultValue;

public:
   /**
    * Creates the phiMax object with a default value.
    * @param defaultValue The default value to return as a phiMax value.
    */
   PhiMax (float defaultValue = 0.001);

   /**
    * Frees up resources used by the object.
    */
   virtual ~PhiMax (void);

   /**
    * Reads the data from the named file.
    * @param filename The name of the file to load phiMax values from.
    * @param conversionFactor The number to multiply each read value of phiMax
    *  by.
    * @return true if the file failed to load or data is already loaded, false
    *  otherwise.
    */
   bool readFile (const char *filename, float conversionFactor = 1.0);

   /**
    * Returns the value of PhiMax at the given time and depth.
    * @param time The time (minutes).
    * @param depth The depth (m).
    * @return The value of PhiMax.
    */
   float operator() (int time, int depth) const;
};

#endif /* #ifndef _PHI_MAX_HH */
