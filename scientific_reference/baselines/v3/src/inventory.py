"""Fresh source inventory; no previous SONAR implementation is imported."""
from pathlib import Path
import json, hashlib, shutil, csv, re
import numpy as np
from flowio import FlowData
from Bio import SeqIO
from sample_metadata import flow_metadata

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parents[1]
SERIES = {'S7':'S7 AC:INAC ver.2 fcs','S10':'S10 EDIT fcs&mby&seq'}
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write_csv(path, rows):
    if not rows: return
    keys=list(dict.fromkeys(k for r in rows for k in r))
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=keys); w.writeheader()
        for row in rows:
            w.writerow({k:(None if isinstance(v,(float,np.floating)) and not np.isfinite(v) else v) for k,v in row.items()})
def dump(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')

def inventory():
    files=[]; acquisitions=[]; channels=[]; seen={}; reader=[]
    prior={}
    if (ROOT/'inventory/input_files.csv').exists():
        with (ROOT/'inventory/input_files.csv').open(encoding='utf-8-sig') as f:prior={r['packaged_path']:r['original_path'] for r in csv.DictReader(f)}
    for series,folder in SERIES.items():
        source=WORKSPACE/'Reporter'/folder
        if not source.exists():source=ROOT/'inputs'/series
        if not source.exists():raise FileNotFoundError(f'No authorized raw inputs for {series}')
        for p in sorted(source.rglob('*')):
            if not p.is_file() or p.name.startswith('.'): continue
            rel=Path(series)/p.relative_to(source); dest=ROOT/'inputs'/rel
            dest.parent.mkdir(parents=True,exist_ok=True)
            if not dest.exists(): shutil.copy2(p,dest)
            assert sha(p)==sha(dest), f'Immutable source copy differs: {p}'
            files.append(dict(series=series,original_path=prior.get(str(dest.relative_to(ROOT)),str(p)),packaged_path=str(dest.relative_to(ROOT)),sha256=sha(p),bytes=p.stat().st_size,extension=p.suffix,role='raw_or_source_record'))
            if p.suffix.lower()!='.fcs': continue
            fd=FlowData(str(dest)); raw=fd.as_array(preprocess=False); arr=fd.as_array(preprocess=True)
            meta=fd.text; h=sha(p)
            acq=seen.get(h,series+'_'+re.sub(r'[^A-Za-z0-9.]','_',p.stem))
            dup=h in seen; seen[h]=acq
            dump(ROOT/'inventory/fcs_metadata'/f'{series}_{p.stem}.json',meta)
            # Independent byte-level check is deliberately limited to this verified profile.
            b=p.read_bytes(); start=int(b[26:34]); stop=int(b[34:42])
            assert meta['datatype']=='F' and meta['byteord']=='1,2,3,4'
            independent=np.frombuffer(b[start:stop+1],dtype='<f4').reshape(fd.event_count,fd.channel_count)
            assert np.array_equal(raw,independent)
            expected=raw.astype(float); ti=fd.pnn_labels.index('Time'); expected[:,ti]*=float(meta['timestep'])
            assert np.array_equal(arr,expected)
            reader.append(dict(acquisition_id=acq,path=str(rel),max_reader_difference=float(np.max(np.abs(raw-independent))),max_linearization_difference=float(np.max(np.abs(arr-expected)))))
            mock=p.stem.upper().startswith('MOCK')
            label=meta.get('tbnm'); suffix=label[-1] if not mock else ''
            condition=None if mock else float(label[:-1].strip()) if series=='S7' else float(label.split()[1])
            prof={k:meta.get(k) for k in ['cyt','cytsn','compgaina','ch1gain','ch2gain','ch3gain','ch8gain','ch13gain','p1g','p2g','p6g','p8g','p10g','spillover','uscomp']}
            profile=hashlib.sha256(json.dumps(prof,sort_keys=True).encode()).hexdigest()[:12]
            acquisitions.append(dict(acquisition_id=acq,series=series,file_path=str(dest.relative_to(ROOT)),sha256=h,is_duplicate_file=dup,source_sample_label=label,filename_label=p.stem,label_agrees=label==p.stem,sample_id=acq,well_id=None,well_identity_status='unverified_A_B_to_well' if not mock else 'distinct_acquisition_well_unknown',biological_replicate_id=None,technical_parent_id=None,replicate_label=suffix,condition_label=condition,sample_role='Mock' if mock else 'AC_INAC_reference' if series=='S7' else 'reporter_editor',reporter_construct='AC/INAC_exact_sequences_unverified' if series=='S7' and not mock else 'RepOpenA_record_label' if not mock else None,editor_construct=None,editor_bfp_linked=None,reporter_dna_ng=None,editor_dna_ng=None,total_dna_ng=None,nominal_ac_label_pct=condition if series=='S7' else None,ac_fraction_basis=None,reporter_editor_label=condition if series=='S10' else None,treatment=None,sampling_time=None,acquisition_date=meta['date'],start_time=meta['btim'],end_time=meta['etim'],instrument=meta['cyt'],instrument_serial=meta['cytsn'],profile_id=profile,events=fd.event_count,abort_count=meta.get('abrt'),compensation_status='identity_matrix_USCOMP_False_optically_unvalidated',matched_mock_ids='S7_MOCK1;S7_MOCK2',rna_pair_id=None,split_role='context_development' if label=='MOCK1' else 'negative_transfer_check' if label=='MOCK2' else 'descriptive_analysis_no_validation_holdout',identity_source='FCS TBNM + folder + hand_record + dated user confirmation; remaining unresolved fields null'))
            acquisitions[-1].update(event_data_sha256=hashlib.sha256(b[start:stop+1]).hexdigest(),instrument_tube_uid=meta.get('tbid'),cell_type=None,culture_id=None,plate_id=None,viability_marker=None,compensation_control_set_id=None,reference_bead_id=None,mixture_process=None,AC_plasmid_length_bp=None,INAC_plasmid_length_bp=None,transfection_reagent='photo_mentions_Lipo3000_P3000_parameters_not_assigned',treatment_TMP=None)
            acquisitions[-1].update(flow_metadata(series,condition,suffix,acq))
            for i,c in fd.channels.items():
                channels.append(dict(acquisition_id=acq,source_series=series,index_1based=i,**c,display=meta.get(f'p{i}display'),bits=meta.get(f'p{i}b'),min=float(raw[:,i-1].min()),max=float(raw[:,i-1].max()),fraction_at_or_above_pnr=float(np.mean(raw[:,i-1]>=c['pnr'])),fraction_at_observed_max=float(np.mean(raw[:,i-1]==raw[:,i-1].max()))))
    write_csv(ROOT/'inventory/input_files.csv',files)
    write_csv(ROOT/'inventory/acquisition_file_manifest.csv',acquisitions)
    write_csv(ROOT/'inventory/acquisition_manifest.csv',[x for x in acquisitions if not x['is_duplicate_file']])
    write_csv(ROOT/'inventory/channel_metadata.csv',channels)
    write_csv(ROOT/'inventory/reader_crosscheck.csv',reader)
    return acquisitions

if __name__=='__main__':
    a=inventory(); print('FCS files:',len(a),'unique:',sum(not r['is_duplicate_file'] for r in a))
