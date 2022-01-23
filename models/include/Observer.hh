#ifndef _OBSERVER_HH
#define _OBSERVER_HH

#include <vector>
#include <cstdlib>

class Observer;
class Observable;

/**
 * An abstract class of object that can listen for changes to an Observable
 *  object.
 */
class Observer {
public:
   /**
    * This is called when an Observable object changes.
    * @param o The Observable object that changed (i.e. had notifyObservers()
    *  called upon it).
    * @param msgObject The pointer that was passed as the parameter to
    *  notifyObservers().
    */
   virtual void observableChanged (Observable *o, void *msgObject) = 0;
};

/**
 * An abstract class of object that can listen to an Observable object.
 * It makes observableChanged() calls on the Observer object whenever
 *  notifyObservers is called.
 */
class Observable {
private:
   /**
    * A list of the observing objects.
    */
   std::vector<Observer *> observers;

public:
   /**
    * Adds an observer to the list of observer objects to notify when the
    *  Observable object changes.
    * @param o The observer to add.
    */
   void addObserver (Observer *o);

   /**
    * Removes an observer from the list of observer objects to notify when the
    *  Observable object changes.
    * @param o The observer to add.
    */
   void removeObserver (Observer *o);

   /**
    * Tells all the observer objects that the observable object has changed.
    *  Each observer object receives the pointer that is passed, and also a
    *  pointer to the Observable object that this member function was called on.
    * @param msgObject The pointer to pass to the observers.
    */
   void notifyObservers (void *msgObject = NULL);
};

#endif /* #ifndef _OBSERVER_HH */
