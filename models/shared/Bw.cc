#include <stdlib.h>
#include <stdio.h>
#include "Bw.hh"

using namespace std;

Bw::Bw (float defaultValue)
{
   data = NULL;
   this->defaultValue = defaultValue;
}

Bw::~Bw (void)
{
   if (data != NULL)
      delete_list(data);
}

bool Bw::readFile (const char *filename, float conversionFactor)
{
   FILE *in;

   if (data != NULL)
      return true;

   int wavelength;
   float bw;

   // Open file and check for error
   in = fopen(filename, "r");
   if (in == NULL)
      return true;

   // Read fields until EOF
   while (!feof(in))
   {
      int fieldsRead = fscanf(in, " %d %f ", &wavelength, &bw);
      if (fieldsRead <= 0)
         continue;
      if (fieldsRead != 2)
      {
         fclose(in);
         return true;
      }
      data = add_list_value(data, wavelength, bw*conversionFactor);
   }

   fclose(in);

   return false;
}

float Bw::operator() (int wavelength) const
{
   return interpolate_using_list(data, wavelength, defaultValue);
}
