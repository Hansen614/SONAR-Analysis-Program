import sys,json
from pathlib import Path
import numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from s7_correction import CORR,BASE,verify_frozen
from inventory import sha

def test_exact_four_authorized_assignments_keep_original_ids_and_prior_15():
    d=pd.read_csv(ROOT/'inventory/S7_corrected_manifest.csv').set_index('acquisition_id')
    changed=d.corrected_ac_mass_fraction!=d.pre_correction_ac_mass_fraction
    assert set(d.index[changed])==set(CORR['swap_by_acquisition_id'])
    for aid,value in CORR['swap_by_acquisition_id'].items():
        row=d.loc[aid];assert row.corrected_ac_mass_fraction==value
        assert row.original_filename==aid.replace('S7_','')+'.fcs'
        assert row.original_acquisition_id==aid and row.correction_source==CORR['correction_source']
        assert row.correction_status==CORR['correction_status']
    for aid in ['S7_10A','S7_10B']:
        assert d.loc[aid,'original_ac_mass_fraction']==.10 and d.loc[aid,'pre_correction_ac_mass_fraction']==.15 and d.loc[aid,'corrected_ac_mass_fraction']==.15

def test_unchanged_measurements_and_figures_are_byte_preserved():
    assert verify_frozen()>100
    a=json.loads((ROOT/'results/prediction/S10_prediction_summary.json').read_text());b=json.loads((BASE/'results/prediction/S10_prediction_summary.json').read_text())
    assert a['models']==b['models'] and a['primary_signal_index']==b['primary_signal_index']

def test_calibration_joins_current_input_by_acquisition_not_frozen_label():
    s=pd.read_csv(ROOT/'results/calibration/S7_reference_response_corrected.csv').set_index('acquisition_id');raw=pd.read_csv(ROOT/'results/ras_results.csv');raw=raw[(raw.series=='S7')&(raw.population_mode=='reporter')].set_index('acquisition_id')
    assert len(s)==20
    for aid in s.index:
        assert s.loc[aid,'ras']==raw.loc[aid,'ras']
        assert s.loc[aid,'event_control_ci_low']==raw.loc[aid,'event_control_ci_low']
    p=pd.read_csv(ROOT/'results/calibration/S7_calibration_predictions.csv')
    for row in p.itertuples():assert row.AC_mass_fraction==s.loc[row.acquisition_id,'corrected_ac_mass_fraction']

def test_reference_level_holdouts_follow_corrected_labels():
    s=pd.read_csv(ROOT/'results/calibration/S7_reference_response_corrected.csv').set_index('acquisition_id');v=pd.read_csv(ROOT/'results/calibration/S7_internal_validation.csv')
    for row in v.itertuples():
        assert row.test_well not in row.train_wells.split(';')
        assert row.true_AC_mass_fraction==s.loc[row.test_well,'corrected_ac_mass_fraction']
        if row.validation=='leave_one_reference_level_out':assert (s.loc[row.train_wells.split(';'),'corrected_ac_mass_fraction']!=row.true_AC_mass_fraction).all()

def test_model_coefficients_and_R2_match_actual_corrected_observations():
    s=pd.read_csv(ROOT/'results/calibration/S7_reference_response_corrected.csv');x=s.corrected_ac_mass_fraction.to_numpy();y=s.ras.to_numpy();coef=np.linalg.lstsq(np.c_[np.ones(len(x)),x],y,rcond=None)[0]
    models=json.loads((ROOT/'models/layer23/S7_calibration_models.json').read_text());np.testing.assert_allclose(models['affine']['coefficients'],coef,rtol=1e-12)
    r2=1-np.sum((y-np.c_[np.ones(len(x)),x]@coef)**2)/np.sum((y-y.mean())**2)
    metrics=pd.read_csv(ROOT/'results/calibration/S7_model_comparison.csv');assert np.isclose(metrics[metrics.model=='affine'].training_R2.iloc[0],r2)
    for m in models.values():assert m['label_correction_sha256']==sha(ROOT/'config/s7_label_correction.json') and m['reference_basis_id']==CORR['reference_basis_id']

def test_high_plateau_no_forced_inverse_and_status_domains_explicit():
    from inverse_calibration import inverse
    models=json.loads((ROOT/'models/layer23/S7_calibration_models.json').read_text());m=models['isotonic'];ii=inverse(m,m['values'][-1]);assert ii['point'] is None and np.isclose(ii['low'],.9) and ii['high']==1
    d=pd.read_csv(ROOT/'results/calibration/S7_RES_results.csv');assert set(d.RES_status)<=set(CORR['status_definitions']);assert d.RES_validated.isna().all()
    assert d.population_mode.eq('reporter').all() and d.reference_basis_id.eq(CORR['reference_basis_id']).all()
    s=pd.read_csv(ROOT/'results/calibration/S10_hypothetical_S7_mapping.csv');assert s.RES_status.eq('NOT_CALIBRATED').all() and s.RES_validated.isna().all()

def test_joint_inverse_screen_requires_both_models_and_untruncated_sets():
    d=pd.read_csv(ROOT/'results/calibration/S7_cross_model_inverse_support.csv');good=d[d.joint_narrow_interior]
    assert len(good)>0 and good.isotonic_point.notna().all() and good.hinge_point.notna().all()
    assert (good.union_compatible_low>0).all() and (good.union_compatible_high<1).all() and (good.union_width<=.2+1e-12).all()
    m=pd.read_csv(ROOT/'results/calibration/S7_matched_inverse_validation.csv')
    for _,q in m.groupby('validation'):assert q.common_wells.nunique()==1 and q.common_well_n.nunique()==1
