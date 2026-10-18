"""Metadata-only correction and preservation contract for the v4 incremental release."""
import shutil
from layer23_common import *
BASE=ROOT/'baselines/v3'
CORR=json.loads((ROOT/'config/s7_label_correction.json').read_text())
DEPENDENT_PREDICTION={'S10_affine_transform_sensitivity.csv','S10_staged_model_results.csv','S10_prediction_summary.json','SONAR_layer_status.csv'}

def frozen_paths():
    paths=[]
    for p in BASE.rglob('*'):
        if not p.is_file():continue
        rel=p.relative_to(BASE)
        if rel.parts[0] in ['contexts','masks'] or (rel.parts[0]=='results' and 'calibration' not in rel.parts and p.name not in DEPENDENT_PREDICTION):paths.append(rel)
    paths.append(pd.io.common.stringify_path('models/layer23/S10_exploratory_signal_models.json'))
    return paths

def prepare():
    # An isolated incremental run starts from archived, reproduced upstream measurements.
    for folder in ['results','inventory','contexts','masks','figures','models','reports']:
        for p in (BASE/folder).rglob('*'):
            if p.is_file():
                dst=ROOT/p.relative_to(BASE)
                if not dst.exists():dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst)
    for name in ['SONAR_Measurement_Evidence_Report.md','SONAR_Layer23_Scientific_Summary_ZH.md','SONAR_Figure_Evidence_Inventory.md','SONAR_中文科学摘要.md']:
        p=BASE/name
        if p.exists() and not (ROOT/name).exists():shutil.copy2(p,ROOT/name)
    assert_upstream();verify_frozen()

def verify_frozen():
    rows=[]
    for rel in frozen_paths():
        a=sha(BASE/rel);b=sha(ROOT/rel);assert a==b,'Unaffected evidence changed: '+str(rel)
        rows.append(dict(path=str(rel),v3_sha256=a,current_sha256=b,byte_identical=True))
    changed_figures={'F04_S7_normalization','L23_07_S7_models','L23_08_S7_residuals','L23_09_inverse_uncertainty','L23_10_reference_anomaly'}
    for p in (BASE/'figures').rglob('*'):
        if p.suffix not in ['.png','.svg'] or p.stem in changed_figures:continue
        rel=p.relative_to(BASE);assert sha(p)==sha(ROOT/rel),'Unaffected plot changed: '+str(rel)
        rows.append(dict(path=str(rel),v3_sha256=sha(p),current_sha256=sha(ROOT/rel),byte_identical=True))
    table('reports/S7_correction_unaffected_hashes.csv',rows)
    return len(rows)

def run():
    for name in ['acquisition_manifest.csv','acquisition_file_manifest.csv']:
        d=pd.read_csv(BASE/'inventory'/name)
        s7=(d.series=='S7')&(d.sample_role!='Mock')
        d['original_ac_mass_fraction']=np.where(s7,d.source_condition_label/100,np.nan)
        d['pre_correction_ac_mass_fraction']=np.where(s7,d.condition_label/100,np.nan)
        d['corrected_ac_mass_fraction']=d.pre_correction_ac_mass_fraction
        d['original_sample_id']=d.sample_id;d['original_acquisition_id']=d.acquisition_id
        d['original_filename']=d.file_path.map(lambda x:str(x).split('/')[-1])
        changed=d.acquisition_id.isin(CORR['swap_by_acquisition_id'])
        d.loc[changed,'corrected_ac_mass_fraction']=d.loc[changed,'acquisition_id'].map(CORR['swap_by_acquisition_id'])
        d.loc[s7,'condition_label']=d.loc[s7,'corrected_ac_mass_fraction']*100
        d.loc[s7,'actual_ac_mass_pct']=d.loc[s7,'condition_label']
        d['reference_basis_id']=np.where(s7,CORR['reference_basis_id'],None)
        d['correction_source']=np.where(changed,CORR['correction_source'],np.where(s7&(d.source_condition_label==10),'Prior user-confirmed 10% to 15% correction preserved',None))
        d['correction_date']=np.where(changed,CORR['correction_date'],None)
        d['correction_status']=np.where(changed,CORR['correction_status'],np.where(s7&(d.source_condition_label==10),'PRIOR_USER_CONFIRMED_10_TO_15',np.where(s7,'UNCHANGED','NOT_APPLICABLE')))
        table('inventory/'+name,d)
        if name=='acquisition_manifest.csv':
            manifest=d.loc[s7].copy();table('inventory/S7_corrected_manifest.csv',manifest)
    raw=pd.read_csv(ROOT/'results/ras_results.csv');s=raw[(raw.series=='S7')&(raw.population_mode=='reporter')].copy()
    cols=['acquisition_id','original_ac_mass_fraction','pre_correction_ac_mass_fraction','corrected_ac_mass_fraction','reference_basis_id','correction_status','correction_source','correction_date','original_filename','original_sample_id']
    s=s.merge(manifest[cols],on='acquisition_id',validate='one_to_one');s['pre_correction_condition_label']=s.condition_label;s['condition_label']=s.corrected_ac_mass_fraction*100;s['mass_fraction']=s.corrected_ac_mass_fraction
    s=s.sort_values(['condition_label','replicate_label']);table('results/calibration/S7_reference_response_corrected.csv',s)
    means=s.groupby('corrected_ac_mass_fraction').agg(mean_RAS=('ras','mean'),SD_RAS=('ras','std'),independent_wells=('ras','size'),original_acquisition_ids=('acquisition_id',lambda a:';'.join(a))).reset_index();table('results/calibration/S7_corrected_response_summary.csv',means)
    # Relabel existing diagnostic summaries, without revisiting or changing any events.
    for name in ['S7_anomaly_well_diagnostics.csv','S7_anomaly_distributions.csv','S7_anomaly_distribution_quantiles.csv']:
        d=pd.read_csv(BASE/'results/calibration'/name);d['pre_correction_condition_label']=d.condition_label
        d['condition_label']=d.acquisition_id.map(manifest.set_index('acquisition_id').condition_label);d['reference_basis_id']=CORR['reference_basis_id'];table('results/calibration/'+name,d)
    sens=pd.read_csv(ROOT/'results/sensitivity.csv');sens=sens[sens.population_mode=='reporter'].merge(manifest[['acquisition_id','condition_label']],on='acquisition_id');rows=[]
    for scenario,z in sens.groupby('scenario'):
        m=z.groupby('condition_label').ras.mean();rows.append(dict(scenario=scenario,RAS75=m[75],RAS90=m[90],RAS100=m[100],delta_90_minus_75=m[90]-m[75],reversal_retained=m[90]<m[75],reference_basis_id=CORR['reference_basis_id']))
    table('results/calibration/S7_anomaly_sensitivity.csv',rows)
    print('Metadata correction applied to four original acquisitions; measurements unchanged',flush=True)
