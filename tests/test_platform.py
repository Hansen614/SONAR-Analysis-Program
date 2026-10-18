import csv
import io
import json
from pathlib import Path
import shutil
import zipfile

import pytest
from sonar_app.backend import Platform, contained, safe_id
from sonar_app.export import export_bundle, csv_safe

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def app(tmp_path_factory):
    return Platform(ROOT/'scientific_reference',tmp_path_factory.mktemp('sonar-workspace'))


def input_directory(app,tmp_path,duplicate=False):
    md=app._metadata('reference','S7_90B')
    shutil.copyfile(app.root/md['file_path'],tmp_path/'sample.fcs')
    rows=[dict(sample_id='new-A',well_id='well-A',file_path='sample.fcs',condition_label='condition A',original_label='original A',
        cell_type='HEK293T',reporter_construct='declared_reporter',linked_editor_present='false')]
    if duplicate:rows.append(dict(rows[0],sample_id='new-B',well_id='well-B'))
    with (tmp_path/'metadata.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)
    return rows


@pytest.mark.parametrize('sample',['S7_90B','S7_5B','S7_100A','S10_1_8_A'])
def test_raw_goldens(app,sample):
    golden=json.loads((app.root/'tests/golden_reference/real_samples.json').read_text())[sample]
    s=app.analyze(sample,diagnostics=False)
    for key in ['ras','n_selected','sum_G_corrected','sum_R_corrected','effective_red_events']:
        assert s['RAS'][0][key]==pytest.approx(golden[key],rel=1e-12,abs=1e-12)
    assert s['RES']['res_mass_fraction']==pytest.approx(golden['RES_mass_fraction']) if golden['RES_mass_fraction'] is not None else s['RES']['res_mass_fraction'] is None
    assert 'PER' not in s


def test_routine_retains_separate_research_value(app):
    s=app.analyze('S7_90B',mode='routine',diagnostics=False)
    assert s['RES']['res_mass_fraction'] is None
    assert s['RES']['research_res_mass_fraction']==pytest.approx(.7454898213131971)
    assert s['RAS'][0]['ras']>0


def test_no_editor_cannot_be_coexpression(app):
    s=app.analyze('S7_90B',population='blue_positive_reporter',diagnostics=False)
    assert s['RAS'][0]['ras'] is None
    assert s['RES']['res_mass_fraction'] is None
    assert s['RAS'][0]['score_status']=='NOT_APPLICABLE_NO_LINKED_EDITOR'


def test_s10_coexpression_never_receives_s7_res(app):
    s=app.analyze('S10_1_8_A',population='blue_positive_reporter',diagnostics=False)
    assert s['RAS'][0]['ras'] is not None
    assert s['RES']['res_mass_fraction'] is None
    assert 'relative_molecular' not in s
    assert 'PER' not in s


def test_arbitrary_calculator_is_not_qualified(app):
    result=app.inverse(.95)
    assert result['res_mass_fraction'] is None
    assert result['research_res_mass_fraction'] is None
    assert result['hypothetical_incompatible_mapping'] is not None
    assert app.inverse(5)['hypothetical_incompatible_mapping'] is None
    with pytest.raises(ValueError):app.inverse(.9,interval=[1,2])
    with pytest.raises(ValueError):app.inverse(float('nan'))


def test_real_import_preserves_raw_and_blocks_transfer(app,tmp_path):
    input_directory(app,tmp_path)
    imported=app.import_directory(tmp_path,'真实参考 FCS 的导入回归测试')
    ds=imported['dataset']
    assert app.validate_dataset(ds)['status']=='PASS'
    s=app.analyze('new-A',dataset=ds,diagnostics=False)
    assert s['RAS'][0]['ras']==pytest.approx(.9562602659677872)
    assert s['RES']['res_mass_fraction'] is None
    assert s['RES']['research_res_mass_fraction'] is None
    assert s['RES']['sample_id'] is None  # no registered observation uncertainty reuse
    assert 'relative_molecular' not in s
    assert 'PER' not in s
    assert s['provenance']['dataset']==ds
    with (app.workspace/'imports'/ds/'inputs/new-A.fcs').open('ab') as f:f.write(b'changed')
    with pytest.raises(ValueError,match='changed'):app.analyze('new-A',dataset=ds)


def test_duplicate_acquisition_not_independent_well(app,tmp_path):
    input_directory(app,tmp_path,duplicate=True)
    with pytest.raises(ValueError,match='Duplicate FCS'):app.import_directory(tmp_path)


def test_wrong_channel_import_rolls_back(app,tmp_path):
    input_directory(app,tmp_path)
    f=tmp_path/'sample.fcs';f.write_bytes(f.read_bytes().replace(b'FL1-A',b'BAD-A'))
    before=set((app.workspace/'imports').glob('*'))
    with pytest.raises(ValueError,match='channel map'):app.import_directory(tmp_path)
    assert set((app.workspace/'imports').glob('*'))==before


def test_missing_metadata_and_wrong_cell_type(app,tmp_path):
    rows=input_directory(app,tmp_path)
    del rows[0]['well_id']
    with pytest.raises(ValueError,match='Missing metadata'):app.validate_import_rows(rows,tmp_path)
    rows=input_directory(app,tmp_path);rows[0]['cell_type']='other'
    with pytest.raises(ValueError,match='HEK293T'):app.validate_import_rows(rows,tmp_path)


@pytest.mark.parametrize('name',['../escape.fcs','/absolute.fcs'])
def test_zip_traversal_rejected(app,name):
    b=io.BytesIO()
    with zipfile.ZipFile(b,'w') as z:z.writestr(name,'payload')
    with pytest.raises(ValueError,match='Path must stay'):app.import_zip(b.getvalue(),'bad')


def test_export_preserves_null_uncertainty_and_provenance(app):
    data=export_bundle(app,sample_ids=['S7_90B','S10_1_8_A'],mode='routine')
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        assert set(['measurements.json','measurements.csv','report.html','calibration.svg','provenance.json','requirements.lock.txt','METHODS.txt'])==set(z.namelist())
        report=json.loads(z.read('measurements.json'))
        assert all(s['RES']['res_mass_fraction'] is None and 'PER' not in s for s in report['samples'])
        s7=next(s for s in report['samples'] if s['series']=='S7')
        assert s7['RES']['research_res_mass_fraction'] is not None
        assert s7['RES']['bootstrap_total_n']==1000
        assert s7['metadata']['source_condition_label']==90
        assert s7['condition_label']==75
        csv_rows=list(csv.DictReader(io.StringIO(z.read('measurements.csv').decode('utf-8-sig'))))
        assert not any(key.startswith('PER') for key in csv_rows[0])
        assert json.loads(z.read('provenance.json'))['context_sha256']
        assert 'AC DNA mass-equivalent percent' in z.read('report.html').decode()


def test_user_fit_has_own_identity_and_grouped_validation(app):
    text='well_id,fraction,ras,context_id,reporter_construct,fraction_basis,population_mode\n'
    for s in app.frozen:
        if s['series']=='S7':
            text+=f"{s['well_id']},{s['condition_label']/100},{s['RAS'][0]['ras']},{app.context['context_id']},S7_exact_sequences_unverified,AC_DNA_mass_fraction,reporter\n"
    fitted=app.fit_references(text,'Real S7 regression fit')
    assert fitted['model_id']!=app.model['model_id']
    assert fitted['routine_allowed'] is False
    assert 'PER' not in fitted
    assert len(fitted['validation'])==20
    assert fitted['uncertainty']['draws']==200
    assert len([v for v in fitted['validation'] if v['inverse']['point'] is None])>=1
    assert app.model['model_id'].endswith('S7-hinge-k050')
    with pytest.raises(ValueError,match='unique'):app.fit_references(text+text.splitlines()[1]+'\n')


def test_version_invalidation(app,tmp_path):
    input_directory(app,tmp_path)
    ds=app.import_directory(tmp_path)['dataset']
    path=app.workspace/'imports'/ds/'experiment.json'
    record=json.loads(path.read_text());record['context_sha256']='invalid';path.write_text(json.dumps(record))
    with pytest.raises(ValueError,match='invalidated'):app.validate_dataset(ds)


def test_safe_names_and_csv_formulas():
    with pytest.raises(ValueError):safe_id('../escape')
    with pytest.raises(ValueError):safe_id('test\nname')
    assert csv_safe('=1+1')=="'=1+1"
    assert csv_safe(-.5)==-.5


def test_backend_has_no_ui_dependency():
    text=(ROOT/'sonar_app/backend.py').read_text()
    assert 'from .server import' not in text
    assert 'import streamlit' not in text
