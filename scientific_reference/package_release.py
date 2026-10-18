#!/usr/bin/env python3
"""Build both self-contained archives from maintained files; never package scratch environments."""
from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parent
OMIT={'_work','__pycache__','.pytest_cache','.venv','.DS_Store'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def files():
    return [p for p in sorted(ROOT.rglob('*')) if p.is_file() and not any(x in OMIT for x in p.relative_to(ROOT).parts) and p.name!='RELEASE_MANIFEST.json']
def build():
    items=files()
    payload=[p for p in items if p.relative_to(ROOT).parts[0] in ['src','config','models','inputs','reference','inventory','results','tests','environment'] or p.name=='science.py']
    payload_hash=hashlib.sha256(json.dumps({str(p.relative_to(ROOT)):sha(p) for p in payload},sort_keys=True).encode()).hexdigest()
    manifest={'release_id':'sonar-science-v1.0-s7s10','release_date':'2026-10-13','scientific_payload_sha256':payload_hash,
      'manifest_self_excluded':True,'runtime_entrypoint':'science.py','implementation_prompt':'CODEX_IMPLEMENTATION_PROMPT.md',
      'raw_data_included':True,'original_absolute_paths_required':False,'external_validation_claimed':False,
      'files':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':p.stat().st_size} for p in items]}
    (ROOT/'RELEASE_MANIFEST.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
    for name,top in [('SONAR_Scientific_Final_S7_S10.zip','SONAR_Scientific_Final_S7_S10'),('SONAR_Codex_Handoff_Ready.zip','SONAR_Codex_Handoff')]:
        path=ROOT.parent/name
        with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for p in items+[ROOT/'RELEASE_MANIFEST.json']:
                info=zipfile.ZipInfo(top+'/'+str(p.relative_to(ROOT)),date_time=(2026,10,13,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
                z.writestr(info,p.read_bytes(),compresslevel=6)
        with zipfile.ZipFile(path) as z:assert z.testzip() is None
        (path.with_suffix('.zip.sha256')).write_text(sha(path)+'  '+path.name+'\n')
        print(json.dumps({'archive':str(path),'bytes':path.stat().st_size,'sha256':sha(path),'entries':len(items)+1,'scientific_payload_sha256':payload_hash}),flush=True)
if __name__=='__main__':build()
