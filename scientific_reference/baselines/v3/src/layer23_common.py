"""Shared version and evidence IO for the extension; upstream math stays frozen."""
import json
import numpy as np
import pandas as pd
from inventory import ROOT,sha,dump,write_csv
CFG=json.loads((ROOT/'config/layer23.json').read_text())
VERSION=CFG['release_version']
def table(path,rows):
    if isinstance(rows,pd.DataFrame):rows=rows.replace({np.nan:None}).to_dict('records')
    write_csv(ROOT/path,rows)
def jsonout(path,obj):
    def plain(x):
        if isinstance(x,dict):return {str(k):plain(v) for k,v in x.items()}
        if isinstance(x,(list,tuple,np.ndarray)):return [plain(v) for v in x]
        if isinstance(x,(np.integer,)):return int(x)
        if isinstance(x,(np.floating,float)):return float(x) if np.isfinite(x) else None
        if isinstance(x,np.bool_):return bool(x)
        return x
    dump(ROOT/path,plain(obj))
def assert_upstream():
    assert sha(ROOT/'results/ras_results.csv')==CFG['upstream_ras_sha256'],'RAS changed: calibration must be invalidated/reviewed'
    assert sha(ROOT/'src/core.py')==CFG['upstream_core_sha256'],'Upstream estimator code changed'
    assert json.loads((ROOT/'config/analysis.json').read_text())['analysis_version']==CFG['upstream_analysis_version']
def model_provenance(molecular=False):
    out=dict(layer23_config_sha256=sha(ROOT/'config/layer23.json'),source_manifest_sha256=sha(ROOT/'reference/layer23/source_manifest.json'))
    if molecular:out.update(reference_sha256=sha(ROOT/'results/molecular/OpenA_amplicon_consensus.fasta'),molecular_results_sha256=sha(ROOT/'results/molecular/S10_well_level_molecular_results.csv'))
    return out
def md(d):
    from reports import md as make
    return make(d)
def report(path,text):
    (ROOT/path).write_text(text.strip()+'\n')
