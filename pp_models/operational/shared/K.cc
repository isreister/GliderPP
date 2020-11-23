#include <stdlib.h>
#include <stdio.h>
#include "K.hh"

using namespace std;

K::K (float defaultValue)
{
   data = NULL;
   this->defaultValue = defaultValue;
}

K::~K (void)
{
   if (data != NULL)
      delete_tree(data);
}

bool K::readFile (const char *filename, float conversionFactor)
{
   FILE *in;

   if (data != NULL)
      return true;

   float depth;
   float wavelength;
   float k;

   // Open file and check for error
   in = fopen(filename, "r");
   if (in == NULL)
      return true;

   // Read fields until EOF
   while (!feof(in))
   {
      int fieldsRead = fscanf(in, " %f %f %f ", &depth, &wavelength, &k);
      if (fieldsRead <= 0)
         continue;
      if (fieldsRead != 3)
      {
         fclose(in);
         return true;
      }
      data = add_tree_value(data, depth, wavelength, k*conversionFactor);
   }

   fclose(in);

   triangulate_tree(data);
   return false;
}

float K::operator() (float depth, float wavelength) const
{
   return interpolate_using_tree(data, depth, wavelength, defaultValue);
}
