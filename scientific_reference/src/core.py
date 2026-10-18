"""Outcome-blind event processing and paired linear ratio-of-sums kernel."""
import numpy as np
from flowio import FlowData
from scipy.stats import chi2
from sklearn.covariance import MinCovDet

CHANNELS=['FSC-H','FSC-A','SSC-H','SSC-A','FL1-H','FL1-A','FL6-H','FL6-A','FL11-H','FL11-A','FSC-Width','Time']
R,G,B=9,5,7

def read_fcs(path):
    fd=FlowData(str(path)); t=fd.text
    if fd.pnn_labels!=CHANNELS: raise ValueError('Unsupported channel map')
    if [t[f'p{i}s'] for i in [6,8,10]]!=['GFP-A','PB450-A','mCherry-A']: raise ValueError('Channel descriptions differ')
    if any(t[f'p{i}e']!='0,0' or float(t[f'p{i}g'])!=1 for i in range(1,13)): raise ValueError('Unsupported gain/log profile')
    spill=t['spillover'].split(','); n=int(spill[0]); matrix=np.array(spill[n+1:],float).reshape(n,n)
    if not np.array_equal(matrix,np.eye(n)) or t['uscomp']!='False': raise ValueError('Optical policy needs explicit review')
    # The identity operation is numerically a no-op. This is NOT optical validation.
    return fd.as_array(preprocess=True),t

def mad(x): return float(np.median(np.abs(x-np.median(x)))*1.4826)

def time_qc(x,cfg):
    finite=np.isfinite(x).all(axis=1)&(x[:,11]>=0)&(x[:,:4]>0).all(axis=1)
    time=x[:,11]; bins=np.floor(np.maximum(time,0)/cfg['time_bin_seconds']).astype(int)
    counts=np.bincount(bins[finite]); duration=max(time[finite].max(),1e-9)
    exposure=np.clip(duration-np.arange(len(counts))*cfg['time_bin_seconds'],0,cfg['time_bin_seconds'])
    rates=counts/np.maximum(exposure,1e-9); complete=exposure>=0.95*cfg['time_bin_seconds']
    med=float(np.median(rates[complete])); scale=max(mad(rates[complete]),np.sqrt(med),0.1*med)
    flagged=complete&(np.abs(rates-med)>cfg['time_rate_mad_multiplier']*scale)
    mask=finite&~flagged[bins]
    records=[]
    for i in range(len(counts)):
        z=finite&(bins==i)
        records.append(dict(bin=i,start_s=i*cfg['time_bin_seconds'],exposure_s=float(exposure[i]),events=int(counts[i]),rate_per_s=float(rates[i]),rate_outlier=bool(flagged[i]),FSC_A_median=float(np.median(x[z,1])) if z.any() else None,G_median=float(np.median(x[z,G])) if z.any() else None,R_median=float(np.median(x[z,R])) if z.any() else None,B_median=float(np.median(x[z,B])) if z.any() else None))
    return mask,records,{'nonfinite_or_nonpositive_scatter':int((~finite).sum()),'time_reversals':int((np.diff(time)<0).sum()),'rate_removed':int((finite&~mask).sum())}

def fit_gates(mock,cfg):
    m,_,_=time_qc(mock,cfg); xy=np.log10(mock[m][:,[1,3]])
    rng=np.random.default_rng(cfg['seed']); fit=xy[rng.choice(len(xy),min(cfg['scatter_fit_max_events'],len(xy)),replace=False)]
    model=MinCovDet(support_fraction=cfg['scatter_mcd_support_fraction'],random_state=cfg['seed']).fit(fit)
    d=xy-model.location_; dist=np.einsum('ij,jk,ik->i',d,model.precision_,d)
    sel=dist<=chi2.ppf(cfg['scatter_chi2_probability'],2)
    ah=np.log10(mock[m,1]/mock[m,0])[sel]
    return dict(location=model.location_.tolist(),precision=model.precision_.tolist(),covariance=model.covariance_.tolist(),distance_cutoff=float(chi2.ppf(cfg['scatter_chi2_probability'],2)),singlet_center=float(np.median(ah)),singlet_scale=mad(ah),training_control=cfg['context_training_control'])

def gate(x,ctx,cfg,prob=None,singlet_mult=None,no_time=False):
    quality,time_table,flags=time_qc(x,cfg)
    if no_time: quality=np.isfinite(x).all(axis=1)&(x[:,11]>=0)&(x[:,:4]>0).all(axis=1)
    xy=np.log10(np.maximum(x[:,[1,3]],np.finfo(float).tiny)); d=xy-np.array(ctx['location'])
    dist=np.einsum('ij,jk,ik->i',d,np.array(ctx['precision']),d)
    cells=quality&(dist<=chi2.ppf(prob or cfg['scatter_chi2_probability'],2))
    ah=np.log10(np.maximum(x[:,1],1e-100)/np.maximum(x[:,0],1e-100))
    singlets=cells&(np.abs(ah-ctx['singlet_center'])<=(singlet_mult or cfg['singlet_log_area_height_mad_multiplier'])*ctx['singlet_scale'])
    return quality,cells,singlets,time_table,flags

def background(control_arrays,cfg):
    means=np.array([a.mean(axis=0) for a in control_arrays]); variances=np.array([a.var(axis=0,ddof=1)/len(a) for a in control_arrays])
    bg=means.mean(axis=0); se=np.sqrt(variances.sum(axis=0))/len(means)
    thresholds=np.max([np.quantile(a,cfg['positivity_quantile'],axis=0) for a in control_arrays],axis=0)
    sd=np.sqrt(np.mean([a.var(axis=0,ddof=1) for a in control_arrays],axis=0))
    rq=max(thresholds[R],bg[R]+cfg['red_min_background_sd_multiplier']*sd[R])
    return bg,se,thresholds,rq

def score(g,r,cfg):
    """No labels, green gate, clipping, pseudocounts, or transformed values."""
    g=np.asarray(g,dtype=float); r=np.asarray(r,dtype=float)
    if g.shape!=r.shape: raise ValueError('Paired channels must have the same shape')
    n=len(g); sg=float(g.sum()); sr=float(r.sum())
    result=dict(n_selected=n,sum_G_corrected=sg,sum_R_corrected=sr,ras=None,score_status='NOT_ESTIMABLE')
    if n<2 or sr<=0 or not np.isfinite(g).all() or not np.isfinite(r).all(): return result
    ratio=sg/sr; den_se=float(r.std(ddof=1)/np.sqrt(n)); rel=den_se/(sr/n)
    se=float((g-ratio*r).std(ddof=1)/np.sqrt(n)/(sr/n))
    result.update(mean_G_corrected=float(g.mean()),mean_R_corrected=float(r.mean()),median_G_corrected=float(np.median(g)),median_R_corrected=float(np.median(r)),denominator_relative_se=rel,ras_delta_se=se,effective_red_events=sr**2/float(np.square(r).sum()),max_red_weight=float(r.max()/sr),signed_green_negative_fraction=float(np.mean(g<0)))
    if n>=cfg['minimum_selected_events'] and rel<=cfg['maximum_denominator_relative_se']:
        result.update(ras=ratio,score_status='ESTIMABLE_EXPLORATORY')
    return result

def bootstrap(g,r,control_noise,cfg,rng):
    n=len(g); draws=[]; combined=[]
    for bi in range(cfg['bootstrap_repeats']):
        ids=rng.integers(0,n,n); gm=g[ids].mean(); rm=r[ids].mean()
        draws.append(gm/rm if rm>0 else np.nan)
        gb=gm-control_noise[bi,0]; rb=rm-control_noise[bi,1]
        combined.append(gb/rb if rb>0 else np.nan)
    return dict(event_ci_low=float(np.nanquantile(draws,.025)),event_ci_high=float(np.nanquantile(draws,.975)),event_control_ci_low=float(np.nanquantile(combined,.025)),event_control_ci_high=float(np.nanquantile(combined,.975)),bootstrap_half_low=float(np.nanquantile(draws[:len(draws)//2],.025)),bootstrap_half_high=float(np.nanquantile(draws[:len(draws)//2],.975)),bootstrap_denominator_failure_fraction=float(np.mean(~np.isfinite(combined)))),draws,combined
