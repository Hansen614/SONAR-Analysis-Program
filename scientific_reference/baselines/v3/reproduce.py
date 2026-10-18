#!/usr/bin/env python3
"""Single-entry, fresh, offline analysis; --verify checks a second isolated run."""
import os,sys,json,shutil,subprocess,argparse,hashlib,platform,importlib.metadata
from pathlib import Path
ROOT=Path(__file__).resolve().parent
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'_work/matplotlib'))
sys.path.insert(0,str(ROOT/'src'))
from inventory import inventory,sha,dump,write_csv

def verify_inputs():
    import csv
    manifest=ROOT/'inventory/input_files.csv'
    if manifest.exists():
        with manifest.open(encoding='utf-8-sig') as f:
            for r in csv.DictReader(f):
                if sha(ROOT/r['packaged_path'])!=r['sha256']:raise RuntimeError('Packaged raw changed: '+r['packaged_path'])
                if Path(r['original_path']).exists() and sha(r['original_path'])!=r['sha256']:raise RuntimeError('Original raw changed: '+r['original_path'])
    manifest=ROOT/'reference/layer23/source_manifest.json'
    if manifest.exists():
        for r in json.loads(manifest.read_text()):
            if sha(ROOT/r['packaged_path'])!=r['sha256']:raise RuntimeError('Layer23 source changed: '+r['packaged_path'])
            if Path(r['original_path']).exists() and sha(r['original_path'])!=r['sha256']:raise RuntimeError('Original Layer23 source changed: '+r['original_path'])

def render_records():
    from PIL import Image,ImageOps
    from pillow_heif import register_heif_opener
    register_heif_opener()
    for s,f in [('S7','IMG_1694.HEIC'),('S10','IMG_1693.HEIC')]:
        im=ImageOps.exif_transpose(Image.open(ROOT/'inputs'/s/f)).convert('RGB');im.thumbnail((1800,1800));im.save(ROOT/'inventory'/f'{s}_record.png')

def environment():
    packages=['numpy','scipy','pandas','matplotlib','scikit-learn','flowio','biopython','openpyxl','pillow','pillow-heif','pytest']
    versions={p:importlib.metadata.version(p) for p in packages}
    dump(ROOT/'config/environment.json',dict(python=platform.python_version(),platform=platform.platform(),packages=versions))
    (ROOT/'requirements.txt').write_text('\n'.join(f'{p}=={v}' for p,v in versions.items())+'\n')

def source_hashes():
    items=[]
    for p in sorted(ROOT.rglob('*')):
        rel=p.relative_to(ROOT)
        if not p.is_file() or any(x in rel.parts for x in ['_work','__pycache__','.pytest_cache']):continue
        if p.name=='release_files_sha256.csv':continue
        items.append(dict(path=str(rel),sha256=sha(p),bytes=p.stat().st_size))
    write_csv(ROOT/'reports/release_files_sha256.csv',items)

def execute(layer23_only=False):
    for d in ['results','contexts','masks','reports','inventory','figures/source_tables','_work','results/molecular','results/calibration','results/prediction','models/layer23','figures/layer23','reports/layer23']:(ROOT/d).mkdir(parents=True,exist_ok=True)
    verify_inputs()
    if not layer23_only:
        inventory();render_records();environment()
        from analyze import run as analyze
        from molecular_and_plate import run as audit
        from plots import run as plots
        from reports import run as reports
        analyze();audit();plots();reports()
    from layer23_common import assert_upstream
    assert_upstream()
    import importlib
    for name in ['layer23_evidence_audit','amplicon_reconstruction','sanger_quantification','reporter_calibration','prediction_validation','layer23_plots','layer23_reports']:
        print('Running '+name,flush=True)
        importlib.import_module(name).run()
    verify_inputs()
    test=subprocess.run([sys.executable,'-m','pytest',str(ROOT/'tests'),'-q'],cwd=ROOT,text=True,capture_output=True)
    (ROOT/'reports/test_results.txt').write_text(test.stdout+test.stderr)
    if test.returncode:raise RuntimeError('Scientific tests failed; see reports/test_results.txt')
    print(test.stdout.strip(),flush=True)

def verify_reexecution():
    import pandas as pd,numpy as np
    from PIL import Image
    dest=ROOT/'_work/reexecution'
    if dest.exists():shutil.rmtree(dest)
    dest.mkdir();(dest/'inputs').symlink_to(ROOT/'inputs',target_is_directory=True)
    for name in ['src','config','tests','reference']:
        shutil.copytree(ROOT/name,dest/name,ignore=shutil.ignore_patterns('__pycache__'))
    (dest/'baselines').symlink_to(ROOT/'baselines',target_is_directory=True)
    (dest/'inventory').mkdir();shutil.copy2(ROOT/'inventory/input_files.csv',dest/'inventory/input_files.csv')
    shutil.copy2(ROOT/'inventory/record_transcription.md',dest/'inventory/record_transcription.md')
    shutil.copy2(ROOT/'reproduce.py',dest/'reproduce.py')
    with (ROOT/'_work/reexecution.log').open('w') as log:
        p=subprocess.run([sys.executable,str(dest/'reproduce.py'),'--single'],cwd=dest,stdout=log,stderr=subprocess.STDOUT)
    if p.returncode:raise RuntimeError('Independent run failed; see _work/reexecution.log')
    tables=0;mask_arrays=0;images=0;model_objects=0;maxdiff=0.0
    for src in sorted((ROOT/'results').rglob('*.csv')):
        target=dest/src.relative_to(ROOT)
        try:a=pd.read_csv(src);b=pd.read_csv(target)
        except pd.errors.EmptyDataError:
            assert src.read_bytes()==target.read_bytes();tables+=1;continue
        pd.testing.assert_frame_equal(a,b,check_exact=False,rtol=1e-12,atol=1e-12)
        for c in a.select_dtypes('number').columns:
            dif=(a[c]-b[c]).abs().dropna()
            if len(dif):maxdiff=max(maxdiff,float(dif.max()))
        tables+=1
    for src in sorted((ROOT/'masks').glob('*.npz')):
        a=np.load(src);b=np.load(dest/'masks'/src.name)
        assert a.files==b.files
        for key in a.files:assert np.array_equal(a[key],b[key]);mask_arrays+=1
    assert json.loads((ROOT/'contexts/context.json').read_text())==json.loads((dest/'contexts/context.json').read_text())
    for src in sorted((ROOT/'figures').rglob('*.png')):
        assert np.array_equal(np.array(Image.open(src)),np.array(Image.open(dest/src.relative_to(ROOT))));images+=1
    for src in sorted((ROOT/'models/layer23').glob('*.json')):
        assert json.loads(src.read_text())==json.loads((dest/src.relative_to(ROOT)).read_text());model_objects+=1
    for name in ['OpenA_amplicon_consensus.fasta','OpenA_amplicon_annotated.gb','OpenA_vs_generic.aligned.fasta']:
        assert (ROOT/'results/molecular'/name).read_bytes()==(dest/'results/molecular'/name).read_bytes()
    result=dict(status='PASS',execution_date='2026-10-13',command='python reproduce.py --verify',analysis_version=json.loads((ROOT/'config/layer23.json').read_text())['release_version'],upstream_analysis_version=json.loads((ROOT/'config/analysis.json').read_text())['analysis_version'],numeric_tables_compared=tables,maximum_absolute_numeric_difference=maxdiff,event_mask_arrays_compared=mask_arrays,diagnostic_PNGs_pixel_equal=images,model_objects_equal=model_objects,reconstructed_reference_files_equal=3,context_equal=True,tolerance=dict(rtol=1e-12,atol=1e-12),tests_log='reports/test_results.txt',raw_integrity='All copied source hashes match; originals also checked when present',reproduction_level='computational_only_not_independent_biological_or_cross_lab')
    dump(ROOT/'reports/reproducibility_record.json',result)
    print(json.dumps(result,indent=2),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--verify',action='store_true');parser.add_argument('--single',action='store_true');parser.add_argument('--layer23-only',action='store_true');args=parser.parse_args()
    if args.verify and args.layer23_only:parser.error('--verify requires a complete run; omit --layer23-only')
    execute(args.layer23_only)
    if args.verify:verify_reexecution()
    source_hashes()
