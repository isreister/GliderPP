#ifndef _BETA_HH
#define _BETA_HH

#include "shared_tree.h"

/**
 * A class that stores and interpolates Beta values.
 */
class Beta
{
private:
protected:
   /**
    * The beta values.
    */
   tree *data;

   /**
    * The default beta value to use if data is NULL.
    */
   float defaultValue;

public:
   /**
    * Creates the beta object with a default value.
    * @param defaultValue The default value to return as a beta value.
    */
   Beta (float defaultValue = 0.0);

   /**
    * Frees up resources used by the object.
    */
   virtual ~Beta (void);

   /**
    * Reads the data from the named file.
    * @param filename The name of the file to load beta values from.
    * @param conversionFactor The number to multiply each read value of beta by.
    * @return true if the file failed to load or data is already loaded, false
    *  otherwise.
    */
   bool readFile (const char *filename, float conversionFactor = 1.0);

   /**
    * Returns the value of Beta at the given beta and wavelength.
    * @param minute The minute of the day (or data run).
    * @param depth The depth at which to sample the beta value (m).
    * @return The value of Beta.
    */
   float operator() (float minute, float depth) const;

   /**
    * Sets the default value of beta.
    * @param defaultValue The value to use as the default.
    */
   inline void setDefault (float defaultValue = 0.0)
   {
      this->defaultValue = defaultValue;
   }

   /**
    * Clears out the loaded data. This allows for different values to be loaded
    *  instead or to use the default value.
    */
   void clear (void);
};

#endif /* #ifndef _BETA_HH */
