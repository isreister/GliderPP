/* shared_list.h
 * 
 *	A module defining the data structures and functions for dealing
 *  with a linked-list that stores (time or wavelength)/value data.
 *
 * Latest modification: 00/10/26
 */

#ifndef _SHARED_LIST
#define _SHARED_LIST

#include "shared_types.h"

#ifdef __cplusplus
extern "C" {
#endif /* __cplusplus */

/**
 * A linked-list node. This is used in interpolating in a one-dimensional
 *  dataset - i.e. one location component mapping onto a one-component value.
 */
typedef struct node_struct {
	/**
         * Position represents time, depth, wavelength or something else
         *  according to the data being stored.
         */
	PositionType position;
	
	/**
         * Value represents the value matching the position.
         */
	ValueType value;
	
        /**
         * The next node in the linked-list.
         */
	struct node_struct *next;
} node;

/**
 * Deletes a linked-list.
 * @param head The head of the linked-list to delete. If this is NULL then this
 *  function does nothing.
 */
void delete_list (node *head);

/**
 * Inserts a value into the linked list at the given position.
 * @param head The head of the linked-list to add a value to. If this is NULL
 *  then this function creates the linked-list..
 * @param position The physical value corresponding to the value. Note that
 *  although this is used to order the nodes in the linked-list, it is not the
 *  index of the value in the list.
 * @param value The value to insert.
 * @return The (possibly new) head of the list. It is important for the caller
 *  to update its head pointer to this return value. e.g.<br>
 * <code>
 * node *head = NULL;<br>
 *  ...<br>
 * head = add_list_value(head, 10, 134.56);
 * </code>
 */
node *add_list_value (node *head, PositionType position, ValueType value);

/**
 * Produces an interpolated value from the list.
 * @param head The head of the linked-list to use.
 * @param position The position of the point to calculate the value at.
 * @param def The default value to return. This is returned if head is NULL - 
 *  i.e. the list is empty and it has no other value to return.
 * @return The interpolated value, or def if the list is empty.
 */
ValueType interpolate_using_list (node *head, PositionType position,
   ValueType def);

/**
 * Prints out the list structure on stdout. Mostly here for debugging purposes
 *  so that programs can quickly print out the data they actually have loaded
 *  and the structure that the list has taken. Position increases along a line.
 * @param head The head of the list to display.
 */
void print_list (node *head);

#ifdef __cplusplus
}
#endif /* __cplusplus */

#endif /* #ifndef _SHARED_LIST */
