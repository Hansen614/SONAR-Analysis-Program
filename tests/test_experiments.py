from pathlib import Path
import io
import json
import zipfile

import pytest
from sonar_app.backend import Platform
from sonar_app.experiments import Experiments
from sonar_app.pipeline import UserPipeline
from sonar_app.measurement import MeasurementPipeline
from sonar_app.experiments import UNSPECIFIED

ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture
def workflow(tmp_path):
    return Experiments(Platform(ROOT/'scientific_reference',tmp_path/'app-workspace'))

def put(w, d, stage, name):
    return w.upload(d['experiment_id'],stage,(w.p.root/'inputs/S7'/name).read_bytes(),name)

def layer0(w,tmp_path):
    d=w.create('分步流程实际 FCS 测试',str(tmp_path/'chosen-output'))
    d=put(w,d,'mock','MOCK1.fcs');d=put(w,d,'mock','MOCK2.fcs')
    return w.analyze_mock(d['experiment_id'],'HEK293T',d['channel_map'])

def settings(d):
    return {'reporter_construct':'S7 reference','files':[f for f in d['files'] if f['stage']=='sample']}

def test_destination_created_without_overwriting(workflow,tmp_path):
    parent=tmp_path/'chosen';parent.mkdir();(parent/'existing.txt').write_text('keep')
    a=workflow.create('same experiment',str(parent));b=workflow.create('same experiment',str(parent))
    assert a['save_path']!=b['save_path']
    assert (parent/'existing.txt').read_text()=='keep'
    assert Path(a['save_path']).parent==parent
    assert a['status']=='mock_upload'
    restored=Experiments(workflow.p).snapshot(a['experiment_id'])
    assert restored==a

def test_only_mock_needed_for_layer0_and_explicit_confirmation(workflow,tmp_path):
    d=workflow.create('Mock only',str(tmp_path));eid=d['experiment_id']
    with pytest.raises(ValueError,match='Layer 0'):put(workflow,d,'sample','90B.fcs')
    with pytest.raises(ValueError,match='Layer 0'):workflow.confirm_theta(eid)
    d=put(workflow,d,'mock','MOCK1.fcs')
    d=workflow.analyze_mock(eid,'HEK293T',d['channel_map'])
    assert d['status']=='theta_ready' and d['result'] is None
    assert len(d['Theta']['controls'])==1
    assert (Path(d['save_path'])/'layer0/Theta.json').exists()
    with pytest.raises(ValueError,match='Confirm'):put(workflow,d,'sample','90B.fcs')
    confirmed=workflow.confirm_theta(eid)
    assert confirmed['confirmed_theta_sha256']==confirmed['theta_sha256']
    assert confirmed['status']=='sample_upload'

def test_final_run_reuses_theta_without_refitting(workflow,tmp_path,monkeypatch):
    d=layer0(workflow,tmp_path);theta=d['Theta'];saved_hash=d['theta_sha256']
    d=workflow.confirm_theta(d['experiment_id']);d=put(workflow,d,'sample','90B.fcs')
    def forbidden(*args,**kwargs):raise AssertionError('Layer 0 must not be refitted during sample calculation')
    monkeypatch.setattr(UserPipeline,'theta',forbidden)
    monkeypatch.setattr(workflow.pipe.core,'fit_gates',forbidden)
    done=workflow.compute(d['experiment_id'],settings(d))
    assert done['status']=='complete';r=done['result']
    assert r['Theta']==theta and done['result_theta_sha256']==saved_hash
    assert r['samples'][0]['RAS']['ras']==pytest.approx(.9562602659677872,rel=1e-12)
    assert r['samples'][0]['RES']['model_estimate_res_mass_fraction']==pytest.approx(.7454898213131971,rel=1e-12)
    assert r['workflow']['theta_reused_without_refit'] is True
    base=Path(done['save_path'])
    assert all((base/n).exists() for n in ('SONAR_report.zip','measurements.csv','report.html','experiment.json'))
    with zipfile.ZipFile(io.BytesIO(workflow.export(d['experiment_id']))) as z:
        assert json.loads(z.read('Theta.json'))==theta
        assert len([n for n in z.namelist() if n.endswith('.fcs')])==3
    assert Experiments(workflow.p).snapshot(d['experiment_id'])['result']==r

def test_mock_revision_invalidates_confirmation_and_result(workflow,tmp_path):
    d=layer0(workflow,tmp_path);d=workflow.confirm_theta(d['experiment_id']);d=put(workflow,d,'sample','90B.fcs')
    done=workflow.compute(d['experiment_id'],settings(d))
    changed=workflow.remove_file(d['experiment_id'],d['files'][0]['file_id'])
    assert changed['status']=='mock_upload'
    assert changed['result'] is None and changed['confirmed_theta_sha256'] is None
    with pytest.raises(ValueError,match='Layer 0'):workflow.compute(d['experiment_id'],settings(changed))
    assert (Path(done['save_path'])/'analyses'/done['result_id']/'results.json').exists()

@pytest.mark.parametrize('target',['Theta','mock'])
def test_control_or_theta_tampering_blocks_compute(workflow,tmp_path,target):
    d=layer0(workflow,tmp_path);d=workflow.confirm_theta(d['experiment_id'])
    base=Path(d['save_path'])
    p=base/('layer0/Theta.json' if target=='Theta' else d['files'][0]['file_path'])
    p.write_bytes(p.read_bytes()+b' ')
    with pytest.raises(ValueError,match='changed'):workflow.compute(d['experiment_id'],settings(d))

def test_duplicate_files_and_missing_sample_are_explicit(workflow,tmp_path):
    d=layer0(workflow,tmp_path)
    with pytest.raises(ValueError,match='already exists'):put(workflow,d,'mock','MOCK1.fcs')
    d=workflow.confirm_theta(d['experiment_id'])
    with pytest.raises(ValueError,match='at least one sample'):workflow.compute(d['experiment_id'],settings(d))

def test_folder_picker_lists_directories_only(workflow,tmp_path):
    (tmp_path/'child').mkdir();(tmp_path/'private.txt').write_text('not returned')
    listing=workflow.folders(str(tmp_path))
    assert 'child' in [f['name'] for f in listing['directories']]
    assert 'private.txt' not in [f['name'] for f in listing['directories']]
    with pytest.raises(ValueError,match='scientific reference'):workflow.create('wrong location',str(workflow.p.root))


def test_optional_metadata_defaults_notes_and_portable_report(workflow,tmp_path):
    d=workflow.create('Optional advanced options',str(tmp_path/'saved'))
    d=put(workflow,d,'mock','MOCK1.fcs');d=put(workflow,d,'mock','MOCK2.fcs')
    eid=d['experiment_id']
    d=workflow.analyze_mock(eid,'',d['channel_map'],'first note')
    theta=d['Theta'];theta_hash=d['theta_sha256']
    assert d['cell_type']==UNSPECIFIED
    note='批次备注\n<script>alert("note")</script> & changed condition'
    d=workflow.analyze_mock(eid,'',d['channel_map'],note)
    assert d['Theta']==theta and d['theta_sha256']==theta_hash
    assert Experiments(workflow.p).snapshot(eid)['experiment_notes']==note
    d=workflow.confirm_theta(eid);d=put(workflow,d,'sample','90B.fcs')
    done=workflow.compute(eid,{'files':[f for f in d['files'] if f['stage']=='sample']})
    result=done['result']
    assert result['cell_type']==result['reporter_construct']==UNSPECIFIED
    assert result['experiment_notes']==note and result['specification']['experiment_notes']==note
    assert result['Theta']==theta
    assert result['samples'][0]['RAS']['ras']==pytest.approx(.9562602659677872,rel=1e-12)
    extracted=tmp_path/'report';extracted.mkdir()
    with zipfile.ZipFile(io.BytesIO(workflow.export(eid))) as z:
        assert json.loads(z.read('results.json'))['experiment_notes']==note
        html=z.read('report.html').decode()
        assert '&lt;script&gt;' in html and '<script>' not in html
        z.extractall(extracted)
    rerun=MeasurementPipeline(Platform(workflow.p.root,tmp_path/'rerun')).rerun(extracted)
    assert rerun['experiment_notes']==note
    assert rerun['Theta']==theta and rerun['samples']==result['samples']
