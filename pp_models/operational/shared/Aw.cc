#include <stdlib.h>
#include <stdio.h>
#include "Aw.hh"

using namespace std;

Aw::Aw (float defaultValue)
{
   data = NULL;
   this->defaultValue = defaultValue;
}

Aw::~Aw (void)
{
   if (data != NULL)
      delete_list(data);
}

bool Aw::readFile (const char *filename, float conversionFactor)
{
   FILE *in;

   if (data != NULL)
      return true;

   int wavelength;
   float aw;

   // Open file and check for error
   in = fopen(filename, "r");
   if (in == NULL)
      return true;

   // Read fields until EOF
   while (!feof(in))
   {
      int fieldsRead = fscanf(in, " %d %f ", &wavelength, &aw);
      if (fieldsRead <= 0)
         continue;
      if (fieldsRead != 2)
      {
         fclose(in);
         return true;
      }
      data = add_list_value(data, wavelength, aw*conversionFactor);
   }

   fclose(in);

   return false;
}

float Aw::operator() (int wavelength) const
{
   return interpolate_using_list(data, wavelength, defaultValue);
}
