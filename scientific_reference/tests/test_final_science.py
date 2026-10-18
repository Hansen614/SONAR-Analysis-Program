"""New contract/edge/integration tests. Synthetic edge cases are not experimental evidence."""
from pathlib import Path
import sys,json,copy
import numpy as np
import pandas as pd
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import science_api as api
from inverse_calibration import inverse
from core import score,read_fcs,G,R,B

def test_preserved_corrected_metadata_and_raw_integrity():
    m=api.load_experiment();assert len(m)==34
    assert api.validate_metadata(m)['independent_wells']==32

def test_context_contract_and_background_separation():
    c=api.load_context();g=c['gate_parameters']
    assert g['background'][G]!=g['positivity_thresholds'][G]
    assert c['red_quantification']['validated_upper'] is None
    assert c['channel_map']['BFP']['index_0based']==B

@pytest.mark.parametrize('name',['S7_90B','S7_5B','S7_100A','S10_1_8_A'])
def test_real_raw_to_score_golden(name):
    golden=json.loads((ROOT/'tests/golden_reference/real_samples.json').read_text())[name]
    m=api.load_experiment(verify_hashes=False).set_index('acquisition_id').loc[name].to_dict();m['acquisition_id']=name
    m['linked_editor_present']=m['series']=='S10' and m['condition_label']>0
    p=api.process_fcs(ROOT/m['file_path'],api.load_context(),m)
    s=api.calculate_ras(p)
    assert s['n_selected']==golden['n_selected']
    for k in ['ras','sum_G_corrected','sum_R_corrected','effective_red_events']:
        assert s[k]==pytest.approx(golden[k],rel=1e-12,abs=1e-12)
    r=api.calculate_res(s['ras'],context_id=api.FINAL['context_id'],population_mode='reporter',calibration_domain_id=api.FINAL['calibration_domain_id'] if m['series']=='S7' else 'S10_NO_QUALIFIED_TRANSFER')
    if m['series']=='S7':assert r['res_mass_fraction']==pytest.approx(golden['RES_mass_fraction'],abs=1e-12)
    else:assert r['res_mass_fraction'] is None and r['hypothetical_incompatible_mapping'] is not None

def test_synthetic_signed_green_ratio_and_positive_denominator():
    cfg={'minimum_selected_events':2,'maximum_denominator_relative_se':1}
    z=score(np.array([-2.,4.]),np.array([2.,2.]),cfg)
    assert z['ras']==.5 and z['signed_green_negative_fraction']==.5
    assert score([2,3],[-1,-1],cfg)['ras'] is None
    assert score([1,np.nan],[1,1],cfg)['ras'] is None

def test_synthetic_population_difference_and_missing_editor():
    m=api.load_experiment(verify_hashes=False);row=m[m.acquisition_id=='S10_1_8_A'].iloc[0].to_dict();row['linked_editor_present']=True
    p=api.process_fcs(ROOT/row['file_path'],metadata=row)
    a=api.calculate_ras(p);b=api.calculate_ras(p,'blue_positive_reporter')
    assert b['n_selected']<a['n_selected'] and b['ras']!=a['ras']
    p['metadata']['linked_editor_present']=False
    assert api.calculate_ras(p,'blue_positive_reporter')['score_status']=='NOT_APPLICABLE_NO_LINKED_EDITOR'
    assert api.calculate_ras(p)['ras']==a['ras']

def test_synthetic_plateau_and_outside_inverse():
    m={'knots':[0,.5,1],'values':[1,1,2]}
    z=inverse(m,1);assert z['point'] is None and z['low']==0 and z['high']==.5
    assert z['status']=='NON_IDENTIFIABLE_PLATEAU'
    assert inverse(m,.5)['point'] is None
    assert inverse(m,np.nan)['status']=='UNAVAILABLE_INPUT'
    assert inverse({'knots':[0,1],'values':[2,1]},1.5)['status']=='NON_MONOTONE_MODEL'

def test_frozen_forward_inverse_round_trip():
    m=api.load_res_model()
    assert m['parameters']['k']==.5
    assert m['model_id']==m['calibration_model_id']==api.FINAL['model_id']
    for a in [0,.1,.5,.7,1]:assert inverse(m,api.forward_res(a,m))['point']==pytest.approx(a,abs=1e-12)
    assert api.forward_res(-.001,m) is None and api.forward_res(1.001,m) is None

def test_research_routine_transfer_and_determinism():
    kw={'context_id':api.FINAL['context_id'],'population_mode':'reporter','calibration_domain_id':api.FINAL['calibration_domain_id']}
    a=api.calculate_res(.95,**kw);b=api.calculate_res(.95,**kw)
    assert a==b and a['res_mass_fraction'] is not None
    assert api.calculate_res(.95,mode='routine',**kw)['res_mass_fraction'] is None
    kw['population_mode']='blue_positive_reporter'
    assert api.calculate_res(.95,**kw)['res_mass_fraction'] is None
    assert api.calculate_res(.2,**kw)['hypothetical_incompatible_mapping'] is None

def test_registered_uncertainty_does_not_attach_to_changed_value():
    with pytest.raises(ValueError,match='Registered sample'):
        api.calculate_res(.55,sample_id='S7_90B',context_id=api.FINAL['context_id'],population_mode='reporter',calibration_domain_id=api.FINAL['calibration_domain_id'])

def test_bootstrap_and_interval_contract():
    r=pd.read_csv(ROOT/'results/layer2/RES_Sample_Results.csv')
    assert (r.bootstrap_total_n==1000).all()
    assert ((r.bootstrap_success_n>=0)&(r.bootstrap_success_n<=r.bootstrap_total_n)).all()
    assert (r.compatibility_low<=r.compatibility_high).all()
    assert r[r.sample_id=='S7_5B'].bootstrap_success_fraction.iloc[0]<1
    assert r.routine_res_mass_fraction.isna().all()
    within=r[r.within_reference_response_screen]
    assert len(within)==2 and within.primary_sample_interval_narrow.all()
    assert not within.cross_model_sample_interval_narrow.any()
    assert sorted(within.cross_model_sample_width)==pytest.approx([.208,.218],abs=1e-12)

def test_full_cv_denominators_and_no_fold_leakage():
    d=pd.read_csv(ROOT/'results/layer2/RES_Inverse_Validation.csv')
    assert len(d)==120
    for row in d.itertuples():
        assert row.test_well not in row.train_wells.split(';')
    z=d[(d.model=='monotone_hinge_50')&(d.validation=='leave_one_reference_level_out')]
    assert len(z)==20 and z.recovered_AC_mass_fraction.notna().sum()==19
    assert z[z.held_input_within_training_domain].shape[0]==16

def test_missing_molecular_and_PER_restrictions(tmp_path):
    assert api.analyze_molecular_reference(tmp_path)['status']=='MOLECULAR_REFERENCE_MISSING'
    assert api.analyze_molecular_reference()['independent_wells']==12
    assert api.predict_per({})['PER'] is None
    model=api.fit_biological_calibration([[0],[1],[2],[3]],[0,.1,.2,.3])
    assert api.predict_per({},model)['PER_status']=='RELATIVE_INDEX_CANNOT_POPULATE_PER'
    with pytest.raises(ValueError):api.fit_biological_calibration([[0],[1],[2]],[0,.1,.2],endpoint='RNA_fraction')

def test_version_compatibility_failure(tmp_path):
    m=api.load_res_model();m['ras_estimator_id']='changed'
    p=tmp_path/'bad_model.json';p.write_text(json.dumps(m))
    with pytest.raises(ValueError,match='version'):api.load_res_model(p)
    c=api.load_context();c['kernel_sha256']='changed'
    with pytest.raises(ValueError,match='version'):api.process_fcs(ROOT/'inputs/S7/0A.fcs',context=c)

def test_new_research_fit_does_not_mutate_frozen_model():
    before=api.digest(ROOT/'models/res_primary/model.json')
    m=api.fit_reporter_calibration([0,0,.5,.5,1,1],[.5,.51,.75,.74,1.1,1.11])
    assert m['qualification'].startswith('NEW_RESEARCH')
    assert api.digest(ROOT/'models/res_primary/model.json')==before

def test_context_channel_rejection(monkeypatch):
    # Synthetic malformed channel header, explicitly not an experimental observation.
    import core
    class BadHeader:
        def __init__(self,*a):self.text={};self.pnn_labels=['missing_BFP']
    monkeypatch.setattr(core,'FlowData',BadHeader)
    with pytest.raises(ValueError,match='channel map'):core.read_fcs('synthetic')
