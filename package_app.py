"""Build an internal source release, excluding local environments and user workspaces."""
import hashlib
import json
from pathlib import Path
import zipfile

root=Path(__file__).resolve().parent
project=root.parent
dest=project/'SONAR_Platform_1.4.0rc1.zip'
excluded={'.venv','_work','workspace','dist','__pycache__','.pytest_cache','.DS_Store'}
files=[project/'README.md',project/'启动 SONAR.command']
files += sorted(p for p in root.rglob('*') if p.is_file() and p.name not in {'package_build.json','release_archive_check.json'} and not any(v in excluded for v in p.relative_to(root).parts))
experiment_roots={f.parent for f in files if f.name=='experiment.json'}
files=[f for f in files if not any(base==f.parent or base in f.parents for base in experiment_roots)]
manifest=[]
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
    for p in files:
        rel=p.relative_to(project).as_posix()
        data=p.read_bytes()
        z.write(p,'SONAR_Platform/'+rel)
        manifest.append({'path':rel,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
    z.writestr('SONAR_Platform/APP_RELEASE_MANIFEST.json',json.dumps({'app_version':'1.4.0rc1','distribution':'internal authorized research','files':manifest},indent=2,ensure_ascii=False))
digest=hashlib.sha256(dest.read_bytes()).hexdigest()
dest.with_suffix('.zip.sha256').write_text(digest+'  '+dest.name+'\n')
print(json.dumps({'archive':str(dest),'bytes':dest.stat().st_size,'sha256':digest,'files':len(files)},indent=2))
