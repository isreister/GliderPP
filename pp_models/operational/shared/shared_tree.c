/* shared_tree.c
 * 
 * A module defining the data structures and functions for dealing
 *  with a binary tree that stores x/y/value data.
 *  The tree branches to the 'right' are in order of increasing x,
 *  and the tree branches 'downwards' are in order of increasing y.
 *  This is not a strict binary tree as there are many interconnections
 *  making a triangulated grid structure.
 *
 * e.g. (interconnections not shown)
 *       x ---->
 *
 *   y  r->o->o->o
 *   |  |  |     |
 *   |  V  V     V
 *   |  o  o     o
 *   V  |
 *      V
 *      o
 *
 * (r=root node, o=general node)
 *
 * Latest modification: 00/10/26
 */

#include <stdio.h>
#include <stdlib.h>

#include "shared_tree.h"
#include "shared_interpolate.h"

/* Function to delete a tree.
 */
void delete_tree (tree *root) {
   tree *cur_head = root;
   tree *next_head;
   
   while (cur_head != NULL) {
      next_head = cur_head->next;
      
      delete_list(cur_head->list);
      
      free(cur_head);
      
      cur_head = next_head;
   }
}

/* Function to create a tree node.
 */
static tree *create_tree (PositionType position) {
   tree *retval = (tree *)malloc(sizeof(tree));
   
   if (retval == NULL) {
      perror(NULL);
      exit(1);
   }
   
   retval->position = position;
   
   retval->next = NULL;
   
   retval->list = NULL;
   
   return retval;
}

/* Function to add an item to a tree. The (possibly new) root node in the 
 *  tree will be returned.
 */
tree *add_tree_value (tree *root,
   PositionType x, PositionType y, ValueType value) {
   
   /* A pointer to which list to add the value into */
   node **destList = NULL;
   
   if (root != NULL) {
      /* Variables to iterate over the 'top' of the structure (to find an x) */
      tree *cur = root;
      tree *prev = NULL;
      
      /* Find a node at the head of a list of y-values. (for the same x) */
      while (cur != NULL) {
         if (x == cur->position) {
            /* The new data belongs on the current item's list */
            destList = &(cur->list);
            break;
         } else if (x < cur->position) {
            /* Insert the new data before the current item (new x) */
            tree *newTree = create_tree(x);
            
            if (prev != NULL) {
               prev->next = newTree;
            } else {
               /* The new node becomes the root node */
               root = newTree;
            }
            newTree->next = cur;
            
            destList = &(newTree->list);
            break;
         }
         prev = cur;
         cur = cur->next;
      }
      if (destList == NULL) {
         /* The new item belongs on the end of the tree */
         tree *newTree = create_tree(x);
         prev->next = newTree;
         destList = &(newTree->list);
      }
   } else {
      /* Tree is empty */
      root = create_tree(x);
      destList = &(root->list);
   }
   
   *destList = add_list_value(*destList, y, value);
   
   return root;
}

/* This function is used to make the points stored into a triangulated
 *  grid. It must be called _after_ all the points have been added, and
 *  before any values are interpolated from the grid. This function makes
 *  lots of cross-branches in the tree.
 */
void triangulate_tree (tree *root) {
}

ValueType interpolate_using_tree (const tree *root,
   PositionType x, PositionType y, ValueType def) {
   
   if (root != NULL) {
      /* Variables to iterate over the 'top' of the structure (to find an x) */
      const tree *cur;
      const tree *prev;
      
      if (x < root->position) {
         /* If the required x position is off the 'left' of the tree, just
          *  interpolate from the left column */
         return interpolate_using_list(root->list, y, def);
      }
      
      /* Find a node at the head of a list of y-values. (for the same x) */
      prev = root;
      cur = prev->next;
      while (cur != NULL) {
         if (x < cur->position) {
            ValueType leftVal, rightVal;
            
            leftVal = interpolate_using_list(prev->list, y, def);
            rightVal = interpolate_using_list(cur->list, y, def);
            
            return interpolate_1(x,
               prev->position, leftVal,
               cur->position, rightVal);
         } else if (x == cur->position) {
            /* The wanted data position is on the current item's list */
            return interpolate_using_list(cur->list, y, def);
         }
         prev = cur;
         cur = cur->next;
      }
      
      /* The required x position is off the 'right' of the tree, just
       *  interpolate from the right column */
      return interpolate_using_list(prev->list, y, def);
   } else {
      /* Tree is empty, return default value */
      return def;
   }
}

/* Prints out the tree structure on stdout. Mostly for debugging purposes.
 *  unlike the conceptial view shown in the diagram at the top of this
 *  file, the y increases to the right, and x increases downwards.
 */
void print_tree (const tree *root) {
   /* Variable to iterate along the 'top' of the structure (x) */
   const tree *cur = root;
   
   cur = root;
   while (cur != NULL) {
      printf("(%4g: ", cur->position);
      print_list(cur->list);
      printf(")\n     V\n");
      cur = cur->next;
   }
}
