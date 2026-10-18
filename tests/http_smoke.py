"""Exercise real HTTP routes against an isolated workspace; never touches user imports."""
import csv
import io
import json
from pathlib import Path
import tempfile
import threading
import urllib.error
import urllib.request
import zipfile

from sonar_app.backend import Platform
from sonar_app.server import create_server

root=Path(__file__).resolve().parents[1]
checks=[]
with tempfile.TemporaryDirectory(prefix='sonar-http-') as tmp:
    app=Platform(root/'scientific_reference',Path(tmp)/'workspace')
    server=create_server(app,0)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    url=f'http://127.0.0.1:{server.server_port}'
    def get(path):
        with urllib.request.urlopen(url+path) as r:return r.read()
    token=json.loads(get('/api/session'))['token']
    def post(path,value,token_value=token,content_type='application/json'):
        body=json.dumps(value).encode() if content_type=='application/json' else value
        request=urllib.request.Request(url+path,data=body,headers={'Content-Type':content_type,'X-SONAR-Token':token_value})
        with urllib.request.urlopen(request) as r:return r.read()
    try:
        assert b'<html lang="zh-CN">' in get('/')
        assert len(json.loads(get('/api/overview'))['samples'])==32
        checks.append('HTML and overview: 32 real wells')
        routine=json.loads(get('/api/overview?mode=routine'))
        assert all(s['RES']['res_mass_fraction'] is None for s in routine['samples'])
        checks.append('Routine normal RES null')
        result=json.loads(post('/api/analyze',{'sample_id':'S7_90B'}))
        assert abs(result['RAS'][0]['ras']-.9562602659677872)<1e-12
        checks.append('Raw FCS analysis matches golden')
        result=json.loads(post('/api/inverse',{'ras':5}))
        assert result['hypothetical_incompatible_mapping'] is None
        checks.append('Out-of-range is null')
        try:post('/api/analyze',{'sample_id':'S7_90B'},token_value='bad')
        except urllib.error.HTTPError as e:assert e.code==403
        else:raise AssertionError('Missing request-token rejection')
        checks.append('Mutation session token required')
        md=app._metadata('reference','S7_90B');data=io.BytesIO()
        text='sample_id,well_id,file_path,condition_label,original_label,cell_type,reporter_construct,linked_editor_present\n'
        text+='qa-A,qa-well-A,inputs/real.fcs,real-reference-copy,90,HEK293T,S7-reference,false\n'
        with zipfile.ZipFile(data,'w',zipfile.ZIP_DEFLATED) as z:
            z.writestr('metadata.csv',text);z.write(app.root/md['file_path'],'inputs/real.fcs')
        imported=json.loads(post('/api/import?name=HTTP-QA-real-reference-copy',data.getvalue(),content_type='application/zip'))
        s=json.loads(post('/api/analyze',{'dataset':imported['dataset'],'sample_id':'qa-A'}))
        assert s['RES']['res_mass_fraction'] is None and s['RAS'][0]['ras'] is not None
        checks.append('ZIP import, raw analysis and transfer restriction')
        bundle=post('/api/export',{'sample_ids':['S7_90B','S10_1_8_A']})
        with zipfile.ZipFile(io.BytesIO(bundle)) as z:
            assert len(json.loads(z.read('measurements.json'))['samples'])==2
            assert 'report.html' in z.namelist()
        (root/'verification/HTTP_example_export.zip').write_bytes(bundle)
        checks.append('HTTP report bundle generated and reopened')
        try:get('/api/molecular')
        except urllib.error.HTTPError as e:assert e.code==404
        else:raise AssertionError('Retired route must be unavailable')
        assert all('PER' not in s for s in json.loads(get('/api/overview'))['samples'])
        checks.append('Measurement-only overview; retired route returns 404')
        from sonar_app.pipeline import UserPipeline
        demo=UserPipeline(app).example();rows=[]
        for row in demo['files']:
            payload=(app.workspace/'uploads'/(row['token']+'.fcs')).read_bytes()
            uploaded=json.loads(post('/api/upload-fcs?name='+row['original_filename'],payload,content_type='application/octet-stream'))
            rows.append({**row,'token':uploaded['token']})
        demo['files']=rows
        analysis=json.loads(post('/api/pipeline',demo))
        assert abs(analysis['samples'][0]['RAS']['ras']-.9562602659677872)<1e-12
        assert abs(analysis['samples'][0]['RES']['model_estimate_res_mass_fraction']-.7454898213131971)<1e-12
        checks.append('Binary FCS uploads -> new Mock Theta -> paired RAS -> explicit S7 model estimate')
        saved=json.loads(get('/api/analysis?id='+analysis['run_id']))
        assert saved==analysis and len(json.loads(get('/api/analyses')))==1
        assert 'PER' not in analysis and 'PER_status' not in analysis
        checks.append('Saved user analysis, identity verification and listing')
        with zipfile.ZipFile(io.BytesIO(post('/api/pipeline-export',{'run_id':analysis['run_id']}))) as z:
            assert json.loads(z.read('Theta.json'))==analysis['Theta']
            assert len([n for n in z.namelist() if n.endswith('.fcs')])==3
            assert len([n for n in z.namelist() if n.endswith('.npz')])==3
        checks.append('User analysis report ZIP includes raw inputs, all event masks and portable rerun config')
        assert len(json.loads(post('/api/pipeline-example',{'full':True}))['files'])==22
        assert b'renderPipelinePage' in get('/pipeline.js')
        checks.append('Real full-reference example and user workflow asset served')
        config=json.loads(get('/api/experiment-config'))
        folders=json.loads(post('/api/folders',{'path':str(Path(tmp))}))
        assert folders['path']==str(Path(tmp).resolve())
        exp=json.loads(post('/api/experiment-create',{'name':'HTTP staged real FCS','save_parent':str(Path(tmp)/'chosen-save')}))
        eid=exp['experiment_id'];assert Path(exp['save_path']).parent==(Path(tmp)/'chosen-save').resolve()
        checks.append('Destination picker and independent experiment folder')
        for name in ('MOCK1.fcs','MOCK2.fcs'):
            exp=json.loads(post('/api/experiment-upload?id='+eid+'&stage=mock&name='+name,(app.root/'inputs/S7'/name).read_bytes(),content_type='application/octet-stream'))
        exp=json.loads(post('/api/experiment-layer0',{'experiment_id':eid,'cell_type':'HEK293T','channel_map':exp['channel_map']}))
        assert exp['status']=='theta_ready' and exp['result'] is None
        theta=exp['Theta']
        exp=json.loads(get('/api/experiment?id='+eid));assert exp['Theta']==theta
        checks.append('Mock-only Layer 0 persisted and resumed before sample upload')
        exp=json.loads(post('/api/experiment-confirm-theta',{'experiment_id':eid}))
        exp=json.loads(post('/api/experiment-upload?id='+eid+'&stage=sample&name=90B.fcs',(app.root/'inputs/S7/90B.fcs').read_bytes(),content_type='application/octet-stream'))
        exp=json.loads(post('/api/experiment-compute',{'experiment_id':eid,'settings':{'reporter_construct':'S7 reference','files':[f for f in exp['files'] if f['stage']=='sample']}}))
        assert exp['status']=='complete' and exp['result']['Theta']==theta
        assert exp['result']['workflow']['theta_reused_without_refit']
        assert abs(exp['result']['samples'][0]['RAS']['ras']-.9562602659677872)<1e-12
        assert (Path(exp['save_path'])/'SONAR_report.zip').exists()
        checks.append('Confirmed Theta applied to later experimental upload with automatic final save')
        with zipfile.ZipFile(io.BytesIO(post('/api/experiment-export',{'experiment_id':eid}))) as z:
            result=json.loads(z.read('results.json'))
            assert result['workflow']['experiment_id']==eid
            assert 'PER' not in result and 'PER_status' not in result
            assert 'RNA 编辑百分比' not in z.read('report.html').decode()
        assert len(json.loads(get('/api/experiments')))==1 and b'wfTrail' in get('/workflow.js')
        checks.append('Staged experiment report export, history and frontend asset')
    finally:
        server.shutdown();server.server_close();thread.join()
(root/'verification/http_tests.json').write_text(json.dumps({'status':'PASS','checks':checks},indent=2))
print(json.dumps({'status':'PASS','checks':len(checks)}))
