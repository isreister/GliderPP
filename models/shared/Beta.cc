#include <stdlib.h>
#include <stdio.h>
#include "Beta.hh"

using namespace std;

Beta::Beta (float defaultValue)
{
   data = NULL;
   this->defaultValue = defaultValue;
}

Beta::~Beta (void)
{
   if (data != NULL)
      delete_tree(data);
}

bool Beta::readFile (const char *filename, float conversionFactor)
{
   FILE *in;

   if (data != NULL)
      return true;

   float minuteOfDay;
   float depth;
   float beta;
   int hour, minute;

   // Open file and check for error
   in = fopen(filename, "r");
   if (in == NULL)
      return true;

   // Read fields until EOF
   while (!feof(in))
   {
      int fieldsRead = fscanf(in, " %d:%d %f %f ",
         &hour, &minute, &depth, &beta);
      if (fieldsRead <= 0)
         continue;
      if (fieldsRead != 4)
      {
         fclose(in);
         return true;
      }
      minuteOfDay = hour*60 + minute;
      data = add_tree_value(data, minuteOfDay, depth, beta*conversionFactor);
   }

   fclose(in);

   triangulate_tree(data);
   return false;
}

float Beta::operator() (float minute, float depth) const
{
   return interpolate_using_tree(data, minute, depth, defaultValue);
}

void Beta::clear (void)
{
   if (data != NULL)
   {
      delete_tree(data);
      data = NULL;
   }
}
