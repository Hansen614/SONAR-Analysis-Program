"""Set-valued monotonic inversion with explicit unavailable states and grid compatibility sets."""
import numpy as np

def inverse(model,y,tol=1e-12):
    if not np.isfinite(y):return dict(low=None,high=None,point=None,status='UNAVAILABLE_INPUT')
    x=np.asarray(model['knots']);v=np.asarray(model['values'])
    if np.any(np.diff(v)<-tol):return dict(low=None,high=None,point=None,status='NON_MONOTONE_MODEL')
    if y<v[0]-tol or y>v[-1]+tol:return dict(low=None,high=None,point=None,status='OUT_OF_CALIBRATION_RANGE')
    candidates=[]
    for l,h,a,b in zip(x[:-1],x[1:],v[:-1],v[1:]):
        if abs(b-a)<=tol:
            if abs(y-a)<=tol:candidates.extend([l,h])
        elif a-tol<=y<=b+tol:candidates.append(l+(h-l)*(y-a)/(b-a))
    if not candidates:return dict(low=None,high=None,point=None,status='UNAVAILABLE_INVERSE')
    lo,hi=float(min(candidates)),float(max(candidates));unique=abs(hi-lo)<=tol
    return dict(low=lo,high=hi,point=lo if unique else None,status='EXPLORATORY_UNIQUE_MODEL_INVERSE' if unique else 'NON_IDENTIFIABLE_PLATEAU')

def set_ranges(grid,mask):
    idx=np.flatnonzero(mask)
    if not len(idx):return [],None,None
    chunks=np.split(idx,np.flatnonzero(np.diff(idx)>1)+1)
    ranges=[[float(grid[c[0]]),float(grid[c[-1]])] for c in chunks]
    return ranges,ranges[0][0],ranges[-1][1]

