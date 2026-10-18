import sys,json,hashlib
from pathlib import Path
import numpy as np,pandas as pd
from Bio import SeqIO
from Bio.Seq import Seq
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from layer23_common import CFG,assert_upstream
from amplicon_reconstruction import F,R,assemble_pair
from ab1_processing import read_ab1,reference_map,site_metrics,original_index
from reporter_calibration import fit_model,inverse,predict

def test_frozen_upstream_hashes():assert_upstream()
def test_reference_reconstructed_from_all_four_original_pairs():
    ref=str(SeqIO.read(ROOT/'results/molecular/OpenA_amplicon_consensus.fasta','fasta').seq)
    for i in range(1,5):
        f=read_ab1(next((ROOT/'inputs/S10/测序').rglob(f'1-0-{i}.F.*.ab1')));r=read_ab1(next((ROOT/'inputs/S10/测序').rglob(f'1-0-{i}.R.*.ab1')))
        seq,info=assemble_pair(f,r);assert seq==ref and len(seq)==523
    assert ref.startswith(F) and ref.endswith(str(Seq(R).reverse_complement()))
    assert ref[279:282]=='CGA' and str(Seq('TGA').translate())=='*'
def test_quality_support_not_invented_at_terminals():
    d=pd.read_csv(ROOT/'results/molecular/OpenA_reference_alignment.csv')
    assert len(d)==523 and (d.Q20_n>0).sum()==494
    assert ((d.Q20_F_n>0)&(d.Q20_R_n>0)).sum()==393
    assert d.loc[d.Q20_n==0,'evidence_status'].eq('PRIMER_INFERRED_NO_Q20').all()
    assert d.loc[d.position_1based==280,'independent_wells_supporting'].iloc[0]==2
    assert d.loc[d.Q20_n>0,'Q20_agreement_fraction'].eq(1).all()
def test_alignment_export_preserves_ungapped_sources():
    records=list(SeqIO.parse(ROOT/'results/molecular/OpenA_vs_generic.aligned.fasta','fasta'))
    ref=SeqIO.read(ROOT/'results/molecular/OpenA_amplicon_consensus.fasta','fasta')
    assert len(records)==2 and len(records[0])==len(records[1])
    assert str(records[1].seq).replace('-','')==str(ref.seq)
    assert len(str(records[0].seq).replace('-',''))==544

def test_dye_mapping_and_reverse_coordinate_are_read_specific():
    ref=str(SeqIO.read(ROOT/'results/molecular/OpenA_amplicon_consensus.fasta','fasta').seq)
    metrics=pd.read_csv(ROOT/'results/molecular/S10_read_level_peak_metrics.csv')
    for row in metrics.itertuples():
        r=read_ab1(ROOT/row.source_AB1);mapping,_=reference_map(ref,r);j=mapping[279];orig=original_index(r,j)
        assert orig+1==row.AB1_base_index_1based
        assert r['loc'][orig]==row.scan_index_0based
        base,alt=('C','T') if r['direction']=='F' else ('G','A')
        assert (base,alt)==(row.trace_reference_base,row.trace_alternative_base)
        loc=r['loc'][orig];expected=r['traces'][alt][loc]/(r['traces'][alt][loc]+r['traces'][base][loc])
        assert np.isclose(expected,row.raw_peak_ratio,rtol=1e-12)
        assert row.dye_order==r['order']
def test_low_quality_alignment_read_remains_auditable_but_unavailable():
    d=pd.read_csv(ROOT/'results/molecular/S10_read_level_peak_metrics.csv');q=d[(d.sample_label=='1-8-2')&(d.direction=='F')].iloc[0]
    assert len(d)==48 and d.eligible.sum()==47
    assert q.flank_identity==.6 and not q.eligible and pd.isna(q.qualified_signal)
    assert np.isfinite(q.raw_peak_ratio)
    assert 'LOW_FLANK_ALIGNMENT_IDENTITY' in q.failure_reasons

def test_technical_reads_not_independent_wells():
    w=pd.read_csv(ROOT/'results/molecular/S10_well_level_molecular_results.csv');p=pd.read_csv(ROOT/'results/molecular/S10_bidirectional_concordance.csv')
    assert len(w)==12 and w.independent_well_n.sum()==12 and len(p)==24
    assert (w.groupby('dose_ratio').size()==2).all() and p.complete_pair.sum()==23
    assert (w.complete_molecular_pairs==1).sum()==1 and w.RNA_editing_fraction.isna().all()
    only=w[w.complete_molecular_pairs==1].iloc[0];assert pd.isna(only.technical_mean_SE)

def test_mass_axis_and_inverse_roundtrip():
    # Synthetic fixtures exercise mathematics, never appear in scientific outputs.
    model=fit_model('affine',[0,.5,1],[.2,.7,1.2])
    assert np.isclose(inverse(model,.7)['point'],.5)
    assert inverse(model,1.3)['status']=='OUT_OF_CALIBRATION_RANGE'
    d=pd.read_csv(ROOT/'results/calibration/S7_RES_results.csv');assert d.known_AC_mass_fraction.min()==0 and d.known_AC_mass_fraction.max()==1
    assert set(d.known_AC_mass_fraction)=={0,.05,.15,.2,.3,.4,.5,.75,.9,1}

def test_plateau_has_interval_never_point_or_clipping():
    m={'knots':[0,.2,.6,1],'values':[.3,.5,.5,1.]}
    inv=inverse(m,.5);assert inv['status']=='NON_IDENTIFIABLE_PLATEAU' and inv['point'] is None
    assert np.isclose(inv['low'],.2) and np.isclose(inv['high'],.6)
    assert inverse(m,.2)['point'] is None and inverse(m,1.1)['point'] is None

def test_grouped_prediction_has_no_well_or_dose_leakage():
    v=pd.read_csv(ROOT/'results/prediction/S10_prediction_validation.csv');pairs=pd.read_csv(ROOT/'results/prediction/S10_flow_molecular_pairs.csv').set_index('well_id')
    for row in v.itertuples():
        train=row.train_wells.split(';');assert row.test_well not in train
        if row.validation=='leave_one_dose_out':assert (pairs.loc[train,'condition_label']!=row.test_dose).all()
    assert v.PER.isna().all() and pairs.PER.isna().all()

def test_no_unsupported_staged_PER_or_validated_RES():
    s=pd.read_csv(ROOT/'results/prediction/S10_staged_model_results.csv');r=pd.read_csv(ROOT/'results/calibration/S7_RES_results.csv')
    assert not s.fitted.any() and s.PER.isna().all() and r.RES_validated.isna().all()
    d=pd.read_csv(ROOT/'results/prediction/S10_affine_transform_sensitivity.csv');assert len(d)==24 and d.difference.abs().max()<1e-12

def test_confirmed_cell_type_and_figure_sources():
    d=pd.read_csv(ROOT/'inventory/acquisition_manifest.csv');assert d.loc[d.sample_role!='Mock','cell_type'].eq('HEK293T').all()
    idx=pd.read_csv(ROOT/'figures/layer23/figure_index.csv')
    for r in idx.itertuples():
        for p in r.source_tables.split(';'):assert (ROOT/p).is_file()
        assert (ROOT/'figures/layer23'/f'{r.figure_id}.png').stat().st_size>1000

def test_serialized_models_pin_upstream_reference_and_configuration():
    from inventory import sha
    for filename in ['S7_calibration_models.json','S10_exploratory_signal_models.json']:
        models=json.loads((ROOT/'models/layer23'/filename).read_text())
        for model in models.values():
            assert model['upstream_RAS_sha256']==sha(ROOT/'results/ras_results.csv')
            expected=ROOT/('baselines/v3/config/layer23.json' if filename.startswith('S10') else 'config/layer23.json')
            assert model['provenance']['layer23_config_sha256']==sha(expected)
            assert model['provenance']['source_manifest_sha256']==sha(ROOT/'reference/layer23/source_manifest.json')
            if filename.startswith('S10'):
                assert model['provenance']['reference_sha256']==sha(ROOT/'results/molecular/OpenA_amplicon_consensus.fasta')
                assert model['provenance']['molecular_results_sha256']==sha(ROOT/'results/molecular/S10_well_level_molecular_results.csv')

def test_event_distribution_counts_preserve_all_selected_events():
    d=pd.read_csv(ROOT/'results/calibration/S7_anomaly_distributions.csv')
    grouped=d.groupby(['acquisition_id','channel'])
    assert len(grouped)==12
    for (aid,ch),z in grouped:
        mask=np.load(ROOT/'masks'/f'{aid}.npz')['reporter']
        assert z.events.sum()==mask.sum()
        assert np.isclose(z.fraction.sum(),1)
