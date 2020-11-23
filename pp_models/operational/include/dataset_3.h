/* dataset_3.h
 * 
 * A module defining the data structures and functions for dealing
 *  with a data structure stores x/y/z/value data and interpolates them.
 */

#ifndef _DATASET_3
#define _DATASET_3

#include "shared_types.h"
#include "shared_tree.h"

#ifdef __cplusplus
extern "C" {
#endif /* __cplusplus */

/**
 * A node for storing a three-dimensional linked structure,
 *  where a value is recorded for given x, y and z 'position'.
 */
typedef struct dataset_3_struct {
   /** The position of the node. */
   PositionType position;
   
   /** A pointer to the next node when traversing nodes. */
   struct dataset_3_struct *next;
   
   /** A tree, which allows interpolation in 2 dimensions */
   tree *data;
} dataset_3;

/**
 * Deletes a dataset and all nodes in it.
 * @param root The root node of the dataset. It can be NULL in which case
 *  this function does nothing and returns.
 */
void dataset_3_delete (dataset_3 *root);

/**
 * Adds a value to a dataset.
 * @param root The root node of the dataset. It can be NULL in which case the
 *  function creates the tree.
 * @param x The x location of the value.
 * @param y The y location of the value.
 * @param value The value at the x,y location.
 * @return The root of the tree. It is important for the caller to update its
 *  root pointer to this return value. e.g.<br>
 * <code>
 * dataset_3 *root = NULL;<br>
 *  ...<br>
 * root = dataset_3_add_value(root, 10.2, 15.5, 53.2, 134.56);
 * </code>
 */
dataset_3 *dataset_3_add_value (dataset_3 *root,
   PositionType x, PositionType y, PositionType z, ValueType value);

/**
 * Produces an interpolated value from the tree.
 * @param root The root node of the tree to use.
 * @param x The x location of the point to calculate the value at.
 * @param y The y location of the point to calculate the value at.
 * @param def The default value to return. This is returned if root is NULL - 
 *  i.e. the tree is empty and it has no other value to return.
 * @return The interpolated value, or def if the tree is empty.
 */
ValueType dataset_3_get_value (const dataset_3 *root,
   PositionType x, PositionType y, PositionType z, ValueType def);

/**
 * Prints out the dataset structure on stdout. Mostly here for debugging
 *  purposes so that programs can quickly print out the data they actually
 *  have loaded and the structure that the tree has taken.
 * @param root The root node of the dataset to display.
 */
void print_dataset_3 (const dataset_3 *root);

#ifdef __cplusplus
}
#endif /* __cplusplus */

#endif /* #ifndef _DATASET_3 */
