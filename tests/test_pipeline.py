import copy
import io
import json
from pathlib import Path
import zipfile

import pytest
from sonar_app.backend import Platform
from sonar_app.pipeline import UserPipeline

ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture(scope='module')
def pipeline(tmp_path_factory):
    return UserPipeline(Platform(ROOT/'scientific_reference',tmp_path_factory.mktemp('user-pipeline')))

@pytest.fixture(scope='module')
def quick(pipeline):
    spec=pipeline.example()
    return spec,pipeline.run(spec)

def test_uploaded_mock_theta_and_raw_goldens(pipeline,quick):
    spec,r=quick;s=r['samples'][0]
    frozen=pipeline.p.context['gate_parameters']
    for key in ['background','positivity_thresholds','red_quantitative_boundary']:
        assert r['Theta']['gate_parameters'][key]==pytest.approx(frozen[key],rel=1e-12)
    g=json.loads((ROOT/'scientific_reference/tests/golden_reference/real_samples.json').read_text())['S7_90B']
    for key in ['ras','n_selected','sum_G_corrected','sum_R_corrected','effective_red_events']:
        assert s['RAS'][key]==pytest.approx(g[key],rel=1e-12)
    assert s['RES']['model_estimate_res_mass_fraction']==pytest.approx(g['RES_mass_fraction'])
    assert s['RES']['res_mass_fraction'] is None
    assert s['RES']['application_status']=='S7_MODEL_ESTIMATE_TRANSFER_UNVALIDATED'
    assert s['RAS']['uncertainty']['repeats']==200

def test_theta_does_not_depend_on_outcome_labels(pipeline,quick):
    spec,r=quick;altered=copy.deepcopy(spec)
    altered['files'][-1]['condition_label']='different outcome label'
    again=pipeline.run(altered)
    assert again['Theta']==r['Theta']
    assert again['samples'][0]['RAS']==r['samples'][0]['RAS'] | {'experimental_condition':'different outcome label'}

@pytest.mark.parametrize('mutation,message',[
    ('no_mock','Mock'),('duplicate','唯一'),('missing_channel','通道'),('missing_identity','细胞类型')])
def test_invalid_batches_rejected(pipeline,quick,mutation,message):
    s=copy.deepcopy(quick[0])
    if mutation=='no_mock':
        for f in s['files']:f['role']='sample'
    if mutation=='duplicate':s['files'].append(s['files'][-1].copy())
    if mutation=='missing_channel':s['channel_map']['EGFP']=''
    if mutation=='missing_identity':s['cell_type']=''
    with pytest.raises(ValueError,match=message):pipeline.run(s)

def test_optional_bfp_is_missing_not_zero(pipeline,quick):
    s=copy.deepcopy(quick[0]);s['channel_map']['BFP']=''
    r=pipeline.run(s)
    assert r['Theta']['channel_summary']['BFP']['background'] is None
    assert r['samples'][0]['qc']['BFP_positive_singlets'] is None
    assert r['samples'][0]['RAS']['ras']==pytest.approx(quick[1]['samples'][0]['RAS']['ras'])
    s['population']='blue_positive_reporter'
    with pytest.raises(ValueError,match='BFP'):pipeline.run(s)

def test_one_mock_and_inapplicable_editor_population(pipeline,quick):
    s=copy.deepcopy(quick[0]);s['files'].pop(1);s['population']='blue_positive_reporter'
    r=pipeline.run(s)
    assert r['Theta']['control_scope']=='ONE_MOCK_NO_INDEPENDENT_CONTROL'
    assert r['samples'][0]['RAS']['ras'] is None
    assert r['samples'][0]['RES']['model_estimate_res_mass_fraction'] is None

def test_batch_calibration_applies_to_uploaded_samples(pipeline):
    spec=pipeline.example(True)
    assert len(spec['files'])==22
    r=pipeline.run(spec)
    assert r['model']['reference_n']==20
    assert len(r['model']['validation'])==20
    assert r['model']['values']==pytest.approx(pipeline.p.model['values'],rel=1e-12)
    s=next(s for s in r['samples'] if s['sample_id']=='S7_90B')
    assert s['RES']['research_res_mass_fraction']==pytest.approx(.7454898213131971)
    assert s['RES']['routine_res_mass_fraction'] is None
    assert s['RES']['bootstrap_total_n']==200
    assert s['RES']['application_status']=='SAME_BATCH_RESEARCH_MODEL'
    assert r['model']['uncertainty']['successful_model_draws']>0

def test_export_can_reproduce_elsewhere(pipeline,quick,tmp_path):
    r=quick[1];payload=pipeline.export(r['run_id'])
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        assert {'Theta.json','model.json','results.json','measurements.csv','report.html','batch.json','artifact_manifest.json'}<=set(z.namelist())
        z.extractall(tmp_path)
    rerun=pipeline.rerun(tmp_path)
    assert rerun['Theta']==r['Theta']
    assert rerun['samples']==r['samples']
    assert rerun['run_id']!=r['run_id']

def test_saved_output_tampering_is_rejected(pipeline,quick):
    r=quick[1];path=pipeline.p.workspace/'analyses'/r['run_id']/'Theta.json'
    original=path.read_bytes()
    try:
        path.write_bytes(original+b' ')
        with pytest.raises(ValueError,match='变化'):pipeline.load(r['run_id'])
    finally:path.write_bytes(original)
