#include <stdlib.h>
#include <fstream>
#include <zlib.h>

#include "Raster.hh"

using namespace std;

void Raster::initData (void)
{
   data = new float[width*height];

   rowPointers = new float *[height];
   for (int i = 0; i < height; i++)
      rowPointers[i] = data + width*i;
}

Raster::Raster (const Raster &r)
{
   this->width = r.width;
   this->height = r.height;
   int numPixels = width*height;
   initData();

   // Copy data values over
   for (int i = 0; i < numPixels; i++)
      this->data[i] = r.data[i];

   float xMin, xMax, yMin, yMax;
   r.getPhysicalDimensions(xMin, xMax, yMin, yMax);
   this->setPhysicalDimensions(xMin, xMax, yMin, yMax);
}

Raster::Raster (int width, int height)
{
   this->width = width;
   this->height = height;
   initData();
   setPhysicalDimensions (0.0f, width-1, 0.0f, height-1);
}

Raster::Raster (int width, int height, float value)
{
   this->width = width;
   this->height = height;
   initData();
   *this = value;
   setPhysicalDimensions (0.0f, width-1, 0.0f, height-1);
}

void Raster::setPhysicalDimensions (float xMin, float xMax, float yMin,
   float yMax)
{
   this->xMin = xMin;
   this->xMax = xMax;
   xRange = xMax - xMin;
   this->yMin = yMin;
   this->yMax = yMax;
   yRange = yMax - yMin;
}

void Raster::getPhysicalDimensions (float &xMin, float &xMax, float &yMin,
   float &yMax) const
{
   xMin = this->xMin;
   xMax = this->xMax;
   yMin = this->yMin;
   yMax = this->yMax;
}

Raster::~Raster (void)
{
   delete []data;
   delete []rowPointers;
}

Raster &Raster::operator= (float value)
{
   int numPixels = width*height;

   for (int i = 0; i < numPixels; i++)
      data[i] = value;

   return *this;
}

float Raster::operator() (float x, float y)
{
   float fracX, fracY;
   fracX = (x - xMin) / xRange;
   fracY = (y - yMin) / yRange;

   // in the following comments:
   //  'left' means x < xMin
   //  'right' means x > mMax
   //  'above' means y < yMin
   //  'below' means y > yMax

   // The x component is left of the image x range
   if (fracX <= 0.0f)
   {
      // The y component is above the image y range
      if (fracY <= 0.0f)
         return rowPointers[0][0];
      // The y component is below the image y range
      else if (fracY >= 1.0f)
         return rowPointers[height-1][0];
      // The y component is within the image y range
      else
      {
         int row1 = (int)((height-1)*fracY);
         int row2 = row1+1;
         float y1 = row1/(float)(height-1);
         float y2 = row2/(float)(height-1);
         float v1 = rowPointers[row1][0];
         float v2 = rowPointers[row2][0];
         float m = (v2-v1)/(y2-y1);
         return v1 + m*(fracY - y1);
      }
   }
   // The x component is right of the image x range
   else if (fracX >= 1.0f)
   {
      // The y component is above the image y range
      if (fracY <= 0.0f)
         return rowPointers[0][width-1];
      // The y component is below the image y range
      else if (fracY >= 1.0f)
         return rowPointers[height-1][width-1];
      // The y component is within the image y range
      else
      {
         int row1 = (int)((height-1)*fracY);
         int row2 = row1+1;
         float y1 = row1/(float)(height-1);
         float y2 = row2/(float)(height-1);
         float v1 = rowPointers[row1][width-1];
         float v2 = rowPointers[row2][width-1];
         float m = (v2-v1)/(y2-y1);
         return v1 + m*(fracY - y1);
      }
   }
   // The x component is within the image x range
   else
   {
      int col1 = (int)((width-1)*fracX);
      int col2 = col1+1;
      float x1 = col1/(float)(width-1);
      float x2 = col2/(float)(width-1);
      // The y component is above the image y range
      if (fracY <= 0.0f)
      {
         float v1 = rowPointers[0][col1];
         float v2 = rowPointers[0][col2];
         float m = (v2-v1)/(x2-x1);
         return v1 + m*(fracX - x1);
      }
      // The y component is below the image y range
      else if (fracY >= 1.0f)
      {
         float v1 = rowPointers[height-1][col1];
         float v2 = rowPointers[height-1][col2];
         float m = (v2-v1)/(x2-x1);
         return v1 + m*(fracX - x1);
      }
      // The y component is within the image y range
      else
      {
         int row1 = (int)((height-1)*fracY);
         int row2 = row1+1;
         float y1 = row1/(float)(height-1);
         float y2 = row2/(float)(height-1);
         float pdy = fracY - y1;
         float dy = y2-y1;
         float vtl = rowPointers[row1][col1];   // Top left
         float vtr = rowPointers[row1][col2];   // Top right
         float vbl = rowPointers[row2][col1];   // Bottom left
         float vbr = rowPointers[row2][col2];   // Bottom right
         float ml = (vtl-vbl)/dy;   // Gradient at left
         float mr = (vtr-vbr)/dy;   // Gradient at right
         float v1 = vtl + ml*pdy;   // Value at left
         float v2 = vtr + mr*pdy;   // Value at right
         float m = (v2-v1)/(x2-x1);
         return v1 + m*(fracX - x1);
      }
   }
}

bool Raster::readRaw (const char *filename,
   RasterFileType::fileTypeEnum fileType)
{
   using namespace RasterFileType;

   gzFile file;
   void *buffer;
   int numPixels = width*height;
   int bytesToRead;

   switch (fileType)
   {
      case Uint8:
         bytesToRead = numPixels * sizeof(unsigned char);
         buffer = malloc(bytesToRead);
         break;
      case Sint8:
         bytesToRead = numPixels * sizeof(signed char);
         buffer = malloc(bytesToRead);
         break;
      case Uint16:
         bytesToRead = numPixels * sizeof(unsigned short);
         buffer = malloc(bytesToRead);
         break;
      case Sint16:
         bytesToRead = numPixels * sizeof(signed short);
         buffer = malloc(bytesToRead);
         break;
      case flt32:
         bytesToRead = numPixels * sizeof(float);
         buffer = data;
         break;
      default:
         // Unknown file type.
         return 1;
   }

   if ((file = gzopen(filename, "rb")) == NULL)
      return true;

   if (gzread(file, buffer, bytesToRead) != bytesToRead)
   {
      gzclose(file);
      if (buffer != data)
         free(buffer);
      return true;
   }

   gzclose(file);

#define COPY_VALUES(type) \
{ \
   type *dest = (type *)data; \
   type *src = (type *)buffer; \
   for (int i = 0; i < numPixels; i++) \
      dest[i] = src[i]; \
}
   switch (fileType)
   {
      case Uint8:
         COPY_VALUES(unsigned char)
         break;
      case Sint8:
         COPY_VALUES(signed char)
         break;
      case Uint16:
         COPY_VALUES(unsigned short)
         break;
      case Sint16:
         COPY_VALUES(signed short)
         break;
      case flt32:
         // Values don't need to be copied 'cos we loaded it straight into the
         //  data area
         break;
   }
#undef COPY_VALUES
   if (buffer != data)
      free(buffer);

   return false;
}

bool Raster::writeRaw (const char *filename,
   RasterFileType::fileTypeEnum fileType, bool compress) const
{
   using namespace RasterFileType;

   void *buffer;
   int numPixels = width*height;
   int bytesToWrite;

   switch (fileType)
   {
      case Uint8:
         bytesToWrite = numPixels * sizeof(unsigned char);
         buffer = malloc(bytesToWrite);
         break;
      case Sint8:
         bytesToWrite = numPixels * sizeof(signed char);
         buffer = malloc(bytesToWrite);
         break;
      case Uint16:
         bytesToWrite = numPixels * sizeof(unsigned short);
         buffer = malloc(bytesToWrite);
         break;
      case Sint16:
         bytesToWrite = numPixels * sizeof(signed short);
         buffer = malloc(bytesToWrite);
         break;
      case flt32:
         bytesToWrite = numPixels * sizeof(float);
         buffer = data;
         break;
      default:
         // Unknown file type.
         return 1;
   }

#define COPY_VALUES(type) \
{ \
   type *dest = (type *)buffer; \
   type *src = (type *)data; \
   for (int i = 0; i < numPixels; i++) \
      dest[i] = src[i]; \
}
   switch (fileType)
   {
      case Uint8:
         COPY_VALUES(unsigned char)
         break;
      case Sint8:
         COPY_VALUES(signed char)
         break;
      case Uint16:
         COPY_VALUES(unsigned short)
         break;
      case Sint16:
         COPY_VALUES(signed short)
         break;
      case flt32:
         // Values don't need to be copied 'cos we are writing it straight from
         //  the data area
         break;
   }
#undef COPY_VALUES

   if (compress)
   {
      gzFile out;
      if ((out = gzopen(filename, "rb")) == NULL)
      {
         if (buffer != data)
            free(buffer);
         return true;
      }

      if (gzread(out, buffer, bytesToWrite) != bytesToWrite)
      {
         gzclose(out);
         if (buffer != data)
            free(buffer);
         return true;
      }

      gzclose(out);
   }
   else
   {
      ofstream out;
      out.open(filename, ios::out | ios::binary | ios::trunc);

      if (!out)
      {
         if (buffer != data)
            free(buffer);
         return true;
      }

      if (!out.write((char *)buffer, bytesToWrite))
      {
         out.close();
         if (buffer != data)
            free(buffer);
         return true;
      }

      out.close();
   }

   if (buffer != data)
      free(buffer);

   return false;
}
