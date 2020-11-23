/*
 * Module  : shared_vector.h
 * Author  : John Beisley
 * Version : 1.3
 * Date    : 02/09/04
 *
 * An implementation of a dynamic array. Similar in function to Java's
 *  java.util.Vector class.
 */

#ifndef _GENERAL_VECTOR
#define _GENERAL_VECTOR

#ifdef __cplusplus
extern "C" {
#endif /* __cplusplus */

/**
 * A node in a linked vector of items
 */
typedef struct {
   void **vector;    /**< An array of items. */
   int size;         /**< A count of the items in the vector. */
   int capacity;     /**< The maximum number of items that can be stored before
                      *    the size of vector must be increased. */
} vector_t;

/**
 * Creates an empty vector and returns it. If the space couldn't be allocated
 *  then NULL is returned.
 * @return The newly created empty vector, or NULL on failure.
 */
extern vector_t *vector_create (void);

/**
 * Deallocates the vector. The items inside the vector are not deallocated.
 * @param vector The vector to deallocate.
 */
extern void vector_free (vector_t *vector);

/**
 * Deallocates the items in the vector using free() from <stdlib.h>. The vector
 *  itself is not deallocated.
 * @param vector The vector from which to deallocate the items.
 */
extern void vector_free_items (vector_t *vector);

/**
 * Empties the vector without deallocating the items in it.
 * @param vector The vector to empty.
 */
extern void vector_empty (vector_t *vector);

/**
 * Adds an item to the end of a vector. Returns non-zero if there was not
 *  enough memory.
 * @param vector The vector to add the item to.
 * @param o The item to add.
 */
extern int vector_add (vector_t *vector, void *o);

/**
 * Inserts an item into a vector, shunting items to retain order. Returns
 *  non-zero if there was not enough memory or the index was out of range.
 * @param vector The vector to add the item to.
 * @param o The item to add.
 * @param index The index that the item should be inserted at.
 */
extern int vector_insert (vector_t *vector, void *o, int index);

/**
 * Removes an item from a vector, shunting items to retain order. The
 *  item is returned, or NULL is returned if index is out of range.
 * @param vector The vector to remove item from.
 * @param index The index that the item should be removed from.
 * @return The item that was removed, or NULL if no item was removed.
 */
extern void *vector_remove_index (vector_t *vector, int index);

/**
 * Removes an item from a vector, shunting items to retain order. If the
 *  item is not in the vector then non-zero is returned, otherwise zero is
 *  returned to indicate success.
 * @param vector The vector to remove item from.
 * @param o The item to remove.
 * @return Zero on successful removal, non-zero if the item was not present.
 */
extern int vector_remove (vector_t *vector, void *o);

/**
 * Retrieves an item from a vector. (if the given index is out of bounds then
 *  NULL is returned.
 * @param vector The vector to retrieve the item from.
 * @param index A zero based index into the vector.
 * @return The item at the given index.
 */
extern void *vector_get (vector_t *vector, int index);

/**
 * Replaces an item in a vector. (if the given index is out of bounds then
 *  NULL is returned.
 * @param vector The vector to replace the item in.
 * @param o The item to put in the index.
 * @param index A zero based index into the vector.
 * @return The original item at the given index.
 */
extern void *vector_set (vector_t *vector, void *o, int index);

/**
 * Returns the lowest index of the specified item in the vector. If not found
 *  then returns -1.
 * @param vector The vector to search for the item in.
 * @param o The item to search for.
 * @return The lowest index of the item, or -1 if the item is not present.
 */
extern int vector_index_of (vector_t *vector, void *o);

/**
 * Returns the number of items in the vector.
 * @param vector The vector to return the size of.
 * @return The number of items in the vector.
 */
extern int vector_size (const vector_t *vector);

#ifdef __cplusplus
}
#endif /* __cplusplus */

#endif /* #ifndef _GENERAL_VECTOR */
