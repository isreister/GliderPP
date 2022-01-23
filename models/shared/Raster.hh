#ifndef _MODEL_RASTER_HH
#define _MODEL_RASTER_HH

namespace RasterFileType
{
   typedef enum
   {
      Uint8,
      Sint8,
      Uint16,
      Sint16,
      flt32
   } fileTypeEnum;
}

/**
 * A floating point image class with support for bilinear interpolation.
 */
class Raster
{
private:
protected:
   /// A pointer to the allocated values in memory.
   float *data;

   /// An array of pointers to contiguous values in each row of the raster.
   float **rowPointers;

   int width;  ///< The width of the raster.
   int height; ///< The height of the raster.

   float xRange;  ///< xMax-xMin.
   float xMin;    ///< The physical x value at column 0.
   float xMax;    ///< The physical x value at column (width-1).
   float yRange;  ///< xMax-xMin.
   float yMin;    ///< The physical y value at column 0.
   float yMax;    ///< The physical y value at column (height-1).

   /**
    * A protected constructor that does absolutely nothing (in case a sub-class
    *  needs to set everything up itself.
    */
   Raster (void);

   /**
    * Creates the data area and sets up the row pointers array. (used internally
    *  only).
    */
   void initData (void);
public:
   /**
    * Copies the given raster object.
    */
   Raster (const Raster &r);

   /**
    * Creates the raster with the given dimensions. The values are left
    *  uninitialised.
    * @param width The width of the raster.
    * @param height The height of the raster.
    */
   Raster (int width, int height);

   /**
    * Creates the raster with the given dimensions. The values are initialised
    *  to a value.
    * @param width The width of the raster.
    * @param height The height of the raster.
    * @param value The value to fill the raster with.
    */
   Raster (int width, int height, float value);

   /**
    * Sets values for xMin etc... @see xMin, xMax, yMin, yMax.
    * @param xMin The physical x value at column 0.
    * @param xMax The physical x value at column (width-1).
    * @param yMin The physical y value at column 0.
    * @param yMax The physical y value at column (height-1).
    */
   void setPhysicalDimensions (float xMin, float xMax, float yMin, float yMax);

   /**
    * Gets values for xMin etc... @see xMin, xMax, yMin, yMax.
    * @param xMin On return is set to the physical x value at column 0.
    * @param xMax On return is set to the physical x value at column (width-1).
    * @param yMin On return is set to the physical y value at column 0.
    * @param yMax On return is set to the physical y value at column (height-1).
    */
   void getPhysicalDimensions (float &xMin, float &xMax, float &yMin,
      float &yMax) const;

   /**
    * Clears up all memory used by the raster.
    */
   virtual ~Raster (void);

   /**
    * Returns the width of the raster.
    * @return The width of the raster.
    */
   inline int getWidth (void) { return width; }

   /**
    * Returns the height of the raster.
    * @return The height of the raster.
    */
   inline int getHeight (void) { return height; }

   /**
    * Returns the dimensions of the raster.
    * @param width On return set to the width of the raster.
    * @param height On return set to the height of the raster.
    */
   inline void getSize (int &width, int &height)
   {
      width = this->width;
      height = this->height;
   }

   /**
    * Sets all values in the raster to the given one.
    * @param value The value to set each value to.
    * @return *this.
    */
   Raster &operator= (float value);

   /**
    * Gets a bilinearly interpolated value from the raster.
    * @param x The x position in the image. It does not necessarily have to be
    *  between xMin and mMax.
    * @param y The y position in the image. It does not necessarily have to be
    *  between yMin and yMax.
    * @return The interpolated value.
    */
   float operator() (float x, float y);

   /**
    * Returns an array of values from a row of the raster. The returned array
    *  should not be deleted since it is the memory used internally by the
    *  raster object. The values may be changed and the values in the raster
    *  object will change also. This function allows for statements like the
    *  following to work: (Where raster is a Raster object)
    *  <code>
    *  raster[row][column] = 10.0f;<br>
    *  cout &lt;&lt raster[row][column] &lt&lt endl;<br>
    *  </code>
    * Note that the order of the "x" and "y" dimensions is the reverse of those
    *  used for the operator() function.
    * @param row The row to return a pointer to. It must be a value between
    *  0 and height-1 inclusive - or Magical Things May Happen.
    * @return A pointer to the beginning of a row.
    */
   inline float *operator[] (int row) { return rowPointers[row]; }

   /**
    * Loads an unsigned raw flat file into the raster. It must be of the same
    *  dimensions as the raster (or at least be the same width and at least the
    *  same height). The file can be gzipped. If the file fails to load then
    *  it is possible that part of the image has been loaded.
    * @param filename The file to load.
    * @param fileType The type of file.
    * @return false on success, true on failure.
    */
   bool readRaw (const char *filename, RasterFileType::fileTypeEnum fileType);

   /**
    * Writes an unsigned raw flat file from the raster.
    * @param filename The file to save.
    * @param fileType The type of file.
    * @param compress Set this to true to compress the file using zlib (gzip
    *  compression). Setting this does <u>not</u> alter the filename.
    * @return false on success, true on failure.
    */
   bool writeRaw (const char *filename, RasterFileType::fileTypeEnum fileType,
      bool compress) const;
};

#endif /* #ifndef _MODEL_RASTER_HH */
