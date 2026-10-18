import sys,json
from pathlib import Path
import numpy as np,pandas as pd
import pytest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from core import score,read_fcs,gate,G,R,B
from inventory import sha

CFG=json.loads((ROOT/'config/analysis.json').read_text())
TESTCFG={**CFG,'minimum_selected_events':2,'maximum_denominator_relative_se':1}

def test_signed_green_and_ratio_of_sums():
    # Synthetic numbers are unit-test fixtures, never experimental observations.
    g=np.array([-2.,12.]);r=np.array([2.,6.]);s=score(g,r,TESTCFG)
    assert s['ras']==1.25 and s['ras']!=np.mean(g/r)
def test_common_scale_and_duplication_invariance():
    g=np.array([1.,4.,9.]);r=np.array([2.,3.,4.]);base=score(g,r,TESTCFG)['ras']
    assert score(g*10,r*10,TESTCFG)['ras']==base
    assert score(np.tile(g,2),np.tile(r,2),TESTCFG)['ras']==base
def test_green_only_rescaling_changes_score():
    g=np.array([1.,4.,9.]);r=np.array([2.,3.,4.]);assert score(g*2,r,TESTCFG)['ras']==2*score(g,r,TESTCFG)['ras']
@pytest.mark.parametrize('r',[[-1.,-2.],[0.,0.]])
def test_no_epsilon_on_invalid_denominator(r):
    out=score([1.,2.],r,TESTCFG);assert out['ras'] is None and out['score_status']=='NOT_ESTIMABLE'
def test_no_green_rectification():
    assert score([-3.,-1.],[2.,2.],TESTCFG)['ras']==-1
def test_nonfinite_unavailable():
    assert score([float('nan'),2.],[2.,2.],TESTCFG)['ras'] is None
def test_pair_length_guard():
    with pytest.raises(ValueError):score([1.],[1.,2.],TESTCFG)
def test_duplicate_controls_not_independent_samples():
    d=pd.read_csv(ROOT/'inventory/acquisition_file_manifest.csv');u=pd.read_csv(ROOT/'inventory/acquisition_manifest.csv')
    assert len(d)==36 and len(u)==34 and d.is_duplicate_file.sum()==2
    assert u.sha256.nunique()==34 and u.event_data_sha256.nunique()==34
def test_raw_integrity_all_supplied_files():
    d=pd.read_csv(ROOT/'inventory/input_files.csv')
    for row in d.itertuples():
        assert sha(ROOT/row.packaged_path)==row.sha256
        if Path(row.original_path).exists():assert sha(row.original_path)==row.sha256
def test_independent_byte_reader_agreement():
    d=pd.read_csv(ROOT/'inventory/reader_crosscheck.csv');assert len(d)==36
    assert (d.max_reader_difference==0).all() and (d.max_linearization_difference==0).all()
def test_all_primary_results_against_raw_bytes_and_masks():
    results=pd.read_csv(ROOT/'results/ras_results.csv');manifest=pd.read_csv(ROOT/'inventory/acquisition_manifest.csv').set_index('acquisition_id')
    ctx=json.loads((ROOT/'contexts/context.json').read_text());bg=np.array(ctx['background'])
    for row in results.itertuples():
        p=ROOT/manifest.loc[row.acquisition_id,'file_path'];blob=p.read_bytes();start=int(blob[26:34]);stop=int(blob[34:42]);raw=np.frombuffer(blob[start:stop+1],dtype='<f4').reshape(-1,12).astype(float)
        m=np.load(ROOT/'masks'/f'{row.acquisition_id}.npz')[row.population_mode]
        assert m.sum()==row.n_selected
        sr=(raw[m,R]-bg[R]).sum();sg=(raw[m,G]-bg[G]).sum()
        assert np.isclose(sr,row.sum_R_corrected,rtol=1e-12) and np.isclose(sg,row.sum_G_corrected,rtol=1e-12)
        if np.isfinite(row.ras):assert np.isclose(sg/sr,row.ras,rtol=1e-12)
def test_partition_identity():
    d=pd.read_csv(ROOT/'results/partition_identity.csv');assert d.reconstruction_error.abs().max()<1e-12
def test_unsupported_calibrations_never_zero():
    d=pd.read_csv(ROOT/'results/ras_results.csv');assert d.RES.isna().all() and d.PER.isna().all() and d.validated_RAS.isna().all()
def test_no_green_gate_in_primary_population():
    d=pd.read_csv(ROOT/'results/ras_results.csv');assert d[d.population_mode=='reporter'].signed_green_negative_fraction.min()>0
def test_gate_reapplication():
    ctx=json.loads((ROOT/'contexts/context.json').read_text());d=pd.read_csv(ROOT/'inventory/acquisition_manifest.csv')
    for row in d.itertuples():
        x,_=read_fcs(ROOT/row.file_path);_,_,s,_,_=gate(x,ctx,CFG);m=np.load(ROOT/'masks'/f'{row.acquisition_id}.npz')
        assert np.array_equal(s,m['singlet'])
        assert np.array_equal(s&(x[:,R]>ctx['red_quantitative_boundary']),m['reporter'])
def test_figure_sources_exist():
    d=pd.read_csv(ROOT/'figures/figure_index.csv')
    for row in d.itertuples():
        for p in row.source_tables.split(';'):assert (ROOT/p).is_file()
        assert (ROOT/'figures'/f'{row.figure_id}.png').stat().st_size>1000
def test_only_authorized_plate_block():
    d=pd.read_csv(ROOT/'results/plate_raw_points.csv');assert not d.sample_label.str.contains('ac',case=False).any()
    assert set(d[d.kind=='PBS_spatial_scan'].well)=={'A01'}

def test_user_confirmed_mass_axis_preserves_source_labels():
    d=pd.read_csv(ROOT/'inventory/acquisition_manifest.csv')
    s=d[(d.series=='S7')&(d.sample_role!='Mock')]
    assert sorted(s.condition_label.unique())==[0,5,15,20,30,40,50,75,90,100]
    corrected=s[s.source_condition_label==10]
    assert len(corrected)==2 and (corrected.condition_label==15).all()
    assert set(corrected.acquisition_id)=={'S7_10A','S7_10B'}
    assert (s.ac_fraction_basis=='mass').all()

def test_confirmed_transfection_unit_and_derived_doses():
    d=pd.read_csv(ROOT/'inventory/acquisition_manifest.csv')
    exp=d[d.sample_role!='Mock']
    assert exp.well_id.nunique()==32
    assert (exp.groupby(['series','condition_label']).well_id.nunique()==2).all()
    s=exp[exp.series=='S10']
    assert (s.reporter_dna_ng==100).all() and (s.total_dna_ng==1000).all()
    np.testing.assert_array_equal(s.editor_dna_ng,s.condition_label*100)
    np.testing.assert_array_equal(s.editor_dna_ng+s.reporter_dna_ng+s.balancing_dna_ng,s.total_dna_ng)
    assert s.editor_bfp_linked.eq(True).all()

def test_two_molecular_labels_share_one_parent_well():
    d=pd.read_csv(ROOT/'inventory/molecular_pairing_registry.csv')
    w=pd.read_csv(ROOT/'results/flow_RNA_well_registry.csv')
    assert len(d)==24 and len(w)==12
    assert (d.groupby('grouped_validation_unit').size()==2).all()
    assert (w.groupby('condition_label').independent_transfection_well_n.sum()==2).all()
    assert (w.read_n==4).all() and (w.molecular_label_n==2).all()
    for r in d.itertuples():
        expected='A' if int(r.molecular_sample_label.split('-')[-1]) in [1,2] else 'B'
        assert r.flow_replicate==expected and r.flow_acquisition_pair.endswith('_'+expected)
        assert r.grouped_validation_unit==r.well_id
    assert set(d.flow_acquisition_pair)==set(w.flow_acquisition_id)
    assert d.RNA_origin_user_confirmed.all()
    assert not d.RNA_origin_assay_validated.any()
    assert (d.RNA_sampling_relation=='same_experimental_timepoint_RNA_extracted_after_flow').all()
    assert d.flow_to_extraction_elapsed_minutes.isna().all()
    assert w.RNA_editing_fraction.isna().all()

def test_editor_mode_excludes_no_editor_control_tail():
    d=pd.read_csv(ROOT/'results/ras_results.csv')
    s=d[d.series=='S10'];positive=s[s.condition_label>0];zero=s[s.condition_label==0]
    assert (positive.coexpression_claim_status=='LINKAGE_USER_CONFIRMED_OPTICAL_BOUNDARY_PROVISIONAL').all()
    assert positive.CEF_editor_exploratory.notna().all()
    assert zero.CEF_editor_exploratory.isna().all()
    assert d.CEF_editor_verified.isna().all()
    q=positive[positive.population_mode=='blue_positive_reporter']
    assert len(q)==10 and (q.population_interpretation=='reporter_editor_coexpression_exploratory').all()
    assert q.ras.notna().all()

def test_repeatability_counts_available_wells_not_events_or_reads():
    d=pd.read_csv(ROOT/'results/repeatability.csv')
    assert (d[d.population_mode=='reporter'].verified_independent_well_n==2).all()
    unavailable=d[(d.series=='S10')&(d.condition_label==0)&(d.population_mode=='blue_positive_reporter')&(d.metric=='ras')]
    assert len(unavailable)==1 and unavailable.verified_independent_well_n.iloc[0]==0
    assert unavailable.cv_percent.isna().all()
