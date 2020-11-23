#include <stdlib.h>
#include <stdio.h>
#include "Ab.hh"

using namespace std;

Ab::Ab (float defaultValue)
{
   data = NULL;
   this->defaultValue = defaultValue;
}

Ab::~Ab (void)
{
   if (data != NULL)
      delete_tree(data);
}

bool Ab::readFile (const char *filename, float conversionFactor)
{
   FILE *in;

   if (data != NULL)
      return true;

   float depth;
   float wavelength;
   float a, b;

   // Open file and check for error
   in = fopen(filename, "r");
   if (in == NULL)
      return true;

   // Read fields until EOF
   while (!feof(in))
   {
      int fieldsRead = fscanf(in, "%f %f %f %f", &depth, &wavelength, &a, &b);
      if (fieldsRead <= 0)
         continue;
      if (fieldsRead != 4)
      {
         fclose(in);
         return true;
      }
      data = add_tree_value(data, depth, wavelength, (b/a)*conversionFactor);
   }

   fclose(in);

   triangulate_tree(data);
   return false;
}

float Ab::operator() (float depth, float wavelength) const
{
   return interpolate_using_tree(data, depth, wavelength, defaultValue);
}
