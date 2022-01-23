/* shared_list.c
 * 
 *   A module defining the data structures and functions for dealing
 *  with a (sorted) linked-list that stores (time or wavelength)/value data.
 *  The list is ordered with increasing time/wavelength value.
 *
 * Latest modification: 00/10/26
 */

#include <stdlib.h>
#include <stdio.h>

#include "shared_list.h"
#include "shared_interpolate.h"

/* Function to delete a linked list.
 */
void delete_list (node *head) {
   node *cur = head;
   node *next;
   
   while (cur != NULL) {
      next = cur->next;
      free(cur);
      cur = next;
   }
}

/* Function to create a linked-list node.
 */
static node *create_node (PositionType position, ValueType value) {
   node *retval = (node *)malloc(sizeof(node));
   
   if (retval == NULL) {
      perror(NULL);
      exit(1);
   }
   
   retval->position = position;
   retval->value = value;
   retval->next = NULL;
   return retval;
}

/* Function to add an item to a linked-list. The (possibly new) head node in the 
 *  list will be returned.
 */
node *add_list_value (node *head, PositionType position, ValueType value) {
   node *cur = head;
   node *prev = NULL;
   node *tmp;
   
   while (cur != NULL) {
      if (position < cur->position) {
         /* Insert the new value before the current value */
         tmp = create_node(position, value);
         
         if (prev == NULL) {
            /* New head node */
            head = tmp;
         } else {
            prev->next = tmp;
         }
         tmp->next = cur;
         return head;
      } else if (position == cur->position) {
         /* Replace current value */
         cur->value = value;
         return head;
      }
      
      prev = cur;
      cur = cur->next;
   }
   
   /* Either list is empty or value belongs at end of list */
   if (prev == NULL) {
      /* Empty list */
      head = create_node(position, value);
   } else {
      /* End of list */
      prev->next = create_node(position, value);
   }
   
   return head;
}

/* Interpolates a value given a single one dimensional x->value mapping.
 *  If there are no values to interpolate from then def is returned.
 */
ValueType interpolate_using_list (node *head, PositionType position, ValueType def) {
   /* The NULL values of i1 and i2 indicate that they have not been found yet.
    *  We need to ensure that the following
    *  inequality is true:
    *  (i1->position) < position < (i2->position)
    */
   node *i1 = NULL, *i2 = NULL;
   node *cur = head;
   
   if (cur == NULL) {
      /* No values to use - simply use default */
      return def;
   }
   
   /* Find irradiance values before the current time */
   while (cur != NULL && cur->position < position) {
      i1 = cur;
      cur = cur->next;
   }
   
   /* If the current time has an actual value - then use it */
   if (cur != NULL && cur->position == position) {
      return cur->value;
   }
   
   /* Find irradiance values after the current time */
   i2 = cur;
   
   /* The prefered case is to use i1 and i2 to interpolate a value
    *  between them.
    */
   if (i1 != NULL && i2 != NULL) {
      return interpolate_1(position, i1->position, i1->value, i2->position, i2->value);
   } else if (i1 == NULL && i2 != NULL) {
      return i2->value;
   } else {
      return i1->value;
   }
}

void print_list (node *head) {
   node *cur = head;
   
   while (cur != NULL) {
      printf("(%4g,%3.1g)->", cur->position, cur->value);
      cur = cur->next;
   }
   printf("\n");
}
