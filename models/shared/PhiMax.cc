#include <stdlib.h>
#include <stdio.h>
#include "PhiMax.hh"

using namespace std;

PhiMax::PhiMax (float defaultValue)
{
   data = NULL;
   this->defaultValue = defaultValue;
}

PhiMax::~PhiMax (void)
{
   if (data != NULL)
      delete_tree(data);
}

bool PhiMax::readFile (const char *filename, float conversionFactor)
{
   FILE *in;

   if (data != NULL)
      return true;

   int hours, minutes, time;
   float depth, phiMax;

   // Open file and check for error
   in = fopen(filename, "r");
   if (in == NULL)
      return true;

   // Read fields until EOF
   while (!feof(in))
   {
      int fieldsRead = fscanf(in, " %d:%d %f %f ",
         &hours, &minutes, &depth, &phiMax);
      if (fieldsRead <= 0)
         continue;
      if (fieldsRead != 4)
      {
         fclose(in);
         return true;
      }
      time = hours*60 + minutes;
      data = add_tree_value(data, time, depth, phiMax*conversionFactor);
   }

   fclose(in);

   return false;
}

float PhiMax::operator() (int time, int depth) const
{
   return interpolate_using_tree(data, time, depth, defaultValue);
}
