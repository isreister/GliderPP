#include <stdlib.h>
#include <stdio.h>
#include "Aph.hh"

using namespace std;

static int readLine (FILE *in, char **buf, int *bufLenPtr)
{
   int chr;
   char *bufPos = *buf;
   int lineLen = 0;
   
   if (*buf == NULL) {
      *bufLenPtr = 0;
   }
   
   while (true) {
      chr = fgetc(in);
      
      // Increase buffer size if needed
      if ((lineLen+2) > (*bufLenPtr)) {
         // Increase size of buffer by 64 chars 
         *bufLenPtr += 64;
         *buf = (char *)realloc(*buf, (*bufLenPtr)*sizeof(char));
         bufPos = *buf + lineLen;
      }
      
      lineLen++;
      if (chr == '\n' || chr == EOF) {
         // Terminate the buffer string
         *bufPos = '\0';
         return chr;
      } else {
         // Append the read char into the buffer
         *(bufPos++) = (char)chr;
      }
      
      // Upper limit of 1kb on line length
      if (lineLen > 1024) {
         // Terminate the buffer string
         *bufPos = '\0';
         return chr;
      }
   }
}

Aph::Aph (float defaultValue)
{
   data = NULL;
   this->defaultValue = defaultValue;
}

Aph::~Aph (void)
{
   if (data != NULL)
      dataset_3_delete(data);
}

bool Aph::readFile (const char *filename, float conversionFactor)
{
   FILE *in;
   char *lineBuf = NULL;
   int lineBufLen = 0;
   
   float *depths = NULL;
   int depths_length = 0;
   int num_depths;
   
   int hours, minutes, time;
   int itemsRead = 0;
   
   try
   {
      // Open file and check for error
      in = fopen(filename, "r");
      if (in == NULL)
         throw 1;
      
      while (!feof(in))
      {
         int fieldsRead, numChars;
         char *linePos;
         
         // Read a line - should contain time, if it is not present
         //  then the file is finished being read
         if (readLine (in, &lineBuf, &lineBufLen) == EOF)
            break;
         
         // Read Time
         fieldsRead = sscanf(lineBuf, "%d:%d", &hours, &minutes);
         if (fieldsRead != 2) {
            // Time not present, assume midnight
            time = 0;
         } else {
            time = hours*60 + minutes;
            
            // Read a line - should contain depth headers
            if (readLine (in, &lineBuf, &lineBufLen) == EOF)
               throw 1;
         }
         
         // Skip any leading non-number field header
         linePos = lineBuf;
         sscanf(linePos, "%*[^0-9.]%n", &numChars);
         linePos += numChars;
         
         // Read depth headers, rellocating depths as necessary.
         //  Stop reading when newline reached.
         num_depths = 0;
         while (true)
         {
            // Increase the size of the depths[] array if needed
            if (num_depths>=depths_length)
            {
               float *newDepths;
               depths_length = num_depths + 32;
               newDepths = (float *)realloc(depths,
                  sizeof(float)*depths_length);
               if (newDepths == NULL)
               {
                  // Error allocating memory for depths
                  throw 1;
               }
               depths = newDepths;
            }
            
            if (sscanf(linePos, "%f%n", depths+num_depths,
               &numChars) < 1)
            {
               // Ran out of depth headers - we're finished with this loop
               break;
            }
            linePos += numChars;
            
            num_depths++;
         }
         
         // Read per-wavelength lines until blank line field or EOF
         while (true)
         {
            float wavelength;
            
            if (readLine (in, &lineBuf, &lineBufLen) == EOF)
               break;
            linePos = lineBuf;
            
            if (sscanf(linePos, "%f%n", &wavelength, &numChars) < 1) {
               // Ran out of wavelength lines
               break;
            }
            linePos += numChars;
            
            // Read num_depths number of aph values
            for (int i = 0; i < num_depths; i++)
            {
               float aph;
               if (sscanf(linePos, "%f%n", &aph, &numChars) < 1)
               {
                  // File format error
                  throw 1;
               }
               linePos += numChars;
               
               data = dataset_3_add_value(data,
                  time, depths[i], wavelength, aph*conversionFactor);
               itemsRead++;
            }
         }
      }
      
      // Did we actually read any data? If not say file format error
      if (itemsRead == 0)
         throw 1;
   }
   catch (int e)
   {
      // File format error or file could not be opened if we are here
      if (in != NULL) fclose(in);
      if (depths != NULL) free(depths);
      if (lineBuf != NULL) free(lineBuf);
      return true;
   }
   
   fclose(in);
   free(depths);
   return false;
}

float Aph::operator() (int time, float depth, float wavelength) const
{
   return dataset_3_get_value(data,
      time, depth, wavelength, defaultValue);
}
