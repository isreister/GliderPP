#include "Observer.hh"

using namespace std;

void Observable::addObserver (Observer *o)
{
   observers.push_back(o);
}

void Observable::removeObserver (Observer *o)
{
   vector<Observer *>::iterator p, end;
   end = observers.end();
   for (p = observers.begin(); p != end; p++)
   {
      if (*p == o)
      {
         observers.erase(p);
         break;
      }
   }
}

void Observable::notifyObservers (void *msgObject)
{
   int size = observers.size();

   for (int i = 0; i < size; i++)
      observers[i]->observableChanged(this, msgObject);
}
