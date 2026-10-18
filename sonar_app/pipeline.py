"""User-FCS workflow: measured batch Theta -> paired linear RAS -> research RES.

The frozen reference is evidence and a reusable algorithm/model resource, not the
identity of every new experiment. Original core numerical functions stay untouched.
"""
from __future__ import annotations
import hashlib
import html
import importlib
import io
import json
from pathlib import Path
import shutil
import tempfile
import uuid
import zipfile

from .backend import safe_id, sha, read_json, write_json, contained
from .export import flatten, csv_safe

VERSION = 'sonar-user-pipeline-v1'
ROLE_KEYS = ['FSC-H', 'FSC-A', 'SSC-H', 'SSC-A', 'EGFP', 'mCherry', 'Time']
CHANNEL_SLOTS = {'FSC-H': 0, 'FSC-A': 1, 'SSC-H': 2, 'SSC-A': 3, 'EGFP': 5, 'BFP': 7, 'mCherry': 9, 'Time': 11}


def stable_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


class UserPipeline:
    def __init__(self, platform):
        self.p = platform
        self.np, self.api = platform.np, platform.api
        self.core = importlib.import_module('core')
        self.cal = importlib.import_module('reporter_calibration')
        self.inverse = importlib.import_module('inverse_calibration').inverse
        self.set_ranges = importlib.import_module('inverse_calibration').set_ranges
        self.FlowData = importlib.import_module('flowio').FlowData

    def upload(self, payload, name):
        if not 0 < len(payload) <= 128 * 1024 * 1024:
            raise ValueError('单个 FCS 必须为 1 字节至 128 MiB。')
        if Path(name).suffix.lower() != '.fcs':
            raise ValueError('请选择原始 .fcs 文件。')
        directory = self.p.workspace / 'uploads'; directory.mkdir(exist_ok=True)
        token = uuid.uuid4().hex
        path = directory / (token + '.fcs'); path.write_bytes(payload)
        try:
            info = self.inspect(path)
            info.update(token=token, original_filename=Path(name).name, sha256=sha(path), bytes=len(payload))
            write_json(directory / (token + '.json'), info)
            return info
        except Exception:
            path.unlink(missing_ok=True)
            raise

    def inspect(self, path):
        fd = self.FlowData(str(path)); t = fd.text
        channels = [{'name': n, 'label': t.get(f'p{i+1}s', ''), 'index': i} for i, n in enumerate(fd.pnn_labels)]
        # Suggestions are exposed for user review, not guessed silently at run time.
        aliases = {'EGFP': {'gfp-a', 'egfp-a'}, 'mCherry': {'mcherry-a'}, 'BFP': {'bfp-a', 'pb450-a'}}
        proposed = {}
        for role in ROLE_KEYS + ['BFP']:
            hits = [c['name'] for c in channels if c['name'].lower() == role.lower() or
                    c['label'].lower() == role.lower() or c['name'].lower() in aliases.get(role,set()) or c['label'].lower() in aliases.get(role,set())]
            proposed[role] = hits[0] if len(hits) == 1 else ''
        return {'events': fd.event_count, 'channels': channels, 'proposed_channel_map': proposed,
                'instrument': t.get('cyt'), 'serial': t.get('cytsn'), 'date': t.get('date'),
                'optical_state': {'uscomp': t.get('uscomp'), 'spillover_present': 'spillover' in t}}

    def example(self, full=False):
        """Stage actual reference acquisitions through the same upload path."""
        ids=['S7_MOCK1','S7_MOCK2']
        ids += [m['sample_id'] for m in self.p.metadata() if m.get('series')=='S7' and 'MOCK' not in m['sample_id']] if full else ['S7_90B']
        rows=[]
        for sid in ids:
            m=self.p.api.clean(self.p.manifest[self.p.manifest.acquisition_id==sid].iloc[0].to_dict())
            info=self.upload((self.p.root/m['file_path']).read_bytes(),Path(m['file_path']).name)
            mock='MOCK' in sid
            rows.append({**info,'sample_id':sid,'well_id':m.get('well_id') or sid,'role':'mock' if mock else ('reference' if full else 'sample'),
                'condition_label':str(m['condition_label']),'original_label':str(m.get('source_condition_label',m['condition_label'])),
                'linked_editor_present':False,'ac_fraction':None if mock else float(m['condition_label'])/100})
        return {'name':'S7 原始 FCS 演示 · '+('本批次拟合' if full else 'Θ / RAS / RES'),
            'cell_type':'HEK293T','reporter_construct':'S7 AC/INAC reporter · exact sequence identity unverified',
            'files':rows,'channel_map':info['proposed_channel_map'],'population':'reporter',
            'calibration_mode':'batch' if full else 'frozen','bootstrap_repeats':200}

    def read(self, path, mapping):
        fd = self.FlowData(str(path)); t = fd.text
        if not mapping or any(not mapping.get(k) for k in ROLE_KEYS):
            raise ValueError('请明确指定 FSC-H/A、SSC-H/A、Time、EGFP 和 mCherry 通道。BFP 可不选。')
        chosen = [v for v in mapping.values() if v]
        if len(chosen) != len(set(chosen)) or any(fd.pnn_labels.count(v) != 1 for v in chosen):
            raise ValueError('通道必须存在且一一对应；同一通道不能分配给两个测量角色。')
        indices = {role: fd.pnn_labels.index(name) for role,name in mapping.items() if name and role in CHANNEL_SLOTS}
        for i in indices.values():
            if t.get(f'p{i+1}e') != '0,0' or float(t.get(f'p{i+1}g', '1')) != 1:
                raise ValueError('此版本需要线性、gain=1 的 FCS 导出；不会猜测 log/gain 还原规则。')
        if t.get('uscomp','False').lower() not in ('false','0'):
            raise ValueError('已补偿文件需要明确的预处理适配；当前入口不会重复或猜测补偿。')
        if t.get('spillover'):
            items=t['spillover'].split(','); n=int(items[0]); matrix=self.np.array(items[n+1:],float).reshape(n,n)
            if not self.np.array_equal(matrix,self.np.eye(n)):
                raise ValueError('文件含非 identity spillover；请先提供经审核的线性预处理方案，本入口不会忽略补偿矩阵。')
        native = fd.as_array(preprocess=True)
        canonical = self.np.zeros((len(native),12),dtype=float)
        for role,i in indices.items(): canonical[:,CHANNEL_SLOTS[role]]=native[:,i]
        # Preserve the original 12-channel decoder exactly for the reference panel.
        if fd.pnn_labels == self.core.CHANNELS and all(indices.get(k)==v for k,v in CHANNEL_SLOTS.items()):
            canonical = native
        used = list(indices.values())
        if len(native) < 100 or not self.np.isfinite(native[:,used]).all():
            raise ValueError('FCS 需要至少 100 个有限事件；发现非有限的必要通道数据。')
        if canonical[:,11].max() > 1e6 or canonical[:,11].min() < 0:
            raise ValueError('Time 通道超出支持范围，请核对通道映射和时间单位。')
        fpkeys=['cyt','cytsn','compgaina','ch1gain','ch2gain','ch3gain','ch8gain','ch13gain','uscomp','spillover']
        fingerprint={k:t.get(k) for k in fpkeys}
        fingerprint['channels']={role:{key:t.get(f'p{i+1}{key}') for key in ['n','s','e','g','r','v']} for role,i in indices.items()}
        return canonical,t,fingerprint,indices

    def theta(self, entries, mapping, cell_type):
        mocks=[e for e in entries if e['role']=='mock']
        if not mocks:
            raise ValueError('计算新批次 Θ 至少需要 1 个明确指定的 Mock 对照 FCS；不能从实验样本猜背景。')
        cfg=read_json(self.p.root/'config/analysis.json')
        cfg.update(context_training_control=mocks[0]['sample_id'], transfer_control=mocks[1]['sample_id'] if len(mocks)>1 else None)
        decoded=[self.read(e['path'],mapping) for e in mocks]
        fingerprints=[d[2] for d in decoded]
        if any(f != fingerprints[0] for f in fingerprints):
            raise ValueError('Mock 之间的采集设置不一致；请按相同采集 profile 分批分析。')
        gates=self.core.fit_gates(decoded[0][0],cfg)
        controls=[]; arrays=[]
        for e,(x,t,fp,ix) in zip(mocks,decoded):
            q,cell,s,_,flags=self.core.gate(x,gates,cfg)
            if s.sum()<100 or not self.np.isfinite(gates['singlet_scale']) or gates['singlet_scale']<=0:
                raise ValueError('Mock 单细胞支持不足或脉冲尺度异常，无法建立 Θ。')
            display_ix=self.np.linspace(0,len(x)-1,min(1000,len(x)),dtype=int)
            scatter=self.np.column_stack([self.np.log10(self.np.maximum(x[display_ix,1],1)),self.np.log10(self.np.maximum(x[display_ix,3],1)),cell[display_ix]])
            pulse=self.np.column_stack([self.np.log10(self.np.maximum(x[display_ix,0],1)),self.np.log10(self.np.maximum(x[display_ix,1],1)),s[display_ix]])
            arrays.append(x[s]);controls.append({'sample_id':e['sample_id'],'sha256':e['sha256'],
                'recorded_events':len(x),'cell_events':int(cell.sum()),'singlet_events':int(s.sum()),'qc':flags,
                'gate_diagnostics':{'scatter_log10_FSC_A_SSC_A':scatter,'pulse_log10_FSC_H_FSC_A':pulse}})
        bg,se,threshold,rq=self.core.background(arrays,cfg)
        gates.update(background=bg.tolist(),background_event_se=se.tolist(),positivity_thresholds=threshold.tolist(),red_quantitative_boundary=float(rq))
        cov=sum(self.np.cov(a[:,[5,9]],rowvar=False,ddof=1)/len(a) for a in arrays)/len(arrays)**2
        identity={'controls':[{k:v for k,v in c.items() if k!='gate_diagnostics'} for c in controls],'mapping':mapping,'profile':fingerprints[0],'config':cfg,'cell_type':cell_type,'kernel':sha(self.p.root/'src/core.py')}
        context_id='Theta-'+stable_hash(identity)[:16]
        channel_summary={}
        for role in ['EGFP','mCherry','BFP']:
            if not mapping.get(role):
                channel_summary[role]={'available':False,'background':None,'positivity_threshold':None};continue
            i=CHANNEL_SLOTS[role];display=self.np.concatenate([self.np.arcsinh(a[:,i]/cfg['display_asinh_cofactor']) for a in arrays])
            channel_summary[role]={'available':True,'background':float(bg[i]),'background_event_se':float(se[i]),
                'positivity_threshold':float(threshold[i]),'display_median':float(self.np.median(display)),
                'display_MAD':self.core.mad(display),'display_cofactor':cfg['display_asinh_cofactor']}
        return self.api.clean({'theta_id':context_id,'context_id':context_id,'version':VERSION,'ras_estimator_id':self.api.ESTIMATOR,
            'kernel_sha256':identity['kernel'],'pipeline_sha256':sha(Path(__file__)),'cell_type':cell_type,
            'instrument_fingerprint':fingerprints[0],'channel_map':mapping,'channel_summary':channel_summary,
            'gate_parameters':gates,'config':cfg,'controls':controls,'background_GR_covariance':cov,
            'red_quantification_boundary':float(rq),'background_method':'equal-control weighted arithmetic means of gated singlets',
            'gates_fitted_from':mocks[0]['sample_id'],'threshold_controls':[e['sample_id'] for e in mocks],
            'population':'scatter-selected singlets; viability not measured','numerical_representation':'native linear identity operation',
            'optical_status':'IDENTITY_OPERATION_NOT_VALIDATED_MULTICOLOR_COMPENSATION',
            'qc_state':'RESEARCH_CONTEXT_REQUIRES_GATE_AND_OPTICAL_REVIEW',
            'control_scope':'ONE_MOCK_NO_INDEPENDENT_CONTROL' if len(mocks)==1 else 'GATES_FROM_FIRST_MOCK_BACKGROUND_THRESHOLDS_FROM_ALL_MOCKS',
            'warnings':['Mock does not establish multicolor compensation or validated LOQ.',
                'The controls contributing to thresholds are not independent threshold validation.',
                'Review scatter/singlet gates and control retention before biological interpretation.']})

    def processed(self, entry, theta, population):
        x,t,fp,ix=self.read(entry['path'],theta['channel_map'])
        if fp != theta['instrument_fingerprint']:
            raise ValueError(entry['sample_id']+' 的采集 profile 与本批次 Mock 不匹配。')
        c=theta['gate_parameters'];q,cell,s,_,flags=self.core.gate(x,c,theta['config'])
        rp=s&(x[:,9]>c['red_quantitative_boundary']);has_blue=bool(theta['channel_map'].get('BFP'))
        bp=rp&(x[:,7]>c['positivity_thresholds'][7]) if has_blue else self.np.zeros(len(x),bool)
        if population!='reporter' and not has_blue:
            raise ValueError('当前选择了 BFP 群体，但未指定 BFP 通道。')
        masks={'quality':q,'cell':cell,'singlet':s,'reporter':rp,'blue_positive_reporter':bp,'blue_negative_reporter':rp&~bp}
        qc={'recorded_events':len(x),'after_acquisition_QC':int(q.sum()),'cell_events':int(cell.sum()),'singlet_events':int(s.sum()),
            'quantifiable_reporter_events':int(rp.sum()),'coexpression_events':int(bp.sum()) if has_blue and entry['linked_editor_present'] else None,
            'BFP_positive_singlets':int((s&(x[:,7]>c['positivity_thresholds'][7])).sum()) if has_blue else None,
            'qc_state':'WARN_OPTICAL_UNVALIDATED','context_profile_id':theta['context_id'],**flags}
        optical=[]
        for role in ['EGFP','mCherry','BFP']:
            if role not in ix:continue
            limit=float(t[f'p{ix[role]+1}r']);v=x[:,CHANNEL_SLOTS[role]]
            optical.append({'channel':role,'declared_PnR':limit,'recorded_max':float(v.max()),'events_at_or_above_PnR':int((v>=limit).sum()),'interpretation':'RANGE_AUDIT_NOT_VALIDATED_SATURATION_TEST'})
        qc['range_warning']=any(a['events_at_or_above_PnR'] for a in optical)
        metadata={k:v for k,v in entry.items() if k!='path'};metadata['acquisition_id']=entry['sample_id']
        return {'array':x,'masks':masks,'metadata':metadata,'context':theta,'qc':qc,'optical':optical,'input_sha256':entry['sha256']}

    def ras(self, processed, population, repeats, shared_noise):
        r=self.api.calculate_ras(processed,population)
        observation=[]
        if r.get('ras') is not None and repeats:
            v=processed['array'][processed['masks'][population]];c=processed['context']['gate_parameters']
            g=v[:,5]-c['background'][5];red=v[:,9]-c['background'][9]
            cfg={**processed['context']['config'],'bootstrap_repeats':repeats}
            u,_,observation=self.core.bootstrap(g,red,shared_noise,cfg,self.np.random.default_rng(int(processed['input_sha256'][:8],16)))
            r['uncertainty']={**u,'status':'USER_BATCH_PAIRED_EVENTS_SHARED_MOCK_NOISE','repeats':repeats,'shared_draw_ids':f'0..{repeats-1}'}
        return self.api.clean(r),self.np.array(observation)

    def fit_batch_model(self, samples, draws, repeats, theta, population):
        refs=[s for s in samples if s['role']=='reference']
        if not refs or any(s['RAS']['ras'] is None for s in refs):
            raise ValueError('批次校准需要可计算 RAS 的 AC/INAC 参考孔。')
        x=self.np.array([s['ac_fraction'] for s in refs],float);y=self.np.array([s['RAS']['ras'] for s in refs])
        levels,counts=self.np.unique(x,return_counts=True)
        if len(levels)<3 or min(counts)<2:
            raise ValueError('当前批次拟合要求至少 3 个 AC 质量比例水平，每水平至少 2 个独立孔。')
        model=self.api.fit_reporter_calibration(x,y);validation=[]
        for level in levels:
            train=x!=level;fm=self.api.fit_reporter_calibration(x[train],y[train])
            for i in self.np.flatnonzero(~train):
                inv=self.inverse(fm,y[i]);pred=self.cal.predict(fm,[x[i]])[0]
                validation.append({'sample_id':refs[i]['sample_id'],'held_fraction':float(level),'observed_ras':float(y[i]),
                    'predicted_ras':float(pred) if self.np.isfinite(pred) else None,'inverse':inv,
                    'forward_error':float(pred-y[i]) if self.np.isfinite(pred) else None,
                    'inverse_error_pp':float(100*(inv['point']-x[i])) if inv['point'] is not None else None})
        errors=[abs(v['forward_error']) for v in validation if v['forward_error'] is not None]
        discrepancy=float(self.np.quantile(errors,.95)) if errors else None
        rng=self.np.random.default_rng(theta['config']['seed']);models=[];bootstrap_ids=[]
        for b in range(repeats):
            ids=self.np.concatenate([rng.choice(self.np.flatnonzero(x==v),int((x==v).sum()),replace=True) for v in levels])
            yy=self.np.array([draws[refs[i]['sample_id']][b] for i in ids])
            if self.np.isfinite(yy).all():
                models.append(self.api.fit_reporter_calibration(x[ids],yy));bootstrap_ids.append(b)
        grid=self.np.linspace(model['x_min'],model['x_max'],1001)
        curves=self.np.array([self.cal.predict(m,grid) for m in models])
        band=None if not len(curves) else self.np.quantile(curves,[.025,.975],axis=0)
        identity={'context_id':theta['context_id'],'population':population,'references':[{'sample_id':s['sample_id'],'sha256':s['input_sha256'],'fraction':s['ac_fraction'],'ras':s['RAS']['ras']} for s in refs]}
        model.update(model_id='RES-batch-'+stable_hash(identity)[:16],context_id=theta['context_id'],population_mode=population,
            qualification='SAME_BATCH_RESEARCH_CALIBRATION_NO_EXTERNAL_VALIDATION',reference_identity=identity,
            validation=validation,reference_n=len(refs),levels=levels.tolist(),internal_discrepancy_q95=discrepancy,
            reference_points=[{'sample_id':s['sample_id'],'fraction':s['ac_fraction'],'ras':s['RAS']['ras']} for s in refs],
            uncertainty={'grid':grid.tolist(),'lower':None if band is None else band[0].tolist(),'upper':None if band is None else band[1].tolist(),
                'bootstrap_models':models,'bootstrap_ids':bootstrap_ids,'total_draws':repeats,'successful_model_draws':len(models),
                'scope':'reference-level-stratified independent-well resampling with paired event/shared-Mock draws; no external batch uncertainty'})
        return self.api.clean(model)

    def res(self, sample, model, theta, calibration_mode, draw_values):
        ras=sample['RAS']['ras'];u=sample['RAS'].get('uncertainty',{});interval=[u.get('event_control_ci_low'),u.get('event_control_ci_high')]
        if any(v is None for v in interval):interval=None
        if calibration_mode=='frozen':
            result=self.api.calculate_res(ras,context_id=theta['context_id'],population_mode=sample['RAS']['population_mode'],
                calibration_domain_id='NEW_USER_BATCH_UNVALIDATED_TRANSFER',ras_interval=interval,model=self.p.model)
            compatible_population=sample['RAS']['population_mode']==self.p.model['population_mode']
            result['model_estimate_res_mass_fraction']=result['hypothetical_incompatible_mapping'] if compatible_population else None
            result['application_status']='S7_MODEL_ESTIMATE_TRANSFER_UNVALIDATED' if compatible_population else 'INCOMPATIBLE_POPULATION_NO_RES'
            result['display_label']='RES · S7 模型估计（跨批次未验证）'
            return result
        point=self.inverse(model,self.np.nan if ras is None else ras);success=[];ur=model['uncertainty']
        for b,m in zip(ur['bootstrap_ids'],ur['bootstrap_models']):
            inv=self.inverse(m,draw_values[b] if b<len(draw_values) else self.np.nan)
            if inv['low'] is not None:success.append([inv['low'],inv['high']])
        conditional=None if not success else [float(self.np.quantile(self.np.array(success)[:,0],.025)),float(self.np.quantile(self.np.array(success)[:,1],.975))]
        ranges=[];lo=hi=None
        if ras is not None and ur['lower'] is not None:
            margin=0 if interval is None else max(ras-interval[0],interval[1]-ras,0)
            discrepancy=model['internal_discrepancy_q95'] or 0
            low=self.np.array(ur['lower'])-margin-discrepancy;high=self.np.array(ur['upper'])+margin+discrepancy
            ranges,lo,hi=self.set_ranges(self.np.array(ur['grid']),(low<=ras)&(high>=ras))
        return {'model_id':model['model_id'],'context_profile_id':theta['context_id'],'population_mode':sample['RAS']['population_mode'],
            'res_mass_fraction':point['point'],'research_res_mass_fraction':point['point'],'model_estimate_res_mass_fraction':point['point'],
            'output_unit':'AC_DNA_mass_equivalent_fraction_0_to_1','numerical_status':point['status'],
            'exact_inverse_interval':[point['low'],point['high']] if point['low'] is not None else None,
            'conditional_bootstrap_interval':conditional,'bootstrap_success_n':len(success),'bootstrap_total_n':ur['total_draws'],
            'compatibility_intervals':ranges,'compatibility_low':lo,'compatibility_high':hi,
            'application_status':'SAME_BATCH_RESEARCH_MODEL','scientific_status':'INTERNAL_RESEARCH_NOT_ROUTINE_OR_RNA_EDITING',
            'routine_res_mass_fraction':None,'validated_RNA_editing_fraction':None,
            'uncertainty_status':'CONDITIONAL_BOOTSTRAP_AND_INTERNAL_COMPATIBILITY_NOT_VALIDATED_95CI',
            'display_label':'RES · 本批次参考等效研究值'}

    def run(self, specification):
        self.p._ensure_current_identity()
        rows=specification.get('files',[]);mapping=specification.get('channel_map',{});population=specification.get('population','reporter')
        mode=specification.get('calibration_mode','frozen');repeats=specification.get('bootstrap_repeats',200)
        if population not in ('reporter','blue_positive_reporter','blue_negative_reporter') or mode not in ('frozen','batch'):
            raise ValueError('未知测量群体或校准模式。')
        if repeats not in (200,500,1000,2000):raise ValueError('bootstrap_repeats 支持 200、500、1000 或 2000。')
        if not 2<=len(rows)<=128:raise ValueError('请提交 Mock 和待测样本，总文件数 2–128。')
        if not str(specification.get('cell_type','')).strip() or not str(specification.get('reporter_construct','')).strip():
            raise ValueError('请填写细胞类型和 reporter 构建身份。')
        entries=[];ids=set();wells=set();hashes=set();total=0
        for r in rows:
            token=safe_id(r['token']);info=read_json(self.p.workspace/'uploads'/(token+'.json'));path=self.p.workspace/'uploads'/(token+'.fcs')
            sid=safe_id(r['sample_id']);well=safe_id(r['well_id']);role=r.get('role','sample')
            if role not in ('mock','sample','reference'):raise ValueError('请为每个文件指定 Mock、样本或 AC/INAC 参考角色。')
            if sid in ids or well in wells or info['sha256'] in hashes:raise ValueError('样本 ID、独立孔 ID、FCS 采集必须唯一；不能重复增加 n。')
            if sha(path)!=info['sha256']:raise ValueError('上传后文件内容已变化。')
            fraction=None
            if role=='reference':
                try:fraction=float(r['ac_fraction'])
                except (ValueError,KeyError,TypeError):raise ValueError('参考孔需要 0–1 的 AC DNA 质量比例。')
                if not self.np.isfinite(fraction) or not 0<=fraction<=1:raise ValueError('参考孔 AC 质量比例必须在 0–1。')
            flag=r.get('linked_editor_present',False)
            if not isinstance(flag,bool):raise ValueError('editor linkage 必须为 true/false。')
            entry={**r,'sample_id':sid,'well_id':well,'role':role,'ac_fraction':fraction,'linked_editor_present':flag,
                'original_filename':info['original_filename'],'original_label':r.get('original_label',info['original_filename']),
                'sha256':info['sha256'],'condition_label':str(r.get('condition_label','')),'path':path}
            entries.append(entry);ids.add(sid);wells.add(well);hashes.add(info['sha256']);total+=info['bytes']
        if total>600*1024*1024:raise ValueError('本批次总大小超过 600 MiB。')
        if not any(e['role']!='mock' for e in entries):raise ValueError('至少需要一个样本或参考孔。')
        runs=self.p.workspace/'analyses';runs.mkdir(exist_ok=True);run_id='analysis-'+uuid.uuid4().hex[:12]
        temp=Path(tempfile.mkdtemp(prefix='.pending-',dir=runs))
        try:
            for e in entries:
                dest=temp/'inputs'/(e['sample_id']+'.fcs');dest.parent.mkdir(exist_ok=True);shutil.copyfile(e['path'],dest);e['path']=dest
            theta=self.theta(entries,mapping,str(specification['cell_type']))
            masks=temp/'masks';masks.mkdir(exist_ok=True)
            for e in entries:
                if e['role']=='mock':
                    x,_,_,_=self.read(e['path'],mapping)
                    q,c,s,_,_=self.core.gate(x,theta['gate_parameters'],theta['config'])
                    self.np.savez_compressed(masks/(e['sample_id']+'.npz'),quality=q,cell=c,singlet=s)
            shared=self.np.random.default_rng(theta['config']['seed']).multivariate_normal([0,0],theta['background_GR_covariance'],size=repeats)
            samples=[];draws={}
            for e in entries:
                if e['role']=='mock':continue
                processed=self.processed(e,theta,population);r,d=self.ras(processed,population,repeats,shared);draws[e['sample_id']]=d
                masks=temp/'masks';masks.mkdir(exist_ok=True);self.np.savez_compressed(masks/(e['sample_id']+'.npz'),**processed['masks'])
                x=processed['array'];ix=self.np.linspace(0,len(x)-1,min(1200,len(x)),dtype=int)
                samples.append({'sample_id':e['sample_id'],'well_id':e['well_id'],'role':e['role'],'condition_label':e['condition_label'],
                    'original_label':e['original_label'],'ac_fraction':e['ac_fraction'],'input_sha256':e['sha256'],'RAS':r,
                    'qc':processed['qc'],'optical':processed['optical'],'diagnostic_points':self.np.column_stack([self.np.arcsinh(x[ix,9]/150),self.np.arcsinh(x[ix,5]/150),processed['masks'][population][ix]]).tolist()})
            model=self.p.model if mode=='frozen' else self.fit_batch_model(samples,draws,repeats,theta,population)
            for s in samples:s['RES']=self.res(s,model,theta,mode,draws[s['sample_id']])
            public_entries=[{**{k:v for k,v in e.items() if k!='path'},'file_path':'inputs/'+e['sample_id']+'.fcs'} for e in entries]
            report=self.api.clean({'run_id':run_id,'name':str(specification.get('name','New experiment'))[:120],'pipeline_version':VERSION,
                'cell_type':specification['cell_type'],'reporter_construct':specification['reporter_construct'],
                'population':population,'calibration_mode':mode,'bootstrap_repeats':repeats,'Theta':theta,'model':model,'samples':samples,
                'inputs':public_entries,'specification':specification,'PER':None,'PER_status':'OUTSIDE_LAYER_0_TO_2_WORKFLOW',
                'provenance':{'pipeline_sha256':sha(Path(__file__)),'kernel_sha256':sha(self.p.root/'src/core.py'),
                    'reference_model_sha256':self.p.model_hash,'reference_manifest_sha256':self.p.release_hash},
                'notes':['Theta is a parameter object, not a scalar editing score.','RAS uses paired signed linear sums.',
                    'RES is AC DNA mass equivalent; no output here is an RNA editing fraction.',
                    'Frozen S7 applications to new contexts are explicit unvalidated model estimates; routine-qualified RES remains null.']})
            write_json(temp/'Theta.json',theta);write_json(temp/'model.json',model);write_json(temp/'results.json',report)
            write_json(temp/'batch.json',{'inputs':public_entries,'specification':{k:v for k,v in specification.items() if k!='files'}})
            write_json(temp/'artifact_manifest.json',{p.relative_to(temp).as_posix():sha(p) for p in temp.rglob('*') if p.is_file()})
            temp.rename(runs/run_id)
            return report
        except Exception:
            shutil.rmtree(temp);raise

    def list_runs(self):
        result=[]
        for p in sorted((self.p.workspace/'analyses').glob('*/results.json'),reverse=True):
            d=read_json(p);result.append({'run_id':d['run_id'],'name':d['name'],'samples':len(d['samples']),'calibration_mode':d['calibration_mode']})
        return result

    def load(self, run_id):
        base=self.p.workspace/'analyses'/safe_id(run_id)
        manifest=read_json(base/'artifact_manifest.json')
        for name,digest in manifest.items():
            if sha(contained(base,name))!=digest:raise ValueError('此分析的输入或输出已变化，需重新分析：'+name)
        d=read_json(base/'results.json')
        if d['provenance']['pipeline_sha256']!=sha(Path(__file__)) or d['provenance']['kernel_sha256']!=sha(self.p.root/'src/core.py'):
            raise ValueError('计算方法版本改变，旧分析需重新计算。')
        if d['calibration_mode']=='frozen' and d['provenance']['reference_model_sha256']!=sha(self.p.root/'models/res_primary/model.json'):
            raise ValueError('RES 标尺版本改变，旧分析需重新计算。')
        return d

    def rerun(self, directory):
        base=Path(directory).resolve();b=read_json(base/'batch.json');rows=[]
        for e in b['inputs']:
            p=contained(base,e['file_path'])
            if sha(p)!=e['sha256']:raise ValueError('复现输入哈希不匹配。')
            uploaded=self.upload(p.read_bytes(),e['original_filename']);rows.append({**e,'token':uploaded['token']})
        return self.run({**b['specification'],'files':rows})

    def export(self, run_id):
        import csv
        d=self.load(run_id);base=self.p.workspace/'analyses'/safe_id(run_id);stream=io.StringIO(newline='')
        rows=[flatten({k:v for k,v in s.items() if k!='diagnostic_points'}) for s in d['samples']]
        writer=csv.DictWriter(stream,fieldnames=list(dict.fromkeys(k for r in rows for k in r)));writer.writeheader()
        writer.writerows([{k:csv_safe(v) for k,v in r.items()} for r in rows])
        es=html.escape;display=lambda v:'Unavailable' if v is None else f'{v:.6g}'
        htmlrows=''.join('<tr>'+''.join('<td>'+es(str(v))+'</td>' for v in [s['sample_id'],s['condition_label'],display(s['RAS']['ras']),display(None if s['RES']['model_estimate_res_mass_fraction'] is None else 100*s['RES']['model_estimate_res_mass_fraction']),s['RES']['application_status'],s['RES']['numerical_status']])+'</tr>' for s in d['samples'])
        report=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>SONAR Θ / RAS / RES</title><style>body{{font:15px/1.6 system-ui;margin:40px;color:#234d40}}table{{border-collapse:collapse}}td,th{{padding:10px;border:1px solid #ddd;text-align:left}}code{{word-break:break-all}}.table{{overflow:auto}}</style><h1>{es(d['name'])} · Θ → RAS → RES</h1><p>Θ: <code>{es(d['Theta']['theta_id'])}</code> · {es(d['population'])}</p><p>RES 单位为 AC DNA 质量参考等效 %。S7 模型用于新批次时是明确标记的未验证转移估计；本批次参考拟合是研究校准，均非 RNA 编辑百分比。</p><div class="table"><table><tr><th>Sample</th><th>Condition</th><th>RAS</th><th>RES model estimate (% mass eq.)</th><th>Application status</th><th>Numerical status</th></tr>{htmlrows}</table></div><p>完整 Θ、signed sums、bootstrap 分母、兼容范围、模型、输入和版本哈希见 JSON/CSV。区间未经名义 95% 覆盖率验证。</p><p>解压本报告后，在相同锁定 Python 环境运行：</p><pre>python -m sonar_app pipeline-rerun . --output rerun.json</pre><p>报告包含此次上传的原始 FCS，仅用于本地内部研究。</p></html>'''
        output=io.BytesIO()
        with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
            for p in base.rglob('*'):
                if p.is_file():z.write(p,p.relative_to(base).as_posix())
            z.writestr('measurements.csv','\ufeff'+stream.getvalue());z.writestr('report.html',report)
            z.write(self.p.root/'environment/requirements.lock.txt','requirements.lock.txt')
        return output.getvalue()
