"""Primer-anchored, reference-free F/R mosaics assembled separately for four controls."""
from collections import Counter
import numpy as np
import pandas as pd
from Bio import SeqIO,Align
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from Bio.SeqFeature import SeqFeature,FeatureLocation
from ab1_processing import read_ab1,aligner,reference_map
from layer23_common import *
F='ATGGCCGATAAGCAGAAGAACG'
R='CCACACTTTTCACCCAGGTCAC'
RC=str(Seq(R).reverse_complement())

def assemble_pair(forward,reverse):
    f,r=forward['oriented'],reverse['oriented'];fq,rq=forward['oriented_q'],reverse['oriented_q']
    al=aligner().align(f,r)[0];indices=al.indices
    eligible=[(int(i),int(j)) for i,j in indices.T if i>=0 and j>=0 and fq[i]>=30 and rq[j]>=30 and f[i]==r[j]]
    if len(eligible)<100:raise ValueError('Insufficient independent F/R overlap')
    i,j=eligible[len(eligible)//2];mosaic=r[:j]+f[i:]
    left=[(k,mosaic.find(F[-k:],0,45)) for k in range(8,len(F)+1) if mosaic.find(F[-k:],0,45)>=0]
    right=[(k,mosaic.rfind(RC[:k],len(mosaic)-45)) for k in range(8,len(RC)+1) if mosaic.rfind(RC[:k],len(mosaic)-45)>=0]
    if not left or not right:raise ValueError('Primer anchoring unavailable')
    lk,lp=max(left);rk,rp=max(right)
    assembled=F+mosaic[lp+lk:rp]+RC
    return assembled,dict(forward_seam_index_1based=i+1,reverse_oriented_seam_index_1based=j+1,Q30_exact_overlap_positions=len(eligible),left_primer_exact_overlap=lk,right_primer_exact_overlap=rk,assembled_length=len(assembled),left_terminal_primer_only_nominal=len(F)-lk,right_terminal_primer_only_nominal=len(RC)-rk)

def run():
    controls=[read_ab1(p) for p in sorted((ROOT/'inputs/S10/测序').rglob('1-0-*.ab1'))]
    assembled=[];pairs=[]
    for label in sorted(set(x['label'] for x in controls)):
        f=next(x for x in controls if x['label']==label and x['direction']=='F');r=next(x for x in controls if x['label']==label and x['direction']=='R')
        seq,info=assemble_pair(f,r);assembled.append(seq);pairs.append(dict(sample_label=label,**info))
    assert len(set(assembled))==1,'Control reconstructions disagree: retain ambiguity before quantification'
    consensus=assembled[0]
    # The supplied candidate is consulted only AFTER the independent assemblies are complete.
    candidate=str(SeqIO.read(ROOT/'reference/layer23/S10_OpenA_edit523_provisional_amplicon.fasta','fasta').seq)
    out=ROOT/'results/molecular'
    SeqIO.write(SeqRecord(Seq(consensus),id='S10_OpenA_consensus_523bp_v3',description='four no-editor AB1 F/R assemblies; primers supply uncertain termini; candidate site C280'),out/'OpenA_amplicon_consensus.fasta','fasta')
    table('results/molecular/OpenA_independent_control_assemblies.csv',pairs)
    rows=[];maps={r['read_id']:reference_map(consensus,r)[0] for r in controls}
    for i,base in enumerate(consensus):
        high=[];allcalls=[]
        for r in controls:
            j=maps[r['read_id']].get(i)
            if j is None:continue
            q=int(r['oriented_q'][j]);within=r['trim'][0]<=j<r['trim'][1]
            row=dict(position_1based=i+1,consensus_base=base,read_id=r['read_id'],sample_label=r['label'],direction=r['direction'],oriented_base_index_1based=j+1,call=r['oriented'][j],phred=q,within_quality_trim=within,eligible_Q20=q>=20 and within)
            allcalls.append(row)
            if row['eligible_Q20']:high.append(row)
        calls=Counter(r['call'] for r in high);agree=calls.get(base,0);labels=set(r['sample_label'] for r in high if r['call']==base);wells=set('A' if int(k.split('-')[-1])<=2 else 'B' for k in labels)
        status='BIDIRECTIONAL_Q20' if set(r['direction'] for r in high if r['call']==base)=={'F','R'} else 'UNIDIRECTIONAL_Q20' if high else 'PRIMER_INFERRED_NO_Q20' if i<22 or i>=len(consensus)-22 else 'LOW_CONFIDENCE_INTERNAL'
        rows.append(dict(position_1based=i+1,consensus_base=base,all_aligned_reads=len(allcalls),Q20_n=len(high),Q20_F_n=sum(r['direction']=='F' for r in high),Q20_R_n=sum(r['direction']=='R' for r in high),Q20_agreement_fraction=agree/len(high) if high else None,independent_wells_supporting=len(wells),molecular_labels_supporting=len(labels),median_Q20=float(np.median([r['phred'] for r in high])) if high else None,other_Q20_calls=';'.join(f'{b}:{n}' for b,n in sorted(calls.items()) if b!=base),evidence_status=status,primer_overlap=i<22 or i>=len(consensus)-22))
        # Detailed mappings preserve low-confidence calls without letting them vote.
        if i==0:long=[]
        long.extend(allcalls)
    table('results/molecular/OpenA_reference_alignment.csv',rows);table('results/molecular/OpenA_control_base_calls.csv',long)
    generic=SeqIO.read(ROOT/'inputs/construct_reference/REPORTER_assembled_from_4_primers.gb','genbank');g=str(generic.seq);start=g.index(F);stop=g.index(RC)+len(RC);amp=g[start:stop]
    ga=Align.PairwiseAligner(mode='global',match_score=2,mismatch_score=-3,open_gap_score=-8,extend_gap_score=-.5).align(amp,consensus)[0]
    ix=ga.indices;variants=[]
    for col,(i,j) in enumerate(ix.T):
        aa=amp[i] if i>=0 else '-';bb=consensus[j] if j>=0 else '-'
        variants.append(dict(alignment_column_1based=col+1,generic_amplicon_position_1based=i+1 if i>=0 else None,generic_plasmid_position_1based=start+i+1 if i>=0 else None,OpenA_position_1based=j+1 if j>=0 else None,generic_base=aa,OpenA_base=bb,match=aa==bb,operation='insertion_OpenA' if i<0 else 'deletion_OpenA' if j<0 else 'match' if aa==bb else 'substitution'))
    table('results/molecular/OpenA_generic_comparison.csv',variants)
    SeqIO.write([SeqRecord(Seq(''.join(v['generic_base'] for v in variants)),id='generic_544bp',description='general design only'),SeqRecord(Seq(''.join(v['OpenA_base'] for v in variants)),id='OpenA_523bp_reconstructed',description='no-editor AB1 consensus')],out/'OpenA_vs_generic.aligned.fasta','fasta')
    frame=(start-int(next(f.location.start for f in generic.features if f.qualifiers.get('label')==['EGFP'])))%3
    assert frame==0
    # Transfer only architectural coordinates with direct alignment support.
    egfp_end=int(next(f.location.end for f in generic.features if f.qualifiers.get('label')==['EGFP']))-start
    dhfr_start=int(next(f.location.start for f in generic.features if f.qualifiers.get('label')==['ecDHFR-DD']))-start
    direct={int(i):int(j) for i,j in ix.T if i>=0 and j>=0}
    egfp_end_new=direct[egfp_end-1]+1;dhfr_start_new=direct.get(dhfr_start)
    sites=[]
    for i,b in enumerate(consensus):
        if b!='C':continue
        cs=(i//3)*3;codon=consensus[cs:cs+3];alt=list(codon);alt[i%3]='T';alt=''.join(alt)
        if len(codon)!=3:continue
        region='EGFP' if i<egfp_end_new else 'switch_linker' if dhfr_start_new is not None and i<dhfr_start_new else 'DHFR_region'
        stopgain=codon not in ['TAA','TAG','TGA'] and alt in ['TAA','TAG','TGA']
        sites.append(dict(position_1based=i+1,reference_base='C',alternative_base='T',RNA_alternative='U',codon_start_1based=cs+1,reference_codon=codon,alternative_codon=alt,reference_aa=str(Seq(codon).translate()),alternative_aa=str(Seq(alt).translate()),stop_gain=stopgain,architecture_region=region,mechanistic_priority='CANDIDATE_SWITCH_STOP' if region=='switch_linker' and stopgain else 'OTHER_STOP_GAIN' if stopgain else 'OTHER_CYTIDINE',Q20_F_n=rows[i]['Q20_F_n'],Q20_R_n=rows[i]['Q20_R_n'],status='CANDIDATE_SITE_SUPPORTED' if i+1==280 else 'BYSTANDER_SCREEN_SITE',intended_target_independently_documented=False))
    table('results/molecular/OpenA_candidate_editing_sites.csv',sites)
    gb=SeqRecord(Seq(consensus),id='OpenA523_v3',name='OpenA523_v3',description='Reconstructed amplicon; not complete clone; target C280 candidate',annotations={'molecule_type':'DNA','topology':'linear'})
    gb.features=[SeqFeature(FeatureLocation(0,22),type='primer_bind',qualifiers={'label':['forward primer']}),SeqFeature(FeatureLocation(len(consensus)-22,len(consensus),strand=-1),type='primer_bind',qualifiers={'label':['reverse primer']}),SeqFeature(FeatureLocation(0,egfp_end_new),type='misc_feature',qualifiers={'label':['EGFP terminal segment; mapped general architecture']}),SeqFeature(FeatureLocation(egfp_end_new,dhfr_start_new),type='misc_feature',qualifiers={'label':['reconstructed linker']}),SeqFeature(FeatureLocation(279,282),type='misc_feature',qualifiers={'label':['candidate C280 CGA to TGA; intended target unconfirmed']})]
    SeqIO.write(gb,out/'OpenA_amplicon_annotated.gb','genbank')
    summary=dict(version=VERSION,length=len(consensus),candidate_fasta_exact_match=consensus==candidate,independent_transfection_wells=2,molecular_labels=4,read_n=8,all_four_assemblies_identical=True,frame_from_generic_EGFP=frame,EGFP_segment_end_1based=egfp_end_new,DHFR_mapped_start_1based=dhfr_start_new+1,alignment_counts=dict(Counter(v['operation'] for v in variants)),net_length_change=len(consensus)-len(amp),coverage_counts=dict(Counter(r['evidence_status'] for r in rows)),Q20_conflicting_positions=[r['position_1based'] for r in rows if r['other_Q20_calls']],no_Q20_positions=[r['position_1based'] for r in rows if not r['Q20_n']],candidate_site=next(r for r in sites if r['position_1based']==280),stop_gain_linker_sites=[r['position_1based'] for r in sites if r['mechanistic_priority']=='CANDIDATE_SWITCH_STOP'],consensus_sha256=sha(out/'OpenA_amplicon_consensus.fasta'),reference_qualification='AMPLICON_CENTRAL_SEQUENCE_SUPPORTED_TERMINI_PRIMER_INFERRED_TARGET_INTENT_PROVISIONAL')
    jsonout('results/molecular/OpenA_reconstruction_summary.json',summary)
    print('Reconstructed OpenA',summary,flush=True)
    return consensus

if __name__=='__main__':run()
