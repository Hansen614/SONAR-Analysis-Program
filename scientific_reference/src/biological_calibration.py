"""Versioned molecular endpoint preparation and simple relative-signal model primitives.

No function labels the uncalibrated chromatogram endpoint as an RNA fraction or PER.
"""
import numpy as np,pandas as pd
from scipy.stats import t
from layer23_common import *

def ols_fit(x,y):
    x=np.asarray(x,float);y=np.asarray(y,float);design=np.column_stack([np.ones(len(x)),x]);coef=np.linalg.lstsq(design,y,rcond=None)[0]
    residual=y-design@coef;df=len(y)-np.linalg.matrix_rank(design);sigma2=float(residual@residual/df) if df>0 else np.nan
    return dict(coefficients=coef.tolist(),residual_df=int(df),sigma2=sigma2,xtx_inverse=np.linalg.pinv(design.T@design).tolist())
def ols_predict(model,x):
    design=np.column_stack([np.ones(len(x)),np.asarray(x,float)]);coef=np.asarray(model['coefficients']);pred=design@coef
    leverage=np.einsum('ij,jk,ik->i',design,np.asarray(model['xtx_inverse']),design);half=t.ppf(.975,model['residual_df'])*np.sqrt(model['sigma2']*(1+leverage))
    return pred,pred-half,pred+half

def build_flow_molecular_pairs():
    assert_upstream();w=pd.read_csv(ROOT/'results/molecular/S10_well_level_molecular_results.csv');flow=pd.read_csv(ROOT/'results/flow_RNA_well_registry.csv')
    r=pd.read_csv(ROOT/'results/ras_results.csv');rp=r[(r.series=='S10')&(r.population_mode=='reporter')]
    bg=pd.read_csv(ROOT/'results/molecular/S10_no_editor_background.csv');constant=float(bg[bg.processing=='raw_peak_ratio'].background.mean())
    pairs=flow.merge(w,on=['well_id'],suffixes=('_flow','_molecular'),validate='one_to_one').merge(rp[['well_id','blue_positive_fraction_reporters','median_B_raw','mean_R_corrected','mean_G_corrected']],on='well_id',validate='one_to_one')
    pairs['raw_signal_index']=pairs.signal_index+constant;pairs['cell_type']='HEK293T';pairs['endpoint']='candidate_C280_direction_averaged_chromatogram_composition_NOT_RNA_fraction';pairs['PER']=np.nan;pairs['PER_status']='ASSAY_VALIDATION_INSUFFICIENT';pairs['log1p_editor_ratio']=np.log1p(pairs.condition_label)
    pairs=pairs.sort_values(['condition_label','well_id']).reset_index(drop=True)
    table('results/prediction/S10_flow_molecular_pairs.csv',pairs)
    return pairs,constant

