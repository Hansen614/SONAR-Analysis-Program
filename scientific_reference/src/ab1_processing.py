"""Original PBAS2/PCON2/PLOC2 and per-file dye mapping, with byte-level cross-check."""
import struct
from pathlib import Path
import numpy as np
from Bio import SeqIO,Align
from Bio.Seq import Seq
from layer23_common import CFG

def byte_tags(path):
    b=Path(path).read_bytes()
    assert b[:4]==b'ABIF'
    version=struct.unpack('>H',b[4:6])[0]
    fmt='>4sIHHIIII';root=struct.unpack_from(fmt,b,6);count,offset=root[4],root[6]
    tags={}
    for j in range(count):
        pos=offset+28*j;name,number,typ,size,n,bytes_n,off,handle=struct.unpack_from(fmt,b,pos)
        value=b[pos+20:pos+20+bytes_n] if bytes_n<=4 else b[off:off+bytes_n]
        tags[name.decode()+str(number)]=(typ,size,n,value)
    return version,tags

def read_ab1(path):
    rec=SeqIO.read(path,'abi');raw=rec.annotations['abif_raw'];version,tags=byte_tags(path)
    seq=raw['PBAS2'].decode();q=np.frombuffer(raw['PCON2'],dtype=np.uint8).copy();loc=np.asarray(raw['PLOC2'],int)
    assert seq==str(rec.seq) and len(seq)==len(q)==len(loc)
    order=raw['FWO_1'].decode();assert len(order)==4 and set(order)==set('ACGT')
    assert tags['PBAS2'][3].decode()==seq and tags['FWO_1'][3].decode()==order
    np.testing.assert_array_equal(np.frombuffer(tags['PLOC2'][3],dtype='>i2'),loc)
    np.testing.assert_array_equal(np.frombuffer(tags['PCON2'][3],dtype='u1'),q)
    traces={}
    for i,base in enumerate(order):
        key=f'DATA{i+9}';v=np.asarray(raw[key],float)
        np.testing.assert_array_equal(np.frombuffer(tags[key][3],dtype='>i2'),v)
        traces[base]=v
    assert len(set(len(v) for v in traces.values()))==1
    assert (np.diff(loc)>0).all() and loc.min()>=0 and loc.max()<len(traces['A'])
    assert not raw.get('RevC1',0),'Unexpected reversed ABIF storage requires separate mapping'
    label,direction=Path(path).name.split('.')[:2];assert direction in ['F','R']
    oriented=seq if direction=='F' else str(Seq(seq).reverse_complement())
    oq=q if direction=='F' else q[::-1]
    window=CFG['trim_window_bases'];good=np.convolve((oq>=20).astype(int),np.ones(window,int),'valid')>=CFG['trim_window_min_Q20'];idx=np.flatnonzero(good)
    trim=(int(idx[0]),int(idx[-1]+window)) if len(idx) else (0,0)
    return dict(path=Path(path),read_id=Path(path).stem,label=label,direction=direction,seq=seq,q=q,loc=loc,traces=traces,order=order,version=version,oriented=oriented,oriented_q=oq,trim=trim,raw=raw)

def aligner(gap_open=None):
    c=CFG['alignment']
    return Align.PairwiseAligner(mode='local',match_score=c['match'],mismatch_score=c['mismatch'],open_gap_score=c['gap_open'] if gap_open is None else gap_open,extend_gap_score=c['gap_extend'])

def reference_map(reference,read,gap_open=None):
    key=(reference,gap_open)
    cache=read.setdefault('_alignment_cache',{})
    if key in cache:return cache[key]
    a=aligner(gap_open).align(reference,read['oriented'])[0];ix=a.indices
    mapping={int(i):int(j) for i,j in ix.T if i>=0 and j>=0}
    cache[key]=(mapping,a)
    return mapping,a

def original_index(read,oriented_index):
    return oriented_index if read['direction']=='F' else len(read['seq'])-1-oriented_index

def site_metrics(reference,read,position):
    mp,a=reference_map(reference,read);i=position-1;direction=read['direction'];ref,alt=('C','T') if direction=='F' else ('G','A')
    out=dict(read_id=read['read_id'],sample_label=read['label'],direction=direction,position_1based=position,reference_base_forward='C',alternative_base_forward='T',trace_reference_base=ref,trace_alternative_base=alt,dye_order=read['order'],abif_version=read['version'],source_AB1=str(read['path']),mapping_status='UNMAPPED',signal_status='UNAVAILABLE')
    if i not in mp:return out
    j=mp[i];orig=original_index(read,j);loc=int(read['loc'][orig]);tr=read['traces'];q=read['q']
    flank=[k for k in range(max(0,i-10),min(len(reference),i+11)) if k!=i]
    matches=[reference[k]==read['oriented'][mp[k]] for k in flank if k in mp]
    flank_identity=sum(matches)/len(flank)
    flank_q=[read['oriented_q'][mp[k]] for k in flank if k in mp]
    stable=all(reference_map(reference,read,go)[0].get(i)==j for go in [-6,-12])
    l=int((read['loc'][orig-1]+loc)//2) if orig>0 else loc-3
    h=int((read['loc'][orig+1]+loc)//2) if orig+1<len(q) else loc+4
    l=max(0,l);h=min(len(tr['A']),h)
    wl=int(read['loc'][max(0,orig-4)]);wh=int(read['loc'][min(len(q)-1,orig+4)])+1
    base={b:float(np.quantile(v[wl:wh],CFG['baseline_quantile'])) for b,v in tr.items()}
    point={b:float(v[loc]) for b,v in tr.items()}
    near={b:float(v[max(l,loc-2):min(h,loc+3)].max()) for b,v in tr.items()}
    area={b:float(np.sum(v[l:h])) for b,v in tr.items()}
    corrected={b:max(0.,point[b]-base[b]) for b in 'ACGT'}
    def ratio(v):return v[alt]/(v[ref]+v[alt]) if v[ref]+v[alt]>0 else np.nan
    other=sum(point[b] for b in 'ACGT' if b not in [ref,alt])/sum(point.values()) if sum(point.values()) else np.nan
    reasons=[]
    if flank_identity<CFG['site_flank_min_identity']:reasons.append('LOW_FLANK_ALIGNMENT_IDENTITY')
    if np.median(flank_q)<CFG['site_flank_min_median_phred']:reasons.append('LOW_FLANK_QUALITY')
    if not stable:reasons.append('ALIGNMENT_PARAMETER_SENSITIVE')
    if other>CFG['site_max_other_base_fraction']:reasons.append('OTHER_BASE_CONTAMINATION')
    if not np.isfinite(ratio(point)):reasons.append('ZERO_PEAK_DENOMINATOR')
    out.update(mapping_status='MAPPED_STABLE' if stable else 'MAPPING_UNSTABLE',oriented_base_index_1based=j+1,AB1_base_index_1based=orig+1,scan_index_0based=loc,called_base=read['seq'][orig],target_phred=int(q[orig]),flank_median_phred=float(np.median(flank_q)),flank_identity=flank_identity,other_base_fraction=other,aligned_context=read['oriented'][max(0,j-10):j+11],reference_context=reference[max(0,i-10):i+11],peak_reference=point[ref],peak_alternative=point[alt],baseline_reference=base[ref],baseline_alternative=base[alt],raw_peak_ratio=ratio(point),baseline_peak_ratio=ratio(corrected),nearby_max_ratio=ratio(near),peak_area_ratio=ratio(area),raw_alt_all_four=point[alt]/sum(point.values()),eligible=not reasons,failure_reasons=';'.join(reasons),signal_status='EXPLORATORY_PEAK_COMPOSITION' if not reasons else 'UNAVAILABLE_SITE_QC',qualified_signal=ratio(point) if not reasons else None)
    for b in 'ACGT':out[f'peak_{b}']=point[b]
    return out
