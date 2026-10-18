#!/usr/bin/env python3
"""Public CLI for the frozen SONAR scientific release. See documentation/API_CONTRACT.md."""
import os,sys,json,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parent
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'_work/matplotlib'))
sys.path.insert(0,str(ROOT/'src'))
from science_api import *

def main():
    p=argparse.ArgumentParser(description='SONAR scientific reference engine; no GUI required')
    sp=p.add_subparsers(dest='command',required=True)
    sp.add_parser('verify',help='Verify raw hashes, release dependencies and all regression tests')
    sp.add_parser('reproduce',help='Rebuild from packaged raw inputs in an isolated working directory and compare frozen results')
    sp.add_parser('finalize',help='Explicit scientific refit/build; for release maintenance, not routine app use')
    q=sp.add_parser('example',help='Run raw FCS -> context -> RAS -> RES -> report for a registered sample')
    q.add_argument('--sample',default='S7_90B');q.add_argument('--output',default='_work/example.json');q.add_argument('--mode',choices=['research','routine'],default='research')
    args=p.parse_args()
    if args.command=='finalize':
        from finalize_science import run
        run()
        from final_reports import run as reports
        reports()
    elif args.command=='reproduce':
        from release_verify import reproduce
        reproduce()
    elif args.command=='verify':
        from release_verify import verify
        verify()
    else:
        m=load_experiment();d=m[m.acquisition_id==args.sample]
        if len(d)!=1 or d.iloc[0].sample_role=='Mock':raise ValueError('Unknown experimental sample ID')
        md=d.iloc[0].to_dict();md['linked_editor_present']=md['series']=='S10' and md['condition_label']>0
        ctx=load_context();processed=process_fcs(ROOT/md['file_path'],ctx,md)
        old=pd.read_csv(ROOT/'results/ras_results.csv');o=old[(old.acquisition_id==args.sample)&(old.population_mode=='reporter')].iloc[0]
        u={k:o[k] for k in ['event_ci_low','event_ci_high','event_control_ci_low','event_control_ci_high','bootstrap_denominator_failure_fraction']}
        ras=calculate_ras(processed,uncertainty=u)
        res=calculate_res(ras['ras'],context_id=ctx['context_id'],population_mode='reporter',calibration_domain_id=FINAL['calibration_domain_id'] if md['series']=='S7' else 'S10_NO_QUALIFIED_TRANSFER',
            sample_id=args.sample,ras_interval=[u['event_control_ci_low'],u['event_control_ci_high']],mode=args.mode)
        sample={'sample_id':args.sample,'well_id':md['well_id'],'condition_label':md['condition_label'],'qc':processed['qc'],'RAS':ras,'RES':res,'PER':predict_per(res)}
        generate_measurement_report(ROOT/args.output,[sample]);print(json.dumps(clean(sample),indent=2))

if __name__=='__main__':main()
