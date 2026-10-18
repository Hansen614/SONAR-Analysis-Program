"""SONAR scientific API v1.0. Portable, GUI-independent wrappers of the frozen kernels.

All fractions are 0..1. A RES fraction is an AC DNA mass equivalent, never RNA editing.
Legacy modules remain intact for historical regression. No implicit model refitting.
"""
from pathlib import Path
import hashlib, json
import numpy as np
import pandas as pd
from core import read_fcs, fit_gates, gate, background, score, bootstrap, R, G, B, CHANNELS
from inverse_calibration import inverse, set_ranges
from reporter_calibration import fit_model, predict
from biological_calibration import ols_fit, ols_predict

ROOT = Path(__file__).resolve().parents[1]
FINAL = json.loads((ROOT / 'config/science_final.json').read_text())
ESTIMATOR = FINAL['ras_estimator_id']
RELEASE = FINAL['release_id']

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def clean(value):
    if isinstance(value, dict): return {k: clean(v) for k,v in value.items()}
    if isinstance(value, (list,tuple,np.ndarray)): return [clean(v) for v in value]
    if isinstance(value, (float,np.floating)): return float(value) if np.isfinite(value) else None
    if isinstance(value, (bool,np.bool_)): return bool(value)
    if isinstance(value, np.integer): return int(value)
    return value

def save_json(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(clean(value), indent=2, ensure_ascii=False, allow_nan=False)+'\n')

def load_experiment(root=ROOT, verify_hashes=True):
    """Load the packaged S7/S10 manifest. original_path is provenance only, never a runtime input."""
    root=Path(root)
    manifest=pd.read_csv(root/'inventory/acquisition_manifest.csv')
    validate_metadata(manifest)
    if verify_hashes:
        for row in pd.read_csv(root/'inventory/input_files.csv').itertuples():
            path=(root/row.packaged_path).resolve()
            if not path.is_relative_to(root.resolve()): raise ValueError('Input path escapes experiment')
            if digest(path)!=row.sha256: raise ValueError('Input integrity failure: '+row.packaged_path)
        for row in json.loads((root/'reference/layer23/source_manifest.json').read_text()):
            if digest(root/row['packaged_path'])!=row['sha256']: raise ValueError('Reference integrity failure')
    return manifest

def validate_metadata(manifest):
    required={'acquisition_id','file_path','sha256','sample_role','series','well_id','profile_id','condition_label'}
    if not required.issubset(manifest.columns): raise ValueError('Missing metadata: '+str(required-set(manifest.columns)))
    if manifest.acquisition_id.duplicated().any(): raise ValueError('Duplicate acquisition IDs')
    exp=manifest[manifest.sample_role!='Mock']
    if exp.well_id.isna().any() or exp.well_id.duplicated().any(): raise ValueError('Independent well identity missing or duplicated')
    for row in exp[exp.series=='S7'].itertuples():
        if not hasattr(row,'corrected_ac_mass_fraction') or not 0<=row.corrected_ac_mass_fraction<=1: raise ValueError('Mass fraction required')
        if row.ac_fraction_basis!='mass': raise ValueError('S7 model requires verified DNA mass basis')
        if row.acquisition_id.startswith('S7_75') and row.corrected_ac_mass_fraction!=.90: raise ValueError('S7 correction mismatch')
        if row.acquisition_id.startswith('S7_90') and row.corrected_ac_mass_fraction!=.75: raise ValueError('S7 correction mismatch')
        if row.acquisition_id in ['S7_10A','S7_10B'] and row.corrected_ac_mass_fraction!=.15: raise ValueError('S7 10-to-15 correction mismatch')
    return {'status':'PASS','independent_wells':len(exp),'controls':int((manifest.sample_role=='Mock').sum())}

def load_context(path=None):
    p=ROOT/'models/context_profiles/context_v1.json' if path is None else Path(path)
    ctx=json.loads(p.read_text())
    if ctx['ras_estimator_id']!=ESTIMATOR: raise ValueError('Incompatible RAS estimator')
    if ctx['kernel_sha256']!=digest(ROOT/'src/core.py'): raise ValueError('Context kernel version mismatch')
    return ctx

def build_context(root=ROOT):
    """Rebuild this registered context from its two raw Mock acquisitions; no outcome-driven gate fit."""
    root=Path(root);cfg=json.loads((root/'config/analysis.json').read_text())
    manifest=load_experiment(root,verify_hashes=False).set_index('acquisition_id')
    ids=[cfg['context_training_control'],cfg['transfer_control']]
    raw=[read_fcs(root/manifest.loc[k,'file_path'])[0] for k in ids]
    ctx=fit_gates(raw[0],cfg)
    ca=[x[gate(x,ctx,cfg)[2]] for x in raw]
    bg,se,threshold,rq=background(ca,cfg)
    ctx.update(background=bg.tolist(),background_event_se=se.tolist(),positivity_thresholds=threshold.tolist(),red_quantitative_boundary=rq)
    cov=sum(np.cov(x[:,[G,R]],rowvar=False,ddof=1)/len(x) for x in ca)/len(ca)**2
    meta=read_fcs(root/manifest.loc[ids[0],'file_path'])[1]
    keys=['cyt','cytsn','compgaina','ch1gain','ch2gain','ch3gain','ch8gain','ch13gain','p1g','p2g','p6g','p8g','p10g','spillover','uscomp']
    return clean(dict(context_id=FINAL['context_id'],version=RELEASE,ras_estimator_id=ESTIMATOR,
        acquisition_profile_id=manifest.loc[ids[0],'profile_id'],instrument=meta['cyt'],instrument_serial=meta['cytsn'],
        instrument_fingerprint={k:meta.get(k) for k in keys},cell_type='HEK293T',
        channel_map={'EGFP':{'index_0based':G,'name':CHANNELS[G]},'mCherry':{'index_0based':R,'name':CHANNELS[R]},'BFP':{'index_0based':B,'name':CHANNELS[B]}},
        numerical_representation='native_linear_detector_au_identity_operation_only',
        compensation_status='IDENTITY_FILE_MATRIX_NOT_VALIDATED_MULTICOLOR_COMPENSATION',
        background_method='equal_control_acquisition_weighted_arithmetic_means_of_gated_singlets',
        controls=[{'id':k,'file_path':manifest.loc[k,'file_path'],'sha256':manifest.loc[k,'sha256']} for k in ids],
        gate_parameters=ctx,config=cfg,kernel_sha256=digest(root/'src/core.py'),config_sha256=digest(root/'config/analysis.json'),
        background_GR_covariance=cov,positivity_policy='maximum_control_99.5th_percentile_per_channel',
        red_quantification={'raw_lower_exclusive':rq,'validated_upper':None,'reported_channel_range':float(meta['p10r']),
          'status':'PROVISIONAL_PRECISION_BOUNDARY_NOT_EMPIRICAL_LOQ','upper_policy':'retain_flag_and_sensitivity_test_not_clip'},
        population_modes={'reporter':'singlets & raw_mCherry > red_quantitative_boundary',
          'blue_positive_reporter':'reporter & raw_BFP > BFP_positivity_threshold; linked editor required'},
        support_requirements={'minimum_events':cfg['minimum_selected_events'],'maximum_denominator_relative_se':cfg['maximum_denominator_relative_se'],'corrected_red_sum_positive':True},
        qc_rules={'state':'WARN unless acquisition or score fails','saturation':'counts at/above PnR and at observed maximum; metadata range exceedance does not establish physical clipping',
          'missing_BFP':'reporter remains possible in a separately qualified context; coexpression unavailable'},
        uncertainty={'event':'paired multichannel resampling; 2000 draws','shared_controls':'one GR noise draw per bootstrap ID used jointly across wells',
          'gates':'fixed primary; perturbations reported separately','between_wells':'n=2 independent transfection wells per condition; not event CI'},
        compatibility={'profile_must_match':True,'cell_type':'HEK293T','RAS_estimator':ESTIMATOR,'RES_requires_separate_reference_domain':True},
        limitations=['no single-color controls or FMO','no viability marker','no validated detector upper limit','S7 construct identity/loading/treatment unresolved','not transferable solely on instrument match']))

def process_fcs(path, context=None, metadata=None):
    context=load_context() if context is None else context
    if context['ras_estimator_id']!=ESTIMATOR or context['kernel_sha256']!=digest(ROOT/'src/core.py'): raise ValueError('Context version mismatch')
    x,t=read_fcs(path)
    if any(t.get(k)!=v for k,v in context['instrument_fingerprint'].items()): raise ValueError('Acquisition profile differs; build a separately qualified context')
    c=context['gate_parameters'];cfg=context['config']
    q,cell,s,_,flags=gate(x,c,cfg)
    rp=s&(x[:,R]>c['red_quantitative_boundary']);bp=rp&(x[:,B]>c['positivity_thresholds'][B])
    masks={'quality':q,'cell':cell,'singlet':s,'reporter':rp,'blue_positive_reporter':bp,'blue_negative_reporter':rp&~bp}
    optical=[]
    for name,ix in [('EGFP',G),('mCherry',R),('BFP',B)]:
        limit=float(t[f'p{ix+1}r'])
        optical.append(dict(channel=name,declared_PnR=limit,recorded_max=float(x[:,ix].max()),recorded_min=float(x[:,ix].min()),
          events_at_or_above_PnR=int((x[:,ix]>=limit).sum()),reporter_at_or_above_PnR=int((rp&(x[:,ix]>=limit)).sum()),
          events_equal_recorded_max=int((x[:,ix]==x[:,ix].max()).sum()),events_exactly_PnR=int((x[:,ix]==limit).sum()),
          physical_saturation='UNRESOLVED_RANGE_EXCEEDED' if (x[:,ix]>=limit).any() else 'NO_PnR_EXCEEDANCE_NOT_DETECTOR_VALIDATION'))
    md={} if metadata is None else metadata
    qc=dict(recorded_events=len(x),after_acquisition_QC=int(q.sum()),cell_events=int(cell.sum()),singlet_events=int(s.sum()),
      reporter_positive_events=int((s&(x[:,R]>c['positivity_thresholds'][R])).sum()),quantifiable_reporter_events=int(rp.sum()),
      BFP_positive_singlets=int((s&(x[:,B]>c['positivity_thresholds'][B])).sum()),coexpression_events=int(bp.sum()) if md.get('linked_editor_present',False) else None,
      blue_positive_reporter_diagnostic_events=int(bp.sum()),context_profile_id=context['context_id'],
      background_provenance='models/context_profiles/context_v1.json#controls',threshold_provenance='models/context_profiles/context_v1.json#gate_parameters',
      qc_state='WARN_OPTICAL_UNVALIDATED',range_warning=any(a['events_at_or_above_PnR']>0 for a in optical),**flags)
    return dict(array=x,masks=masks,metadata=md,context=context,qc=qc,optical=optical,input_sha256=digest(path))

def calculate_ras(processed,population_mode='reporter',uncertainty=None,bootstrap_repeats=0):
    """Uncertainty can be an audited frozen record; optional paired bootstrap for new samples.
    bootstrap_repeats=0 returns analytic event SE and explicit interval-unavailable status.
    """
    if population_mode not in ['reporter','blue_positive_reporter','blue_negative_reporter']: raise ValueError('Unknown population mode')
    ctx=processed['context'];md=processed['metadata']
    base=dict(sample_id=md.get('acquisition_id'),well_id=md.get('well_id'),experimental_condition=md.get('condition_label'),
      population_mode=population_mode,context_profile_id=ctx['context_id'],estimator_version=ESTIMATOR,input_sha256=processed['input_sha256'],qc_state=processed['qc']['qc_state'])
    if population_mode=='blue_positive_reporter' and not md.get('linked_editor_present',False):
        return {**base,'ras':None,'score_status':'NOT_APPLICABLE_NO_LINKED_EDITOR','scientific_status':'BLUE_TAIL_NOT_EDITOR_POPULATION'}
    v=processed['array'][processed['masks'][population_mode]];c=ctx['gate_parameters']
    g=v[:,G]-c['background'][G];r=v[:,R]-c['background'][R]
    res=score(g,r,ctx['config']);u={'status':'DELTA_EVENT_SE_ONLY_INTERVAL_NOT_COMPUTED'}
    if uncertainty is not None:
        u={k:clean(v) for k,v in uncertainty.items()};u['status']='FROZEN_PAIRED_EVENT_SHARED_CONTROL_BOOTSTRAP'
    elif bootstrap_repeats and res['ras'] is not None:
        cfg={**ctx['config'],'bootstrap_repeats':int(bootstrap_repeats)}
        noise=np.random.default_rng(cfg['seed']).multivariate_normal([0,0],ctx['background_GR_covariance'],size=bootstrap_repeats)
        seed=int(processed['input_sha256'][:8],16)
        u,_,_=bootstrap(g,r,noise,cfg,np.random.default_rng(seed));u['status']='PAIRED_EVENT_SHARED_CONTROL_BOOTSTRAP_V1_API'
    return clean({**base,**res,'uncertainty':u,'scientific_status':'DETECTOR_SCALE_EXPLORATORY_NOT_MOLECULAR_FRACTION'})

def fit_reporter_calibration(fractions,ras,model='monotone_hinge_50',fraction_basis='AC_DNA_mass_fraction'):
    """Explicit research fit. Does not replace or qualify the released model."""
    x=np.asarray(fractions,float);y=np.asarray(ras,float)
    if fraction_basis!='AC_DNA_mass_fraction': raise ValueError('Unsupported fraction basis')
    if len(x)!=len(y) or len(x)<4 or not np.isfinite(x).all() or not np.isfinite(y).all() or np.any((x<0)|(x>1)) or len(np.unique(x))<2: raise ValueError('Invalid reference observations')
    m=fit_model(model,x,y);m['qualification']='NEW_RESEARCH_FIT_REQUIRES_OWN_METADATA_VALIDATION_AND_MODEL_ID'
    return m

def load_res_model(path=None):
    p=ROOT/'models/res_primary/model.json' if path is None else Path(path)
    m=json.loads(p.read_text())
    if m['ras_estimator_id']!=ESTIMATOR or m['kernel_sha256']!=digest(ROOT/'src/core.py'): raise ValueError('Model/estimator version mismatch')
    if m['context_profile_sha256']!=digest(ROOT/'models/context_profiles/context_v1.json'): raise ValueError('Model/context fingerprint mismatch')
    for rel,h in m['source_hashes'].items():
        if digest(ROOT/rel)!=h: raise ValueError('Calibration dependency changed: '+rel)
    return m

def forward_res(fraction,model=None):
    m=load_res_model() if model is None else model
    if not np.isfinite(fraction) or not m['x_min']<=fraction<=m['x_max']: return None
    return float(predict(m,[fraction])[0])

def calculate_res(ras, *, context_id, population_mode, calibration_domain_id, mode='research',
                  sample_id=None, ras_interval=None, model=None, uncertainty_bundle=None):
    """Load-only inverse. Separate research output, routine permission, and incompatible mapping."""
    if mode not in ['research','routine']: raise ValueError('Mode must be research or routine')
    m=load_res_model() if model is None else model
    if m['ras_estimator_id']!=ESTIMATOR: raise ValueError('Estimator mismatch')
    u=json.loads((ROOT/'models/res_primary/uncertainty.json').read_text()) if uncertainty_bundle is None else uncertainty_bundle
    if sample_id in u.get('sample_RAS',{}) and (ras is None or not np.isclose(float(ras),u['sample_RAS'][sample_id],rtol=1e-12,atol=1e-12)):
        raise ValueError('Registered sample RAS differs; do not reuse its frozen observation uncertainty')
    compatible=(context_id==m['context_id'] and population_mode==m['population_mode'] and calibration_domain_id==m['calibration_domain_id'])
    val=float(ras) if ras is not None else np.nan;inv=inverse(m,val)
    point=inv['point'];ranges=[];lo=hi=None;cross_ranges=[];cross_lo=cross_hi=None;boot=[];bn=0
    margin=0.
    if ras_interval is not None and np.isfinite(val):
        if len(ras_interval)!=2 or not all(np.isfinite(ras_interval)): raise ValueError('Invalid RAS interval')
        margin=max(0.,val-ras_interval[0],ras_interval[1]-val)
    if np.isfinite(val):
        grid=np.asarray(u['grid']);low=np.asarray(u['primary_lower'])-margin;high=np.asarray(u['primary_upper'])+margin
        ranges,lo,hi=set_ranges(grid,(low<=val)&(high>=val))
        iso_low=np.asarray(u['isotonic_lower'])-margin;iso_high=np.asarray(u['isotonic_upper'])+margin
        cross_ranges,cross_lo,cross_hi=set_ranges(grid,((low<=val)&(high>=val))|((iso_low<=val)&(iso_high>=val)))
        # The registered samples retain joint reference/observation/control draw IDs.
        observations=u['sample_observation_draws'].get(sample_id)
        for i,coef in enumerate(u['hinge_coefficients']):
            a,sl,sh=coef;bm=dict(knots=[0,.5,1],values=[a,a+.5*sl,a+.5*sl+.5*sh])
            z=inverse(bm,observations[i] if observations is not None else val)
            if z['low'] is not None: boot.append([z['low'],z['high']])
        bn=len(u['hinge_coefficients'])
    interval=[float(np.quantile(np.array(boot)[:,0],.025)),float(np.quantile(np.array(boot)[:,1],.975))] if boot else None
    domain=m['domains'];rg=domain['internal_screen']['RAS_largest_contiguous']
    in_region=np.isfinite(val) and rg is not None and rg[0]<=val<=rg[1]
    width=None if lo is None else hi-lo
    sample_narrow=lo is not None and lo>0 and hi<1 and width<=FINAL['compatibility_width_limit']
    cross_width=None if cross_lo is None else cross_hi-cross_lo
    cross_narrow=cross_lo is not None and cross_lo>0 and cross_hi<1 and cross_width<=FINAL['compatibility_width_limit']
    if inv['status']=='OUT_OF_CALIBRATION_RANGE': region='OUTSIDE_NUMERICAL_RESPONSE_RANGE'
    elif point is None: region='NON_IDENTIFIABLE_OR_UNAVAILABLE'
    elif point>=.9: region='OBSERVED_HIGH_END_FLATTENING_PRIMARY_SLOPE_MODEL_DEPENDENT'
    elif in_region and sample_narrow and cross_narrow: region='INTERNAL_EXPLORATORY_SCREEN'
    elif in_region and sample_narrow: region='PRIMARY_INFORMATIVE_CROSS_MODEL_SET_BROAD'
    else: region='NUMERICALLY_AVAILABLE_WEAK_OR_BOUNDARY_SUPPORT'
    slope=None if point is None else (m['coefficients'][1] if point<.5 else m['coefficients'][2])
    evidence='S7_SAME_EXPERIMENT_INTERNAL_EXPLORATORY' if compatible else 'CALIBRATION_TRANSFER_NOT_ESTABLISHED'
    ordinary=point if compatible and mode=='research' else None
    return clean(dict(sample_id=sample_id,RAS=ras,model_id=m['model_id'],estimator_version=ESTIMATOR,context_profile_id=context_id,
      population_mode=population_mode,input_basis=m['fraction_basis'],output_unit='AC_DNA_mass_equivalent_fraction_0_to_1',
      res_mass_fraction=ordinary,research_res_mass_fraction=point if compatible else None,
      hypothetical_incompatible_mapping=point if not compatible and mode=='research' else None,
      exact_inverse_interval=[inv['low'],inv['high']] if inv['low'] is not None else None,numerical_status=inv['status'],
      scientific_status=evidence,calibration_region=region,mode=mode,routine_res_mass_fraction=None,
      routine_status='NOT_QUALIFIED_INTERNAL_CALIBRATION_ONLY',local_forward_slope=slope,local_inverse_sensitivity=None if slope is None or slope<=1e-12 else 1/slope,
      conditional_bootstrap_interval=interval,bootstrap_success_n=len(boot),bootstrap_total_n=bn,
      bootstrap_success_fraction=len(boot)/bn if bn else None,bootstrap_status='CONDITIONAL_ON_IN_RANGE_NOT_COVERAGE_GUARANTEE',
      observation_uncertainty='PAIRED_SHARED_CONTROL_DRAWS' if sample_id in u['sample_observation_draws'] else 'RAS_MARGIN_ONLY_NO_OBSERVATION_BOOTSTRAP',
      compatibility_intervals=ranges,compatibility_low=lo,compatibility_high=hi,compatibility_width=width,
      within_reference_response_screen=bool(in_region),primary_sample_interval_narrow=bool(sample_narrow),
      cross_model_sample_intervals=cross_ranges,cross_model_sample_width=cross_width,cross_model_sample_interval_narrow=bool(cross_narrow),
      uncertainty_status='BOOTSTRAP_CURVE_PLUS_INTERNAL_RESIDUAL_PLUS_RAS_MARGIN_NOT_NOMINAL_95CI',
      numerical_domain=domain['numerical'],calibration_domain_id=m['calibration_domain_id'],
      transfer_domain='S7_REFERENCE_SESSION_ONLY_NO_EXTERNAL_TRANSFER',validated_RNA_editing_fraction=None))

def analyze_molecular_reference(root=ROOT):
    root=Path(root);p=root/'results/molecular/S10_well_level_molecular_results.csv'
    if not p.exists(): return {'status':'MOLECULAR_REFERENCE_MISSING','relative_index_available':False,'absolute_fraction_qualified':False,'PER':None}
    wells=pd.read_csv(p)
    return {'status':'RELATIVE_INDEX_AVAILABLE','relative_index_available':True,'candidate_editing_signal_detected':True,
      'absolute_fraction_qualified':False,'independent_wells':int(wells.well_id.nunique()),'well_results':clean(wells.to_dict('records')),'PER':None,'PER_status':'ASSAY_VALIDATION_INSUFFICIENT'}

def fit_biological_calibration(x,y,endpoint='relative_chromatogram_index'):
    if endpoint!='relative_chromatogram_index': raise ValueError('Absolute fraction fitting requires a separately reviewed assay/domain qualification; not implemented in v1')
    x=np.asarray(x,float);y=np.asarray(y,float)
    if x.ndim==1:x=x[:,None]
    if len(x)!=len(y) or len(y)<=x.shape[1]+1 or not np.isfinite(x).all() or not np.isfinite(y).all(): raise ValueError('Insufficient finite well-level observations')
    return {**ols_fit(x,y),'endpoint':endpoint,'status':'EXPLORATORY_RELATIVE_MODEL_NOT_PER','absolute_fraction_qualified':False}

def predict_per(res_result,biological_model=None):
    if biological_model is None: reason='NO_QUALIFIED_ABSOLUTE_MOLECULAR_MODEL'
    elif not biological_model.get('absolute_fraction_qualified',False): reason='RELATIVE_INDEX_CANNOT_POPULATE_PER'
    else: reason='ABSOLUTE_MODEL_ADAPTER_NOT_IMPLEMENTED_REQUIRES_SCIENTIFIC_REVIEW'
    return {'PER':None,'unit':'percent_edited_RNA','PER_status':reason,'relative_molecular_analysis_available':biological_model is not None,'framework':'PER = 100 h(RES); unavailable until independently qualified'}

def generate_measurement_report(path,samples):
    save_json(path,{'release_id':RELEASE,'samples':samples,'missing_values':'JSON null, never zero','sharing':'internal authorized data'})
    return str(path)
