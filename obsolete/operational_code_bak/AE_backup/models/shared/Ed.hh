#ifndef _ED_HH
#define _ED_HH

#include "shared_tree.h"

/**
 * A class that stores and interpolates Ed and mu0 values.
 */
class Ed
{
private:
protected:
   /**
    * The ed values.
    */
   tree *edData;

   /**
    * The mu0 values.
    */
   tree *mu0Data;

   /**
    * The default ed value to use if edData is NULL.
    */
   float defaultEd;

   /**
    * The default mu0 value to use if edData is NULL.
    */
   float defaultMu0;

   /**
    * The first minute of the loaded data.
    */
   int firstMinute;

   /**
    * The last minute of the loaded data.
    */
   int lastMinute;

public:
   /**
    * Creates the ed object with a default value.
    * @param defaultEdValue The default value to return as a ed value.
    * @param defaultMu0Value The default value to return as a mu0 value.
    */
   Ed (float defaultEdValue = 0.0, float defaultMu0Value = 1.0);

   /**
    * Frees up resources used by the object.
    */
   virtual ~Ed (void);

   /**
    * Reads the data from the named file.
    * @param filename The name of the file to load ed and mu0 values from.
    * @param edConversionFactor The number to multiply each read value of ed by.
    * @param mu0ConversionFactor The number to multiply each read value of
    *  mu0 by.
    * @return true if the file failed to load or data is already loaded, false
    *  otherwise.
    */
   bool readFile (const char *filename, float edConversionFactor = 1.0,
      float mu0ConversionFactor = 1.0);

   /**
    * Returns the value of Ed at the given wavelength and time
    *  (in W M^-2 nm^-1).
    * @param minute The minute of the day (or run of data).
    * @param wavelength The wavelength (nm).
    * @return The value of Ed.
    */
   float operator() (int minute, float wavelength) const;

   /**
    * Returns the value of mu0 at the given wavelength and time.
    * @param minute The minute of the day (or run of data).
    * @param wavelength The wavelength (nm).
    * @return The value of mu0.
    */
   float getMu0 (int minute, float wavelength) const;

   /**
    * Returns the first minute of the day (or run of data) that was loaded.
    * @return The first minute of the day (or run of data) that was loaded.
    */
   inline int getFirstMinute (void) const { return firstMinute; }

   /**
    * Returns the last minute of the day (or run of data) that was loaded.
    * @return The last minute of the day (or run of data) that was loaded.
    */
   inline int getLastMinute (void) const { return lastMinute; }
};

#endif /* #ifndef _ED_HH */
