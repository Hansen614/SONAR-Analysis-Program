"""Offline raw reconstruction and portable-release verification; historical paths never required."""
import shutil,subprocess,sys,json
import pandas as pd
import numpy as np
from science_api import ROOT,load_experiment,load_res_model,digest,save_json,RELEASE

def verify():
    load_experiment();load_res_model()
    result=subprocess.run([sys.executable,'-m','pytest','tests','-q'],cwd=ROOT,capture_output=True,text=True)
    (ROOT/'_work').mkdir(exist_ok=True)
    (ROOT/'_work/verification_tests.txt').write_text(result.stdout+result.stderr)
    print(result.stdout,flush=True)
    if result.returncode:raise RuntimeError('Tests failed; see _work/verification_tests.txt')
    print('PASS: packaged raw hashes, model dependency hashes, scientific tests',flush=True)

def run_stage(dest,code,name):
    log=ROOT/'_work'/f'rebuild_{name}.log'
    with log.open('w') as f:
        r=subprocess.run([sys.executable,'-u','-c',"import sys;sys.path.insert(0,'src');"+code],cwd=dest,stdout=f,stderr=subprocess.STDOUT)
    if r.returncode:raise RuntimeError('Raw rebuild failed at '+name+'; see '+str(log.relative_to(ROOT)))
    print('Rebuilt '+name,flush=True)

def reproduce():
    """Explicit scientific audit may refit; normal API and example commands only load frozen models."""
    load_experiment();dest=ROOT/'_work/raw_rebuild'
    if dest.exists():shutil.rmtree(dest)
    dest.mkdir(parents=True)
    for name in ['src','config','reference','models']:
        shutil.copytree(ROOT/name,dest/name,ignore=shutil.ignore_patterns('__pycache__'))
    # A real input copy also exercises the API's path-containment check.
    # No original user/workspace paths are accessed.
    shutil.copytree(ROOT/'inputs',dest/'inputs')
    (dest/'baselines').symlink_to(ROOT/'baselines',target_is_directory=True)
    for name in ['results/molecular','results/calibration','results/prediction','contexts','masks','inventory','figures/source_tables','reports','provenance','_work']:(dest/name).mkdir(parents=True,exist_ok=True)
    # Recreate upstream metadata view so immutable RAS bytes keep their historical labels.
    # Corrected labels are reapplied explicitly downstream, by stable acquisition ID.
    shutil.copytree(ROOT/'baselines/v3/inventory',dest/'inventory',dirs_exist_ok=True)
    shutil.copy2(ROOT/'inventory/input_files.csv',dest/'inventory/input_files.csv')
    shutil.copy2(ROOT/'baselines/v3/config/layer23.json',dest/'config/layer23.json')
    run_stage(dest,'import analyze;analyze.run()','raw_flow')
    assert digest(dest/'results/ras_results.csv')==digest(ROOT/'results/ras_results.csv'),'RAS bytes changed'
    run_stage(dest,'import layer23_evidence_audit,molecular_and_plate,amplicon_reconstruction,sanger_quantification,prediction_validation;layer23_evidence_audit.run();molecular_and_plate.run();amplicon_reconstruction.run();sanger_quantification.run();prediction_validation.run()','raw_molecular')
    # Preserve original scientific regression before the authorized metadata overlay.
    molecular_tables=0
    for p in sorted((ROOT/'results/molecular').glob('*.csv')):
        q=dest/p.relative_to(ROOT)
        pd.testing.assert_frame_equal(pd.read_csv(p),pd.read_csv(q),check_exact=False,rtol=1e-12,atol=1e-12)
        molecular_tables+=1
    for name in ['OpenA_amplicon_consensus.fasta','OpenA_amplicon_annotated.gb','OpenA_vs_generic.aligned.fasta']:
        assert (dest/'results/molecular'/name).read_bytes()==(ROOT/'results/molecular'/name).read_bytes()
    shutil.copy2(ROOT/'config/layer23.json',dest/'config/layer23.json')
    run_stage(dest,'import s7_correction,reporter_calibration,correction_analysis;s7_correction.prepare();s7_correction.run();reporter_calibration.run();correction_analysis.run()','corrected_reference')
    run_stage(dest,'import finalize_science;finalize_science.run()','final_science')
    tables=0;maxdiff=0.
    for directory in ['results/layer0','results/layer1','results/layer2','results/layer3']:
        for p in sorted((ROOT/directory).glob('*.csv')):
            a=pd.read_csv(p);b=pd.read_csv(dest/p.relative_to(ROOT))
            pd.testing.assert_frame_equal(a,b,check_exact=False,rtol=1e-12,atol=1e-12)
            for col in a.select_dtypes('number'):
                dd=(a[col]-b[col]).abs().dropna()
                if len(dd):maxdiff=max(maxdiff,float(dd.max()))
            tables+=1
    models=0
    for directory in ['models/res_primary','models/context_profiles','models/molecular']:
        for p in sorted((ROOT/directory).glob('*.json')):
            assert json.loads(p.read_text())==json.loads((dest/p.relative_to(ROOT)).read_text()),str(p)
            models+=1
    masks=0
    for p in (ROOT/'masks').glob('*.npz'):
        a=np.load(p);b=np.load(dest/p.relative_to(ROOT))
        for k in a.files:np.testing.assert_array_equal(a[k],b[k]);masks+=1
    integrated='results/integrated/SONAR_Sample_Reports.json'
    assert json.loads((ROOT/integrated).read_text())==json.loads((dest/integrated).read_text())
    record=dict(status='PASS',release_id=RELEASE,command='python science.py reproduce',execution_scope='raw FCS through paired bootstrap; raw AB1 reconstruction and site metrics; v4 correction/calibration; final contracts and validation',
      preserved_RAS_bytes_equal=True,raw_molecular_tables_compared=molecular_tables,final_tables_compared=tables,maximum_absolute_numeric_difference=maxdiff,
      mask_arrays_equal=masks,frozen_model_objects_equal=models,integrated_sample_reports_equal=True,required_external_data_paths=0,
      tolerance={'rtol':1e-12,'atol':1e-12},interpretation='computational reproducibility; no new biological validation')
    save_json(ROOT/'_work/raw_reproduction_result.json',record)
    print(json.dumps(record,indent=2),flush=True)
