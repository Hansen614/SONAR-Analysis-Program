"""Collect original dependency notices from the exact isolated build environment."""
from pathlib import Path
from importlib.metadata import distributions
import json
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '_work' / 'third-party-notices'
# Installed only for frozen reference-environment metadata; never imported by SAP.
EXCLUDED_BINARIES = {'pillow-heif'}


def collect():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    records = []
    for d in sorted(distributions(), key=lambda d: d.metadata['Name'].lower()):
        name = re.sub(r'[-_.]+', '-', d.metadata['Name']).lower()
        if name in EXCLUDED_BINARIES:
            records.append({'name': name, 'version': d.version, 'scope': 'metadata only; HEIC decoder and its libraries excluded'})
            continue
        dest = OUT / (name + '-' + d.version)
        dest.mkdir()
        copied = []
        for f in d.files or []:
            p = Path(str(f))
            if re.match(r'^(licen[cs]e|copying|copyright|notice|authors)([._-]|$)', p.name, re.I):
                src = Path(d.locate_file(f))
                if src.is_file() and src.stat().st_size < 5_000_000:
                    target = dest / str(f).replace('..', '_').replace('/', '--')
                    shutil.copyfile(src, target)
                    copied.append(target.name)
        supplemental = 'pyobjc-core' if name.startswith('pyobjc-') else name.replace('-', '_')
        for f in (ROOT / 'packaging/licenses').glob(supplemental + '--*'):
            shutil.copyfile(f, dest / f.name)
            copied.append(f.name)
        license_text = d.metadata.get('License') or ''
        if not copied and len(license_text) > 200:
            (dest / 'LICENSE-from-package-metadata.txt').write_text(license_text, encoding='utf-8')
            copied.append('LICENSE-from-package-metadata.txt')
        if not copied:
            raise RuntimeError(f'Missing original license text: {name} {d.version}')
        record = {'name': name, 'version': d.version, 'license': d.metadata.get('License-Expression') or license_text[:160],
                  'upstream': d.metadata.get_all('Project-URL') or [d.metadata.get('Home-page')], 'notices': copied}
        (dest / 'package.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
        records.append(record)
    shutil.copytree(ROOT / 'packaging/licenses', OUT / 'supplemental')
    shutil.copyfile(ROOT / 'THIRD_PARTY_NOTICES.md', OUT / 'README.md')
    (OUT / 'packages.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
    print(f'Collected notices for {len(records)} installed build/runtime distributions')
    return OUT

if __name__ == '__main__':
    collect()
