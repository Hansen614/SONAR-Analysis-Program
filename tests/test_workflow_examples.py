"""Example entry points must use the real pipeline without changing user runs."""
from pathlib import Path
import hashlib
import pytest
from sonar_app.backend import Platform
from sonar_app.experiments import Experiments

ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture(scope='module')
def examples(tmp_path_factory):
    return Experiments(Platform(ROOT/'scientific_reference',tmp_path_factory.mktemp('example-workspace')))

@pytest.mark.parametrize('stage',['mock_upload','theta_ready','sample_upload','complete'])
def test_example_stages_are_real_and_isolated(examples,stage):
    user=examples.create('user control',str(examples.p.workspace/'user'))
    before={str(p):p.read_bytes() for p in Path(user['save_path']).rglob('*') if p.is_file()}
    d=examples.example(stage)
    assert d['status']==stage
    assert d['experiment_id']!=user['experiment_id']
    assert Path(d['save_path']).parent==examples.p.workspace/'examples'
    assert len([f for f in d['files'] if f['stage']=='mock'])==2
    for f in d['files']:
        source=examples.p.root/'inputs/S7'/f['original_filename']
        assert hashlib.sha256(source.read_bytes()).hexdigest()==f['sha256']
    assert {str(p):p.read_bytes() for p in Path(user['save_path']).rglob('*') if p.is_file()}==before
    if stage!='mock_upload':
        assert d['Theta']['cell_type']=='HEK293T'
    if stage in ('sample_upload','complete'):
        assert d['confirmed_theta_sha256']==d['theta_sha256']
        assert len([f for f in d['files'] if f['stage']=='sample'])==1
    if stage=='complete':
        assert d['result']['workflow']['theta_reused_without_refit'] is True
        assert (Path(d['save_path'])/'SONAR_report.zip').is_file()
        assert d['result']['samples'][0]['RES']['model_estimate_res_mass_fraction']==pytest.approx(.7454898213131971,rel=1e-12)
        assert d['result']['samples'][0]['RES']['res_mass_fraction'] is None
        assert d['result']['samples'][0]['RAS']['ras']==pytest.approx(.9562602659677872,rel=1e-12)


def test_bad_stage_has_no_side_effect(examples):
    before=examples.list()
    with pytest.raises(ValueError):examples.example('../complete')
    assert examples.list()==before
