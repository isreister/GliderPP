#include <stdlib.h>
#include <stdio.h>
#include "Pbm.hh"

using namespace std;

Pbm::Pbm (float defaultValue)
{
   data = NULL;
   this->defaultValue = defaultValue;
}

Pbm::~Pbm (void)
{
   if (data != NULL)
      delete_tree(data);
}

bool Pbm::readFile (const char *filename, float conversionFactor)
{
   FILE *in;

   if (data != NULL)
      return true;

   float minuteOfDay;
   float depth;
   float pbm;
   int hour, minute;

   // Open file and check for error
   in = fopen(filename, "r");
   if (in == NULL)
      return true;

   // Read fields until EOF
   while (!feof(in))
   {
      int fieldsRead = fscanf(in, " %d:%d %f %f ",
         &hour, &minute, &depth, &pbm);
      if (fieldsRead <= 0)
         continue;
      if (fieldsRead != 4)
      {
         fclose(in);
         return true;
      }
      minuteOfDay = hour*60 + minute;
      data = add_tree_value(data, minuteOfDay, depth, pbm*conversionFactor);
   }

   fclose(in);

   triangulate_tree(data);
   return false;
}

float Pbm::operator() (float minute, float depth) const
{
   return interpolate_using_tree(data, minute, depth, defaultValue);
}

void Pbm::clear (void)
{
   if (data != NULL)
   {
      delete_tree(data);
      data = NULL;
   }
}
