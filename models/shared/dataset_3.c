/* dataset_3.c
 * 
 * A module defining the data structures and functions for dealing
 *  with a data structure stores x/y/z/value data and interpolates them.
 */

#include <stdio.h>
#include <stdlib.h>

#include "dataset_3.h"
#include "shared_interpolate.h"

/* Function to delete a dataset_3.
 */
void dataset_3_delete (dataset_3 *root) {
   dataset_3 *cur = root;
   dataset_3 *next;
   
   while (cur != NULL) {
      next = cur->next;
      
      delete_tree(cur->data);
      
      free(cur);
      
      cur = next;
   }
}

/* Function to create a dataset node.
 */
static dataset_3 *create_dataset_3 (PositionType position) {
   dataset_3 *retval = (dataset_3 *)malloc(sizeof(dataset_3));
   
   if (retval == NULL) {
      perror(NULL);
      exit(1);
   }
   
   retval->position = position;
   
   retval->next = NULL;
   
   retval->data = NULL;
   
   return retval;
}

/* Function to add an item to a tree. The (possibly new) root node in the 
 *  tree will be returned.
 */
dataset_3 *dataset_3_add_value (dataset_3 *root,
   PositionType x, PositionType y, PositionType z, ValueType value) {
   
   /* A pointer to which tree to add the value into */
   tree **destTree = NULL;
   
   if (root != NULL) {
      /* Variables to iterate over the 'top' of the structure (to find a
       *  node or two with the required position(s) ) */
      dataset_3 *cur = root;
      dataset_3 *prev = NULL;
      /* Find a node at the head of a list of y-values. (for the same x) */
      while (cur != NULL) {
         if (x == cur->position) {
            /* The new data belongs on the current item's list */
            destTree = &(cur->data);
            break;
         } else if (x < cur->position) {
            /* Insert the new data before the current item (new x) */
            dataset_3 *newNode = create_dataset_3(x);
            
            if (prev != NULL) {
               prev->next = newNode;
            } else {
               /* The new node becomes the root node */
               root = newNode;
            }
            newNode->next = cur;
            
            destTree = &(newNode->data);
            break;
         }
         prev = cur;
         cur = cur->next;
      }
      if (destTree == NULL) {
         /* The new item belongs on the end of the tree */
         dataset_3 *newNode = create_dataset_3(x);
         prev->next = newNode;
         destTree = &(newNode->data);
      }
   } else {
      /* Tree is empty */
      root = create_dataset_3(x);
      destTree = &(root->data);
   }
   
   *destTree = add_tree_value(*destTree, y, z, value);
   
   return root;
}

ValueType dataset_3_get_value (const dataset_3 *root,
   PositionType x, PositionType y, PositionType z, ValueType def) {
   
   if (root != NULL) {
      /* Variables to iterate over the 'top' of the structure (to find an x) */
      const dataset_3 *cur;
      const dataset_3 *prev;
      
      if (x < root->position) {
         /* If the required x position is off the 'left' of the dataset, just
          *  interpolate from the left side */
         return interpolate_using_tree(root->data, y, z, def);
      }
      
      /* Find a node at the head of a list of y-values. (for the same x) */
      prev = root;
      cur = prev->next;
      while (cur != NULL) {
         if (x < cur->position) {
            ValueType leftVal, rightVal;
            
            leftVal = interpolate_using_tree(prev->data, y, z, def);
            rightVal = interpolate_using_tree(cur->data, y, z, def);
            
            return interpolate_1(x,
               prev->position, leftVal,
               cur->position, rightVal);
         } else if (x == cur->position) {
            /* The wanted data position is in the current item's data */
            return interpolate_using_tree(cur->data, y, z, def);
         }
         prev = cur;
         cur = cur->next;
      }
      
      /* The required x position is off the 'right' of the tree, just
       *  interpolate from the right side */
      return interpolate_using_tree(prev->data, y, z, def);
   } else {
      /* Tree is empty, return default value */
      return def;
   }
}

/* Prints out the tree structure on stdout.
 */
void print_dataset_3 (const dataset_3 *root) {
   /* Variable to iterate along the 'top' of the structure (x) */
   const dataset_3 *cur = root;
   
   cur = root;
   while (cur != NULL) {
      printf("(%4g: ", cur->position);
      print_tree(cur->data);
      printf(")\n     V\n");
      cur = cur->next;
   }
}
