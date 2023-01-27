/*
 * Module  : shared_vector.c
 * Author  : John Beisley
 * Version : 1.1
 * Date    : 02/07/01
 *
 * An implementation of a dynamic array. Similar in function to Java's
 *  java.util.Vector class.
 */

#include <stdio.h>
#include <stdlib.h>
#include "shared_vector.h"

#define INITIAL_CAPACITY      10
#define CAPACITY_INCREMENT    10

static int set_capacity (vector_t *vector, size_t capacity) {
   if (vector->vector == NULL) {
      vector->vector = malloc(sizeof(void *)*capacity);
   } else {
      vector->vector = realloc(vector, sizeof(void *)*capacity);
   }
   
   if (vector->vector == NULL) {
      return 1;
   }
   
   vector->capacity = capacity;
   
   return 0;
}

/* Creates an empty vector and returns it. If the space couldn't be allocated then
 *  NULL is returned. */
extern vector_t *vector_create (void) {
   vector_t *vector = (vector_t *)malloc(sizeof(vector_t));
   
   if (vector == NULL) {
      return NULL;
   }
   
   vector->vector = NULL;
   if (set_capacity(vector, INITIAL_CAPACITY)) {
      free(vector);
      return NULL;
   }
   vector->size = 0;
   
   return vector;
}

/* Deallocates the vector. The items inside the vector are not deallocated.
 * vector - The vector to deallocate.
 */
extern void vector_free (vector_t *vector) {
   free(vector);
}

/* Deallocates the items in the vector using free() from <stdlib.h>. The vector
 *  itself is not deallocated.
 * vector - The vector from which to deallocate the items.
 */
extern void vector_free_items (vector_t *vector) {
   int i;
   void **cur = vector->vector;
   
   for (i = 0; i < vector->size; i++) {
      if (*cur != NULL) {
         free(*cur);
      }
      cur++;
   }
   
   vector->size = 0;
}

/* Empties the vector without deallocating the items in it.
 * vector - The vector to empty.
 */
extern void vector_empty (vector_t *vector) {
   vector->size = 0;
}

/* Adds an item to the end of a vector. Returns non-zero if there was not
 *  enough memory.
 * vector - The vector to add the item to.
 * o - The item to add.
 */
extern int vector_add (vector_t *vector, void *o) {
   if (vector->capacity == vector->size) {
      if (set_capacity(vector, vector->capacity+CAPACITY_INCREMENT)) {
         return 1;
      }
   }
   
   vector->vector[vector->size] = o;
   vector->size++;
   
   return 0;
}

/* Inserts an item into a vector, shunting items to retain order. Returns
 *  non-zero if there was not enough memory or the index was out of range.
 * vector - The vector to add the item to.
 * o - The item to add.
 * index - The index that the item should be inserted at.
 */
extern int vector_insert (vector_t *vector, void *o, int index) {
   int i;
   
   if (index < 0 || index >= vector->size) {
      return -2;
   }
   
   if (vector->capacity == vector->size) {
      if (set_capacity(vector, vector->capacity+CAPACITY_INCREMENT)) {
         return -1;
      }
   }
   
   vector->size++;
   
   /* Shunt items */
   for (i = vector->size-1; i > index; i--) {
      vector->vector[i] = vector->vector[i-1];
   }
   
   /* Insert item */
   vector->vector[index] = o;
   
   return 0;
}

/* Removes an item from a vector, shunting items to retain order. The
 *  item is returned, or NULL is returned if index is out of range.
 * vector - The vector to remove item from.
 * index - The index that the item should be removed from.
 */
extern void *vector_remove_index (vector_t *vector, int index) {
   int i;
   void *o;
   
   if (index < 0 || index >= vector->size) {
      return NULL;
   }
   
   o = vector->vector[index];
   
   vector->size--;
   
   /* Shunt items */
   for (i = index; i < vector->size; i++) {
      vector->vector[i] = vector->vector[i+1];
   }
   
   return o;
}

/* Removes an item from a vector, shunting items to retain order. If the
 *  item is not in the vector then non-zero is returned, otherwise zero is
 *  returned to indicate success.
 * vector - The vector to remove item from.
 * o - The item to remove.
 */
extern int vector_remove (vector_t *vector, void *o) {
   int index = vector_index_of(vector, o);
   
   if (index >= 0) {
      return (vector_remove_index(vector,index)==NULL);
   }
   
   return -1;
}

/* Retrieves an item from a vector. (if the given index is out of bounds then
 *  NULL is returned.
 * vector - The vector to retrieve the item from.
 * index - A zero based index into the vector.
 * returns the item at the given index.
 */
extern void *vector_get (vector_t *vector, int index) {
   if (index < 0 || index >= vector->size) {
      return NULL;
   }
   
   return vector->vector[index];
}

/* Replaces an item in a vector. (if the given index is out of bounds then
 *  NULL is returned.
 * vector - The vector to replace the item in.
 * o - The item to put in the index.
 * index - A zero based index into the vector.
 * returns the original item at the given index.
 */
extern void *vector_set (vector_t *vector, void *o, int index) {
   void *tmp;
   
   if (index < 0 || index >= vector->size) {
      return NULL;
   }
   
   tmp = vector->vector[index];
   vector->vector[index] = o;
   
   return tmp;
}

/* Returns the lowest index of the specified item in the vector. If not found
 *  then returns -1.
 * vector - The vector to search for the item in.
 * o - The item to search for.
 */
extern int vector_index_of (vector_t *vector, void *o) {
   int i;
   
   for (i = 0; i < vector->size; i++) {
      if (vector->vector[i] == o) {
         return i;
      }
   }
   
   return -1;
}

/* Returns the number of items in the vector.
 * vector - The vector to return the size of.
 */
extern int vector_size (const vector_t *vector) {
   return vector->size;
}
