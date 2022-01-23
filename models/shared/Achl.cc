#include <stdlib.h>
#include <stdio.h>
#include "Achl.hh"

using namespace std;

Achl::Achl (float defaultValue)
{
   data = NULL;
   this->defaultValue = defaultValue;
}

Achl::~Achl (void)
{
   if (data != NULL)
      delete_list(data);
}

bool Achl::readFile (const char *filename, float conversionFactor)
{
   FILE *in;

   if (data != NULL)
      return true;

   int wavelength;
   float achl;

   // Open file and check for error
   in = fopen(filename, "r");
   if (in == NULL)
      return true;

   // Read fields until EOF
   while (!feof(in))
   {
      int fieldsRead = fscanf(in, " %d %f ", &wavelength, &achl);
      if (fieldsRead <= 0)
         continue;
      if (fieldsRead != 2)
      {
         fclose(in);
         return true;
      }
      data = add_list_value(data, wavelength, achl*conversionFactor);
   }

   fclose(in);

   return false;
}

float Achl::operator() (int wavelength) const
{
   return interpolate_using_list(data, wavelength, defaultValue);
}
