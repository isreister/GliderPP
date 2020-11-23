#include <stdlib.h>
#include <stdio.h>
#include "Kc.hh"

using namespace std;

Kc::Kc (float defaultValue)
{
   data = NULL;
   this->defaultValue = defaultValue;
}

Kc::~Kc (void)
{
   if (data != NULL)
      delete_tree(data);
}

bool Kc::readFile (const char *filename, float conversionFactor)
{
   FILE *in;

   if (data != NULL)
      return true;

   float wavelength;
   float kc;
   float chl;

   // Open file and check for error
   in = fopen(filename, "r");
   if (in == NULL)
      return true;

   // Read fields until EOF
   while (!feof(in))
   {
      int fieldsRead = fscanf(in, " %f %f %f ", &wavelength, &chl, &kc);
      if (fieldsRead <= 0)
         continue;
      if (fieldsRead != 3)
      {
         fclose(in);
         return true;
      }
      data = add_tree_value(data, wavelength, chl, kc*conversionFactor);
   }

   fclose(in);

   triangulate_tree(data);
   return false;
}

float Kc::operator() (float chl, float wavelength) const
{
   return interpolate_using_tree(data, wavelength, chl, defaultValue);
}
