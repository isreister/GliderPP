import numpy as np

def good_vals(inarray):
   '''
      check for number of good values in a list/array; must be better way to check for '--'
   '''
   inarray=inarray[np.isfinite(inarray)==True]
   return len(inarray)

def good_array(inarray):
   '''
      returns good array: -- removed.
   '''
   outarray=inarray[np.isfinite(inarray)==True]
   return np.asarray(outarray)

def get_mask(inarray):
   '''
      returns good array: -- and 0.0 removed.
   '''
   # init mask
   mask=np.zeros(np.shape(inarray))
   # allow finite values
   mask[np.isfinite(inarray)==True]=1
   # remove zeros (nearly always spurious)
   mask[inarray==0]=0
   return mask.astype(int)

def get_spurious(inarray,deviation=150):
   '''
      returns good array: removes pressure values that deviate from a twice moving-average smoothed profile by more than deviation
   '''
   # init mask
   mask=np.ones(np.shape(inarray))
   # cal smoothed array
   ext_array = np.append(inarray,np.ones(100)*inarray[-1])
   ext_apprx = movingaverage(ext_array,10)
   ext_apprx = movingaverage(ext_apprx,5)
   diff      = abs(ext_apprx[0:np.shape(inarray)[0]]-inarray)
   bad       = np.where(diff>deviation)[0]
   mask[bad] = 0
   return mask.astype(int)

def movingaverage(interval, window_size):
    # called from here
    window = np.ones(int(window_size))/float(window_size)
    return np.convolve(interval, window,'same')
