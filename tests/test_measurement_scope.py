from pathlib import Path
import hashlib
import io
import json
import zipfile

import pytest
from sonar_app.backend import Platform
from sonar_app.measurement import MeasurementPipeline
from sonar_app.pipeline import UserPipeline
from sonar_app.scope import measurement_data

ROOT=Path(__file__).resolve().parents[1]


def test_scope_projection_preserves_measurements_and_user_text():
    original={'PER':None,'PER_status':'unused','samples':[{'relative_molecular':{'signal':.5},'RAS':{'ras':.9},
               'RES':{'res_mass_fraction':None},'condition_label':'PER is a user-supplied sample name'}]}
    projected=measurement_data(original)
    assert 'PER' not in projected and 'PER_status' not in projected
    assert 'relative_molecular' not in projected['samples'][0]
    assert projected['samples'][0]['RAS']==original['samples'][0]['RAS']
    assert projected['samples'][0]['RES']==original['samples'][0]['RES']
    assert projected['samples'][0]['condition_label']==original['samples'][0]['condition_label']
    assert original['samples'][0]['relative_molecular']=={'signal':.5}


def test_old_analysis_exports_current_scope_without_mutating_source_and_reruns(tmp_path):
    p=Platform(ROOT/'scientific_reference',tmp_path/'workspace')
    original=UserPipeline(p);report=original.run(original.example())
    saved=p.workspace/'analyses'/report['run_id']/'results.json';source_bytes=saved.read_bytes()
    public=MeasurementPipeline(p);loaded=public.load(report['run_id'])
    assert loaded['Theta']==report['Theta'] and loaded['samples']==report['samples']
    assert 'PER' not in loaded and 'PER_status' not in loaded
    extracted=tmp_path/'export';extracted.mkdir()
    with zipfile.ZipFile(io.BytesIO(public.export(report['run_id']))) as z:
        result=json.loads(z.read('results.json'))
        assert 'PER' not in result and 'PER_status' not in result
        assert 'RNA 编辑百分比' not in z.read('report.html').decode()
        assert 'lang="en"' in z.read('report.html').decode()
        assert 'RES units are AC DNA mass reference equivalent' in z.read('report.html').decode()
        assert '完整 Θ' not in z.read('report.html').decode()
        for name,digest in json.loads(z.read('artifact_manifest.json')).items():
            assert hashlib.sha256(z.read(name)).hexdigest()==digest
        z.extractall(extracted)
    assert saved.read_bytes()==source_bytes
    rerun=public.rerun(extracted)
    assert rerun['Theta']==report['Theta']
    assert rerun['samples']==report['samples']
    assert 'PER' not in rerun and 'PER_status' not in rerun
    assert 'PER' not in json.loads((p.workspace/'analyses'/rerun['run_id']/'results.json').read_text())
