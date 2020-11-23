#include <stdlib.h>
#include <stdio.h>
#include "Chl.hh"

using namespace std;

Chl::Chl (float defaultValue)
{
   data = NULL;
   this->defaultValue = defaultValue;
}

Chl::~Chl (void)
{
   if (data != NULL)
      delete_tree(data);
}

bool Chl::readFile (const char *filename, float conversionFactor)
{
   FILE *in;

   if (data != NULL)
      return true;

   float minuteOfDay;
   float depth;
   float chl;
   int hour, minute;

   // Open file and check for error
   in = fopen(filename, "r");
   if (in == NULL)
      return true;

   // Read fields until EOF
   while (!feof(in))
   {
      int fieldsRead = fscanf(in, " %d:%d %f %f ",
         &hour, &minute, &depth, &chl);
      if (fieldsRead <= 0)
         continue;
      if (fieldsRead != 4)
      {
         fclose(in);
         return true;
      }
      minuteOfDay = hour*60 + minute;
      data = add_tree_value(data, minuteOfDay, depth, chl*conversionFactor);
   }

   fclose(in);

   triangulate_tree(data);
   return false;
}

float Chl::operator() (float minute, float depth) const
{
   return interpolate_using_tree(data, minute, depth, defaultValue);
}

void Chl::clear (void)
{
   if (data != NULL)
   {
      delete_tree(data);
      data = NULL;
   }
}
