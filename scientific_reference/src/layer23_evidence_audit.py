"""Search supplied primary records and permitted construct documentation for blockers."""
import re,json
from pathlib import Path
import pandas as pd,numpy as np
import openpyxl
from Bio import SeqIO
from layer23_common import *

def run():
    inventory=[];hits=[];constructs=[]
    terms={'RNA_controls':r'(?i)DNase|no[ -_]?RT|minus[ -_]?RT|去除.?DNA|去.?基因组|不加逆转录|\bNTC\b', 'population':r'(?i)sort(ed|ing)?|FACS|分选|bulk|剩余细胞', 'optics':r'(?i)single[ -]?colou?r|单色|FMO|compensation|spillover', 'reference_identity':r'(?i)(?<![A-Za-z])INAC(?![A-Za-z])|(?<![A-Za-z])AC(?![A-Za-z])|locked'}
    sources=list((ROOT/'inputs/S7').rglob('*'))+list((ROOT/'inputs/S10').rglob('*'))+list((ROOT/'reference/layer23/construct_records').glob('*'))
    for p in sorted(sources):
        if not p.is_file() or p.name.startswith(('.', '~$')):continue
        ext=p.suffix.lower();units=[];status='binary_raw_or_image_inventoried_separately'
        if ext=='.xlsx':
            wb=openpyxl.load_workbook(p,data_only=True)
            for s in wb:
                for row in s:
                    for c in row:
                        if isinstance(c.value,str):units.append((f'{s.title}!{c.coordinate}',c.value))
            status='all_text_cells_searched'
        elif ext in ['.txt','.xml','.config','.xit','.seq','.fasta']:
            b=p.read_bytes()
            if b.startswith((b'<?xml',b'<',b'\xef\xbb\xbf')) or ext in ['.txt','.seq','.fasta','.config','.xml']:
                text=b.decode('utf-8',errors='replace');units=[('text',text)];status='text_searched'
        elif ext in ['.gb','.dna']:
            fmt='genbank' if ext=='.gb' else 'snapgene'
            try:
                rec=SeqIO.read(p,fmt);labels=[str(v) for f in rec.features for vals in f.qualifiers.values() for v in vals];units=[('features',';'.join(labels))]
                constructs.append(dict(source=str(p.relative_to(ROOT)),sha256=sha(p),length_bp=len(rec),format=fmt,record_id=rec.id,labels=';'.join(labels),exact_S7_AC_INAC_identity_verified=False))
                status='construct_sequence_and_annotations_read'
            except Exception as e:status='UNREADABLE_'+type(e).__name__
        inventory.append(dict(source=str(p.relative_to(ROOT)),sha256=sha(p),extension=ext,inspection=status))
        for loc,txt in units:
            for category,pattern in terms.items():
                matches=list(re.finditer(pattern,txt))
                for m in matches[:30]:hits.append(dict(source=str(p.relative_to(ROOT)),location=loc,category=category,matched=m.group(),context=txt[max(0,m.start()-75):m.end()+110].replace('\n',' '),interpretation='search_hit_not_proof_of_experimental_control'))
    table('results/molecular/source_record_audit.csv',inventory);table('results/molecular/source_record_search_hits.csv',hits);table('results/molecular/construct_document_audit.csv',constructs)
    # User-confirmed cell type is metadata only, never an upstream numerical change.
    for name in ['acquisition_manifest.csv','acquisition_file_manifest.csv']:
        p=ROOT/'inventory'/name;d=pd.read_csv(p);d.loc[d.sample_role!='Mock','cell_type']='HEK293T';d['cell_type_source']=np.where(d.sample_role!='Mock','reference/layer23/user_request.txt section 3','unconfirmed_Mock_specific_record');table(str(p.relative_to(ROOT)),d)
    # Anomaly inspection uses preserved flow outputs and masks, with no retuning.
    ras=pd.read_csv(ROOT/'results/ras_results.csv');s=ras[(ras.series=='S7')&(ras.population_mode=='reporter')].copy()
    ret=pd.read_csv(ROOT/'results/event_retention.csv');inf=pd.read_csv(ROOT/'results/high_expression_influence.csv');inf=inf[inf.population_mode=='reporter']
    q=s.merge(ret[['acquisition_id','after_singlet','rate_removed']],on='acquisition_id').merge(inf[['acquisition_id','top_one_percent_red_share','relative_change_without_top_one_percent']],on='acquisition_id')
    table('results/calibration/S7_anomaly_well_diagnostics.csv',q[q.condition_label.isin([50,75,90,100])][['acquisition_id','condition_label','replicate_label','mean_G_raw','mean_R_raw','mean_G_corrected','mean_R_corrected','ras','event_control_ci_low','event_control_ci_high','n_selected','after_singlet','rate_removed','top_one_percent_red_share','relative_change_without_top_one_percent']])
    sens=pd.read_csv(ROOT/'results/sensitivity.csv');sens=sens[(sens.population_mode=='reporter')&sens.acquisition_id.isin(s.acquisition_id)].merge(s[['acquisition_id','condition_label']],on='acquisition_id')
    sensitivity=[]
    for scenario,z in sens.groupby('scenario'):
        means=z.groupby('condition_label').ras.mean();sensitivity.append(dict(scenario=scenario,RAS75=means[75],RAS90=means[90],RAS100=means[100],delta_90_minus_75=means[90]-means[75],reversal_retained=means[90]<means[75]))
    table('results/calibration/S7_anomaly_sensitivity.csv',sensitivity)
    fcs=pd.read_csv(ROOT/'inventory/acquisition_manifest.csv')
    from core import read_fcs,G,R
    distributions=[];quantiles=[];edges=np.r_[-np.inf,np.linspace(-1,6.5,91),np.inf]
    for row in fcs[(fcs.series=='S7')&fcs.condition_label.isin([75,90,100])].itertuples():
        x,_=read_fcs(ROOT/row.file_path);mask=np.load(ROOT/'masks'/f'{row.acquisition_id}.npz')['reporter'];x=x[mask]
        for label,col in [('EGFP',G),('mCherry',R)]:
            values=x[:,col];v=np.log10(np.maximum(values,.01));counts,_=np.histogram(v,edges)
            for i,n in enumerate(counts):distributions.append(dict(acquisition_id=row.acquisition_id,condition_label=row.condition_label,replicate_label=row.replicate_label,channel=label,bin_index=i,log10_left=float(edges[i]) if np.isfinite(edges[i]) else None,log10_right=float(edges[i+1]) if np.isfinite(edges[i+1]) else None,events=int(n),fraction=n/len(values),total_selected=len(values),axis='log10_raw_linear_fluorescence_display_only'))
            for p in [.01,.05,.25,.5,.75,.95,.99]:quantiles.append(dict(acquisition_id=row.acquisition_id,condition_label=row.condition_label,channel=label,quantile=p,value=float(np.quantile(values,p)),units='raw_linear_detector_au'))
    table('results/calibration/S7_anomaly_distributions.csv',distributions);table('results/calibration/S7_anomaly_distribution_quantiles.csv',quantiles)
    compat=[('cell_type','HEK293T_user_confirmed','HEK293T_user_confirmed','MATCH'),('detector_profile','same recorded CytoFLEX S profile','same profile','MATCH_NOT_SUFFICIENT'),('population','reporter eligible','reporter eligible or R+B+','REPORTER_MATCH_BPOS_MISMATCH'),('reporter_architecture','AC/INAC exact sequences and lengths unverified','OpenA reconstructed amplicon; full construct unknown','UNRESOLVED'),('reporter_loading','per-well amount unresolved','100 ng/well','UNRESOLVED'),('treatment_TMP','unresolved','unresolved','UNRESOLVED'),('editor_presence','BFP label does not verify linked editor','ORCA-P2A-BFP at variable doses','UNRESOLVED_REFERENCE_BRIDGE'),('reference_axis','AC DNA mass mixture','editor DNA dose; unknown actual RNA state','DIFFERENT_EXPERIMENTAL_AXIS'),('molecular_population','not applicable','RNA cell population undocumented','UNRESOLVED')]
    table('results/calibration/S7_S10_compatibility.csv',[dict(dimension=a,S7=b,S10=c,status=d,calibration_transfer_qualified=False) for a,b,c,d in compat])
    jsonout('results/molecular/source_audit_summary.json',dict(files_inspected=len(inventory),construct_documents=len(constructs),RNA_control_hits=sum(h['category']=='RNA_controls' for h in hits),population_hits=sum(h['category']=='population' for h in hits),S7_plate_workbooks=sum(Path(r['source']).suffix=='.xlsx' and r['source'].startswith('inputs/S7') for r in inventory),single_color_controls_present=False,exact_AC_INAC_lengths_verified=False,actual_available_FCS_labels=fcs.acquisition_id.tolist(),scope='Only S7/S10 experimental materials; generic construct documents allowed; source photos re-reviewed separately'))
    print('Source audit',len(inventory),'files',len(hits),'search hits',flush=True)

if __name__=='__main__':run()
