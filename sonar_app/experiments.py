"""Durable experiment stages: destination -> Mock/Theta -> samples -> report."""
from __future__ import annotations
from datetime import datetime
from zoneinfo import ZoneInfo
import io
from pathlib import Path
import re
import shutil
import uuid
import zipfile

from .backend import Platform, contained, read_json, safe_id, sha, write_json
from .measurement import MeasurementPipeline

WORKFLOW_VERSION = 'sonar-staged-experiment-v1'
UNSPECIFIED = 'Not specified'


def experiment_text(value, label, limit=200, default=''):
    text = '' if value is None else str(value).strip()
    if len(text) > limit:
        raise ValueError(f'{label} must be at most {limit} characters.')
    return text or default


def now():
    return datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(timespec='seconds')


def atomic_json(path, value):
    path=Path(path);temporary=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    try:
        write_json(temporary,value);temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


class BoundThetaPipeline(MeasurementPipeline):
    """Apply the reviewed Layer 0 object without fitting it a second time."""
    def __init__(self, platform, theta):
        super().__init__(platform);self.bound_theta=theta

    def theta(self, entries, mapping, cell_type):
        t=self.bound_theta
        from . import pipeline
        if t['pipeline_sha256']!=sha(Path(pipeline.__file__)) or t['kernel_sha256']!=sha(self.p.root/'src/core.py'):
            raise ValueError('The Layer 0 method version changed. Reanalyze the Mock controls.')
        if mapping!=t['channel_map'] or cell_type!=t['cell_type']:
            raise ValueError('Experiment identity or channels differ from the confirmed Θ. Return to Upload controls.')
        controls=[(e['sample_id'],e['sha256']) for e in entries if e['role']=='mock']
        expected=[(e['sample_id'],e['sha256']) for e in t['controls']]
        if controls!=expected:
            raise ValueError('Mock files differ from the confirmed Θ. Recalculate Layer 0.')
        return t


class Experiments:
    def __init__(self, platform):
        self.p=platform;self.pipe=MeasurementPipeline(platform)
        self.index_path=platform.workspace/'experiments_index.json'
        self.default_parent=platform.workspace/'experiments'

    def config(self):
        return {'default_save_parent':str(self.default_parent),'workflow_version':WORKFLOW_VERSION}

    def example(self, stage='mock_upload'):
        """Open an isolated walkthrough using authentic, same-batch acquisitions.

        Never accepts a destination experiment ID: loading a demo cannot mix
        reference files with a user's current controls or overwrite their run.
        All calculations use the normal upload, Theta and analysis methods.
        """
        stages=('mock_upload','theta_ready','sample_upload','complete')
        if stage not in stages:
            raise ValueError('Unknown example stage.')
        ids=['S7_MOCK1','S7_MOCK2','S7_90B']
        sources=[]
        for sid in ids:
            row=self.p.api.clean(self.p.manifest[self.p.manifest.acquisition_id==sid].iloc[0].to_dict())
            path=contained(self.p.root,row['file_path'])
            sources.append((sid,row,path.read_bytes(),Path(row['file_path']).name))
        d=self.create('Example experiment · Reporter',str(self.p.workspace/'examples'))
        eid=d['experiment_id']
        base,document=self._document(eid)
        document.update(example_source={'kind':'bundled_reference_FCS','acquisition_ids':ids},
                        cell_type='HEK293T',reporter_construct='Built-in reference Reporter (sequence identity unverified)',
                        experiment_notes='Built-in real FCS example for trying the analysis workflow.')
        self._save(base,document)
        for sid,row,payload,name in sources[:2]:
            d=self.upload(eid,'mock',payload,name)
        if stage=='mock_upload':return d
        d=self.analyze_mock(eid,'HEK293T',d['channel_map'])
        if stage=='theta_ready':return d
        d=self.confirm_theta(eid)
        sid,row,payload,name=sources[2]
        d=self.upload(eid,'sample',payload,name)
        base,document=self._document(eid)
        sample=next(f for f in document['files'] if f['stage']=='sample')
        sample.update(condition_label=str(row['condition_label'])+'% AC mass',
                      original_label=str(row.get('source_condition_label',row['condition_label'])))
        self._save(base,document)
        d=self.snapshot(eid)
        if stage=='sample_upload':return d
        return self.compute(eid,{'files':[f for f in d['files'] if f['stage']=='sample'],
                                 'population':'reporter','calibration_mode':'frozen','bootstrap_repeats':200})

    def folders(self, path=None):
        if path is None or path==str(self.default_parent):
            self.default_parent.mkdir(parents=True,exist_ok=True);p=self.default_parent
        else:
            p=Path(str(path)).expanduser()
            if not p.is_absolute():raise ValueError('Enter an absolute folder path.')
            p=p.resolve()
        if not p.is_dir():raise ValueError('The save location must be an existing folder. Choose its parent directory if needed.')
        children=[]
        for c in sorted(p.iterdir(),key=lambda c:c.name.lower()):
            if c.name.startswith('.'):continue
            try:
                if c.is_dir():children.append({'name':c.name,'path':str(c.resolve())})
            except OSError:continue
        return {'path':str(p),'parent':str(p.parent),'directories':children,
                'shortcuts':[{'name':'Default experiment folder','path':str(self.default_parent)},
                             {'name':'Project folder','path':str(self.p.workspace.parent.parent)},
                             {'name':'Desktop','path':str(Path.home()/'Desktop')}]}

    def _index(self):
        return read_json(self.index_path) if self.index_path.exists() else {}

    def _document(self, experiment_id):
        eid=safe_id(experiment_id);index=self._index()
        if eid not in index:raise ValueError('Experiment not found. Choose one from Experiment history.')
        base=Path(index[eid]).resolve();d=read_json(base/'experiment.json')
        if d['experiment_id']!=eid:raise ValueError('Experiment file identity does not match.')
        return base,d

    def _save(self, base, document):
        document['updated_at']=now();atomic_json(base/'experiment.json',document)

    def _invalidate(self, d, stage):
        d['status']='mock_upload' if stage=='mock' else 'sample_upload'
        d['result_id']=None;d['result_theta_sha256']=None
        if stage=='mock':d['theta_sha256']=None;d['confirmed_theta_sha256']=None

    def create(self, name, save_parent):
        name=str(name).strip()
        if not 1<=len(name)<=100:raise ValueError('Enter an experiment name of 1–100 characters.')
        parent=Path(str(save_parent)).expanduser()
        if not parent.is_absolute():raise ValueError('Choose a save folder first.')
        parent=parent.resolve()
        if parent==self.p.root or self.p.root in parent.parents:
            raise ValueError('Choose a save location outside the scientific reference package.')
        parent.mkdir(parents=True,exist_ok=True)
        eid='experiment-'+uuid.uuid4().hex[:12]
        slug=re.sub(r'[^\w.-]+','_',name).strip('._')[:50] or 'experiment'
        base=parent/(datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y%m%d_%H%M%S')+'_'+slug+'_'+eid[-6:])
        base.mkdir()
        d={'experiment_id':eid,'name':name,'created_at':now(),'updated_at':now(),'workflow_version':WORKFLOW_VERSION,
           'status':'mock_upload','files':[],'cell_type':UNSPECIFIED,'reporter_construct':UNSPECIFIED,'experiment_notes':'','channel_map':{},
           'population':'reporter','calibration_mode':'frozen','bootstrap_repeats':200,
           'theta_sha256':None,'confirmed_theta_sha256':None,'result_id':None,'result_theta_sha256':None,'theta_revision':0}
        self._save(base,d);index=self._index();index[eid]=str(base);atomic_json(self.index_path,index)
        return self.snapshot(eid)

    def list(self):
        result=[]
        for eid,path in self._index().items():
            try:
                d=read_json(Path(path)/'experiment.json')
                result.append({k:d[k] for k in ['experiment_id','name','created_at','updated_at','status']}|{'save_path':path})
            except (OSError,ValueError,KeyError):
                result.append({'experiment_id':eid,'name':Path(path).name,'status':'unavailable','updated_at':'','save_path':path})
        return sorted(result,key=lambda d:d['updated_at'],reverse=True)

    def _inputs(self, base, d, stage=None):
        entries=[]
        for f in d['files']:
            if stage and f['stage']!=stage:continue
            p=contained(base,f['file_path'])
            if not p.is_file() or sha(p)!=f['sha256']:raise ValueError(f['original_filename']+' : the saved file has changed. Upload it again.')
            entries.append({**f,'path':p})
        return entries

    def _theta(self, base, d, confirmed=False):
        path=base/'layer0/Theta.json'
        if not d['theta_sha256'] or not path.exists() or sha(path)!=d['theta_sha256']:
            raise ValueError('Layer 0 is incomplete or has changed. Reanalyze the Mock controls.')
        if confirmed and d['confirmed_theta_sha256']!=d['theta_sha256']:
            raise ValueError('Review Θ first, then select Confirm Θ and continue.')
        self._inputs(base,d,'mock')
        from . import pipeline
        t=read_json(path)
        if t['pipeline_sha256']!=sha(Path(pipeline.__file__)) or t['kernel_sha256']!=sha(self.p.root/'src/core.py'):
            raise ValueError('The Layer 0 method version changed. Reanalyze the Mock controls.')
        return t

    def snapshot(self, experiment_id):
        base,d=self._document(experiment_id)
        result={'experiment_notes':'',**d,'save_path':str(base),'Theta':None,'result':None}
        if d['status'] in ('theta_ready','sample_upload','complete'):result['Theta']=self._theta(base,d)
        if d['status']=='complete':
            if d['result_theta_sha256']!=d['theta_sha256']:raise ValueError('Results use an outdated Θ. Recalculate the results.')
            result['result']=MeasurementPipeline(Platform(self.p.root,base,verify=False)).load(d['result_id'])
        return result

    def upload(self, experiment_id, stage, payload, name):
        if stage not in ('mock','sample'):raise ValueError('Unknown upload stage.')
        base,d=self._document(experiment_id)
        if stage=='sample':self._theta(base,d,confirmed=True)
        info=self.pipe.upload(payload,name)
        source=self.p.workspace/'uploads'/(info['token']+'.fcs')
        try:
            if any(f['sha256']==info['sha256'] for f in d['files']):raise ValueError('This FCS already exists and cannot be counted as an independent acquisition again.')
            if len(d['files'])>=128 or sum(f['bytes'] for f in d['files'])+info['bytes']>600*1024*1024:
                raise ValueError('An experiment supports up to 128 files and 600 MiB total.')
            sid=re.sub('[^A-Za-z0-9_.-]','_',Path(name).stem).strip('._-')[:60] or 'sample'
            original=sid;n=2
            while any(f['sample_id']==sid for f in d['files']) or (base/'inputs'/stage/(sid+'.fcs')).exists():
                sid=original+'_'+str(n);n+=1
            rel='inputs/'+stage+'/'+sid+'.fcs';destination=contained(base,rel);destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(source,destination)
            entry={k:v for k,v in info.items() if k!='token'}
            entry.update(file_id=uuid.uuid4().hex[:12],file_path=rel,stage=stage,role='mock' if stage=='mock' else 'sample',
                         sample_id=sid,well_id=sid,condition_label='',original_label=name,ac_fraction=None,linked_editor_present=False)
            d['files'].append(entry)
            if stage=='mock' and not d['channel_map']:d['channel_map']=info['proposed_channel_map']
            self._invalidate(d,stage);self._save(base,d)
        finally:
            source.unlink(missing_ok=True);source.with_suffix('.json').unlink(missing_ok=True)
        return self.snapshot(experiment_id)

    def remove_file(self, experiment_id, file_id):
        base,d=self._document(experiment_id);f=next((f for f in d['files'] if f['file_id']==file_id),None)
        if f is None:raise ValueError('File not found.')
        # Keep the original copy on disk for recovery; remove it from active inputs.
        d['files']=[v for v in d['files'] if v['file_id']!=file_id]
        self._invalidate(d,f['stage']);self._save(base,d)
        return self.snapshot(experiment_id)

    def revise(self, experiment_id, stage):
        if stage not in ('mock','sample'):raise ValueError('Unknown stage.')
        base,d=self._document(experiment_id)
        if stage=='sample':self._theta(base,d,confirmed=True)
        self._invalidate(d,stage);self._save(base,d)
        return self.snapshot(experiment_id)

    def analyze_mock(self, experiment_id, cell_type, channel_map, experiment_notes=None):
        base,d=self._document(experiment_id);entries=self._inputs(base,d,'mock')
        if not entries:raise ValueError('Upload at least one Mock FCS file first.')
        cell_type=experiment_text(cell_type,'Cell type',default=UNSPECIFIED)
        notes=experiment_text(d.get('experiment_notes','') if experiment_notes is None else experiment_notes,'Experiment notes',4000)
        self.p._ensure_current_identity()
        theta=self.pipe.theta(entries,channel_map,cell_type)
        for e in entries:
            x,_,_,_=self.pipe.read(e['path'],channel_map)
            q,c,s,_,_=self.pipe.core.gate(x,theta['gate_parameters'],theta['config'])
            directory=base/'layer0/masks';directory.mkdir(parents=True,exist_ok=True)
            self.p.np.savez_compressed(directory/(e['sample_id']+'.npz'),quality=q,cell=c,singlet=s)
        atomic_json(base/'layer0/Theta.json',theta)
        self._invalidate(d,'mock');d.update(cell_type=cell_type,experiment_notes=notes,channel_map=channel_map,status='theta_ready',
            theta_sha256=sha(base/'layer0/Theta.json'),theta_revision=d['theta_revision']+1)
        atomic_json(base/'layer0/manifest.json',{'Theta.json':d['theta_sha256'],
            **{'masks/'+e['sample_id']+'.npz':sha(base/'layer0/masks'/(e['sample_id']+'.npz')) for e in entries}})
        self._save(base,d)
        return self.snapshot(experiment_id)

    def confirm_theta(self, experiment_id):
        base,d=self._document(experiment_id)
        if d['status']!='theta_ready':raise ValueError('Complete Layer 0 analysis first.')
        self._theta(base,d);d.update(confirmed_theta_sha256=d['theta_sha256'],theta_confirmed_at=now(),status='sample_upload')
        self._save(base,d);return self.snapshot(experiment_id)

    def compute(self, experiment_id, settings):
        base,d=self._document(experiment_id);theta=self._theta(base,d,confirmed=True)
        if d['status'] not in ('sample_upload','complete'):raise ValueError('Proceed to Upload samples first.')
        sample_entries=self._inputs(base,d,'sample')
        if not sample_entries:raise ValueError('Upload at least one sample FCS file.')
        reporter=experiment_text(settings.get('reporter_construct',d.get('reporter_construct','')),'Reporter construct name',default=UNSPECIFIED)
        notes=experiment_text(settings.get('experiment_notes',d.get('experiment_notes','')),'Experiment notes',4000)
        overrides={r['file_id']:r for r in settings.get('files',[])}
        if set(overrides)!={f['file_id'] for f in sample_entries}:raise ValueError('The sample file list has changed. Reload it.')
        for f in d['files']:
            if f['stage']=='sample':
                row=overrides[f['file_id']]
                for key in ('sample_id','well_id','condition_label','ac_fraction','linked_editor_present','role'):
                    if key in row:f[key]=row[key]
                if f['role'] not in ('sample','reference'):raise ValueError('Sample files must be test samples or AC/INAC reference wells.')
        local=Platform(self.p.root,base,verify=False);engine=BoundThetaPipeline(local,theta);rows=[];tokens=[]
        for e in self._inputs(base,d):
            u=engine.upload(e['path'].read_bytes(),e['original_filename']);tokens.append(u['token'])
            rows.append({k:v for k,v in e.items() if k!='path'}|{'token':u['token']})
        spec={'name':d['name'],'files':rows,'channel_map':d['channel_map'],'cell_type':d['cell_type'],
            'reporter_construct':reporter,'experiment_notes':notes,'population':settings.get('population','reporter'),
            'calibration_mode':settings.get('calibration_mode','frozen'),'bootstrap_repeats':settings.get('bootstrap_repeats',200)}
        try:
            report=engine.run(spec)
            report['workflow']={'version':WORKFLOW_VERSION,'experiment_id':experiment_id,'theta_reused_without_refit':True,
                'confirmed_theta_sha256':d['confirmed_theta_sha256'],'theta_revision':d['theta_revision']}
            output=base/'analyses'/report['run_id'];write_json(output/'results.json',report)
            manifest=read_json(output/'artifact_manifest.json');manifest['results.json']=sha(output/'results.json');write_json(output/'artifact_manifest.json',manifest)
            payload=engine.export(report['run_id']);(base/'SONAR_report.zip').write_bytes(payload)
            with zipfile.ZipFile(io.BytesIO(payload)) as z:
                for name in ('measurements.csv','report.html'):(base/name).write_bytes(z.read(name))
            d.update(status='complete',result_id=report['run_id'],result_theta_sha256=d['theta_sha256'],
                     reporter_construct=reporter,experiment_notes=notes,population=spec['population'],calibration_mode=spec['calibration_mode'],bootstrap_repeats=spec['bootstrap_repeats'])
            self._save(base,d)
        finally:
            for token in tokens:
                for suffix in ('.fcs','.json'):(base/'uploads'/(token+suffix)).unlink(missing_ok=True)
        return self.snapshot(experiment_id)

    def export(self, experiment_id):
        base,d=self._document(experiment_id)
        if d['status']!='complete':raise ValueError('Complete Layer 1 / Layer 2 calculations first.')
        self._theta(base,d,confirmed=True)
        if d['result_theta_sha256']!=d['theta_sha256']:raise ValueError('Results use an outdated Θ.')
        return MeasurementPipeline(Platform(self.p.root,base,verify=False)).export(d['result_id'])
