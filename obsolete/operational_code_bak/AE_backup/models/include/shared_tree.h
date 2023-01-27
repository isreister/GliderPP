/* shared_tree.h
 * 
 * A module defining the data structures and functions for dealing
 *  with a data structure stores x/y/value data and interpolates them.
 *  It used to be in the form of a tree, but is now a list of interpolating
 *  lists.
 *  The tree branches to the 'right' are in order of increasing x,
 *  and the tree branches 'downwards' are in order of increasing y.
 *
 *       next ---->
 *
 *   valuesList      r->o->o
 *   |               |  |  |
 *   V               V  V  V
 *   listNext        l  l  l
 *   |               |
 *   |               V
 *   V               l
 *         
 * (r=root node, o=general node, l=list node)
 *
 * Latest modification: 00/10/26
 */

#ifndef _SHARED_TREE
#define _SHARED_TREE

#include "shared_types.h"
#include "shared_list.h"

#ifdef __cplusplus
extern "C" {
#endif /* __cplusplus */

/**
 * A node for storing a two-dimensional linked structure of data (a tree),
 *  where a value is recorded for given x and y 'position'.
 */
typedef struct tree_struct {
   /** The position of the node. */
   PositionType position;
   
   /** A pointer to the next node when traversing nodes. */
   struct tree_struct *next;
   
   /** A list, which allows interpolation in 1 dimension */
   node *list;
} tree;

/**
 * Deletes a tree and all nodes in it.
 * @param root The root node of the tree. It can be NULL in which case this
 *  function does nothing and returns.
 */
void delete_tree (tree *root);

/**
 * Adds a value to a tree.
 * @param root The root node of the tree. It can be NULL in which case the
 *  function creates the tree.
 * @param x The x location of the value.
 * @param y The y location of the value.
 * @param value The value at the x,y location.
 * @return The root of the tree. It is important for the caller to update its
 *  root pointer to this return value. e.g.<br>
 * <code>
 * tree *root = NULL;<br>
 *  ...<br>
 * root = add_tree_value(root, 10.2, 15.5, 134.56);
 * </code>
 */
tree *add_tree_value (tree *root, PositionType x, PositionType y,
   ValueType value);

/**
 * Readies the tree for producing interpolated values. This <em>must</em> be
 *  called before using interpolate_using_tree().
 * @param root The root node of the tree to triangulate.
 * @deprecated This function is no longer required to be called. It now does
 *  nothing.
 */
void triangulate_tree (tree *root);

/**
 * Produces an interpolated value from the tree.
 * @param root The root node of the tree to use.
 * @param x The x location of the point to calculate the value at.
 * @param y The y location of the point to calculate the value at.
 * @param def The default value to return. This is returned if root is NULL - 
 *  i.e. the tree is empty and it has no other value to return.
 * @return The interpolated value, or def if the tree is empty.
 */
ValueType interpolate_using_tree (const tree *root,
   PositionType x, PositionType y, ValueType def);

/**
 * Prints out the tree structure on stdout. Mostly here for debugging purposes
 *  so that programs can quickly print out the data they actually have loaded
 *  and the structure that the tree has taken. Y increases along a line, and x
 *  increases on each subsequent line.
 * @param root The root node of the tree to display.
 */
void print_tree (const tree *root);

#ifdef __cplusplus
}
#endif /* __cplusplus */

#endif /* #ifndef _SHARED_TREE */
