#include <stdio.h>

#include <stdlib.h>
#include "Ed.hh"

using namespace std;

Ed::Ed (float defaultEdValue, float defaultMu0Value)
{
   edData = NULL;
   mu0Data = NULL;

   defaultEd = defaultEdValue;
   defaultMu0 = defaultMu0Value;
   firstMinute = 0;
   lastMinute = 0;
}

Ed::~Ed (void)
{
   if (edData != NULL)
      delete_tree(edData);
   if (mu0Data != NULL)
      delete_tree(mu0Data);
}

bool Ed::readFile (const char *filename, float edConversionFactor,
      float mu0ConversionFactor)
{
   FILE *in;

   if (edData != NULL)
      return true;

   int hour, minute, minuteOfDay;
   float wavelength;
   float ed;
   float mu0;
   bool minSet = false;

   // Open file and check for error
   in = fopen(filename, "r");
   if (in == NULL)
      return true;

   // Read fields until EOF
   while (!feof(in))
   {
      int fieldsRead = fscanf(in, " %d:%d %f %f %f ", &hour, &minute,
         &wavelength, &ed, &mu0);
      if (fieldsRead <= 0)
         continue;
      if (fieldsRead != 5)
      {
         fclose(in);
         return true;
      }
      minuteOfDay = hour*60 + minute;
      edData = add_tree_value(edData, minuteOfDay, wavelength,
         ed*edConversionFactor);
      mu0Data = add_tree_value(mu0Data, minuteOfDay, wavelength,
         mu0*mu0ConversionFactor);
      if (!minSet)
      {
         firstMinute = minuteOfDay;
         lastMinute = minuteOfDay;
         minSet = true;
      }
      if (minuteOfDay < firstMinute)
         firstMinute = minuteOfDay;
      if (minuteOfDay > lastMinute)
         lastMinute = minuteOfDay;
   }

   fclose(in);

   triangulate_tree(edData);
   triangulate_tree(mu0Data);
   return false;
}

float Ed::operator() (int minute, float wavelength) const
{
   return interpolate_using_tree(edData, minute, wavelength, defaultEd);
}

float Ed::getMu0 (int minute, float wavelength) const
{
   return interpolate_using_tree(mu0Data, minute, wavelength, defaultMu0);
}
