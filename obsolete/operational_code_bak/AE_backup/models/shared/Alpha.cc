#include <stdlib.h>
#include <stdio.h>
#include "Alpha.hh"

using namespace std;

Alpha::Alpha (float defaultValue)
{
   data = NULL;
   this->defaultValue = defaultValue;
}

Alpha::~Alpha (void)
{
   if (data != NULL)
      delete_tree(data);
}

bool Alpha::readFile (const char *filename, float conversionFactor)
{
   FILE *in;

   if (data != NULL)
      return true;

   float minuteOfDay;
   float depth;
   float alpha;
   int hour, minute;

   // Open file and check for error
   in = fopen(filename, "r");
   if (in == NULL)
      return true;

   // Read fields until EOF
   while (!feof(in))
   {
      int fieldsRead = fscanf(in, " %d:%d %f %f ",
         &hour, &minute, &depth, &alpha);
      if (fieldsRead <= 0)
         continue;
      if (fieldsRead != 4)
      {
         fclose(in);
         return true;
      }
      minuteOfDay = hour*60 + minute;
      data = add_tree_value(data, minuteOfDay, depth, alpha*conversionFactor);
   }

   fclose(in);

   triangulate_tree(data);
   return false;
}

float Alpha::operator() (float minute, float depth) const
{
   return interpolate_using_tree(data, minute, depth, defaultValue);
}

void Alpha::clear (void)
{
   if (data != NULL)
   {
      delete_tree(data);
      data = NULL;
   }
}
